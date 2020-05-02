# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2015 Roberto Longobardi
# 
# This file is part of the Test Manager plugin for Trac.
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at: 
#   https://trac-hacks.org/wiki/TestManagerForTracPluginLicense
#
# Author: Roberto Longobardi <otrebor.dev@gmail.com>
# 

import copy
from datetime import date, datetime
import re

from trac.core import Component, implements
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionError
from trac.resource import Resource, ResourceNotFound
from trac.util.datefmt import utc, utcmax
from trac.util.text import CRLF
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

from testmanager.util import get_page_title, get_page_description
from tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, AbstractWikiPageWrapper, need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm
from tracgenericclass.util import to_any_timestamp, get_timestamp_db_type, \
    db_insert_or_ignore, formatExceptionInfo


try:
    from testmanager.api import _, tag_, N_
except ImportError:
    from trac.util.translation import _, N_
    tag_ = _

class AbstractTestDescription(AbstractWikiPageWrapper):
    """
    A test description object based on a Wiki page.
    Concrete subclasses are TestCatalog and TestCase.
    
    Uses a textual 'id' as key.
    
    Comprises a title and a description, currently embedded in the wiki
    page respectively as the first line and the rest of the text.
    The title is automatically wiki-formatted as a second-level title
    (i.e. sorrounded by '==').
    """
    
    # Fields that must not be modified directly by the user
    protected_fields = ('id', 'page_name')

    def __init__(self, env, realm='testdescription', id=None, page_name=None, title=None, description=None, db=None):
    
        self.env = env
        
        self.values = {}

        self.values['id'] = id
        self.values['page_name'] = page_name

        self.title = title
        self.description = description

        self.env.log.debug('Title: %s' % self.title)
        self.env.log.debug('Description: %s' % self.description)
    
        key = self.build_key_object()
    
        AbstractWikiPageWrapper.__init__(self, env, realm, key, db)

    def post_fetch_object(self, db):
        # Fetch the wiki page
        AbstractWikiPageWrapper.post_fetch_object(self, db)

        # Then parse it and derive title, description and author
        self.title = get_page_title(self.wikipage.text)
        self.description = get_page_description(self.wikipage.text)
        self.author = self.wikipage.author

        self.env.log.debug('Title: %s' % self.title)
        #self.env.log.debug('Description: %s' % self.description)

    def pre_insert(self, db):
        """ Assuming the following fields have been given a value before this call:
            title, description, author, remote_addr 
        """
    
        self.text = '== '+self.title+' ==' + CRLF + CRLF + self.description
        AbstractWikiPageWrapper.pre_insert(self, db)

        return True

    def pre_save_changes(self, db):
        """ Assuming the following fields have been given a value before this call:
            title, description, author, remote_addr 
        """
    
        self.text = '== '+self.title+' ==' + CRLF + CRLF + self.description
        AbstractWikiPageWrapper.pre_save_changes(self, db)
        
        return True

    def get_search_results(self, req, terms, filters):
        """
        Currently delegates the search to the Wiki module. 
        """
        for result in WikiModule(self.env).get_search_results(req, terms, ('wiki',)):
            if result[0].rpartition('/')[2].startswith("TC"):
                yield result


class TestCatalog(AbstractTestDescription):
    """
    A container for test cases and sub-catalogs.
    
    Test catalogs are organized in a tree. Since wiki pages are instead
    on a flat plane, we use a naming convention to flatten the tree into
    page names. These are examples of wiki page names for a tree:
        TC          --> root of the tree. This page is automatically 
                        created at plugin installation time.
        TC_TT0      --> test catalog at the first level. Note that 0 is
                        the catalog ID, generated at creation time.
        TC_TT0_TT34 --> sample sub-catalog, with ID '34', of the catalog 
                        with ID '0'
        TC_TT27     --> sample other test catalog at first level, with
                        ID '27'
                        
        There is not limit to the depth of a test tree.
                        
        Test cases are contained in test catalogs, and are always
        leaves of the tree:

        TC_TT0_TT34_TC65 --> sample test case, with ID '65', contained 
                             in sub-catalog '34'.
                             Note that test case IDs are independent on 
                             test catalog IDs.
    """
    def __init__(self, env, id=None, page_name=None, title=None, description=None, db=None):
    
        AbstractTestDescription.__init__(self, env, 'testcatalog', id, page_name, title, description, db)

    def get_enclosing_catalog(self):
        """
        Returns the catalog containing this test catalog, or None if its a root catalog.
        """
        page_name = self.values['page_name']
        cat_page = page_name.rpartition('_TT')[0]

        if cat_page == 'TC':
            return None
        else:
            cat_id = page_name.rpartition('TT')[0].page_name.rpartition('TT')[2].rpartition('_')[0]

            return TestCatalog(self.env, cat_id, cat_page)
        
    def list_subcatalogs(self, db=None):
        """
        Returns a list of the sub catalogs of this catalog.
        """
        tc_search = TestCatalog(self.env)
        tc_search['page_name'] = self.values['page_name'] + '_TT%'
        
        cat_re = re.compile('^TT[0-9]*$')
        
        for tc in tc_search.list_matching_objects(exact_match=False, db=db):
            # Only return direct sub-catalogs and exclude test cases
            if cat_re.match(tc['page_name'].partition(self.values['page_name']+'_')[2]) :
                yield tc
        
    def list_testcases(self, plan_id=None, deep=False, db=None):
        """
        Returns a list of the test cases in this catalog.
        If plan_id is provided, returns a list of TestCaseInPlan objects,
        otherwise, of TestCase objects.
        
        :deep: if True indicates to return all TCs in the catalog and 
               recursively in all the contained sub-catalogs.
        """
        self.env.log.debug('>>> list_testcases')
        
        if plan_id is not None:
            from testmanager.api import TestManagerSystem
            default_status = TestManagerSystem(self.env).get_default_tc_status()
        
        tc_search = TestCase(self.env)
        tc_search['page_name'] = self.values['page_name'] + ('_TC%', '%_TC%')[deep]
        
        for tc in tc_search.list_matching_objects(exact_match=False, db=db):
            self.env.log.debug('    ---> Found testcase %s' % tc['id'])
            if plan_id is None:
                yield tc
            else:
                tcip = TestCaseInPlan(self.env, tc['id'], plan_id)
                if not tcip.exists or 'status' not in tcip.fields:
                    tcip['status'] = default_status
                    
                tcip['exec_order'] = tc['exec_order']

                yield tcip

        self.env.log.debug('<<< list_testcases')
                
    def list_testplans(self, db=None):
        """
        Returns a list of test plans for this catalog.
        """

        self.env.log.debug('>>> list_testplans')
        
        tp_search = TestPlan(self.env)
        tp_search['catid'] = self.values['id']
        tp_search['contains_all'] = None
        tp_search['freeze_tc_versions'] = None
        
        for tp in tp_search.list_matching_objects(db=db):
            yield tp

        self.env.log.debug('<<< list_testplans')

    def get_last_order(self, db=None):
        tcat_page_filter = "%s_TC%%" % self.values['page_name']
        
        if not db:
            db = self.env.get_read_db()
        
        cursor = db.cursor()
        cursor.execute("SELECT max(exec_order) FROM testcase WHERE page_name LIKE %s",
            (tcat_page_filter,))

        row = cursor.fetchone()
        last_order = row[0]
        
        if last_order is None:
            last_order = -1
        
        return last_order
        
    def remove_testcase_from_order(self, tc, db=None):
        """ 
        Removes the test case from the ordered list of test cases, rearranging the
        other test cases to fill the empty position.
        """

        @self.env.with_transaction(db)
        def do_remove_testcase_from_order(db):
            old_order = tc['exec_order']
            tcat_page_filter = "%s_TC%%" % self.values['page_name']

            cursor = db.cursor()
            
            # Spostare indietro di 1 posizione tutti gli elementi
            # da old_order + 1 in poi
            cursor.execute("UPDATE testcase SET exec_order = exec_order - 1 WHERE page_name LIKE %s AND exec_order >= %s", 
                (tcat_page_filter, old_order + 1))
                
    def insert_testcase_into_order(self, tc, new_order, db=None):
        """ 
        Inserts the test case into the ordered list of test cases, at the specified
        position, rearranging the other test cases accordingly.
        """

        @self.env.with_transaction(db)
        def do_insert_testcase_into_order(db):
            tcat_page_filter = "%s_TC%%" % self.values['page_name']
            
            cursor = db.cursor()
            
            # Spostare avanti di 1 posizione tutti gli elementi
            # da new_order in poi
            cursor.execute("UPDATE testcase SET exec_order = exec_order + 1 WHERE page_name LIKE %s AND exec_order >= %s", 
                (tcat_page_filter, new_order))
                
    def change_testcase_order(self, tc, new_order, db=None):
        """ 
        Moves the test case to a different position inside the same catalog.
        """

        @self.env.with_transaction(db)
        def do_change_testcase_order(db):
            old_order = tc['exec_order']
            tcat_page_filter = "%s_TC%%" % self.values['page_name']

            cursor = db.cursor()
            
            if new_order < old_order:
                # Spostare in avanti di 1 posizione tutti gli elementi compresi
                # tra new_order incluso e old_order -1 inluso
                #update testcase set exec_order = old_order + 1 where 
                cursor.execute("UPDATE testcase SET exec_order = exec_order + 1 WHERE page_name LIKE %s AND exec_order >= %s AND exec_order <= %s", 
                    (tcat_page_filter, new_order, old_order - 1))

            else:
                # Spostare indietro di 1 posizione tutti gli elementi compresi
                # tra old_order + 1 incluso e new_order incluso
                cursor.execute("UPDATE testcase SET exec_order = exec_order - 1 WHERE page_name LIKE %s AND exec_order >= %s AND exec_order <= %s", 
                    (tcat_page_filter, old_order + 1, new_order))

    def pre_delete(self, db):
        """ 
        Delete all contained test catalogs and test cases, recursively.
        """
        AbstractTestDescription.pre_delete(self, db)
        
        self.env.log.debug("Deleting all test cases related to this catalog id '%s'" % self['id'])
        for tc in self.list_testcases(db=db):
            tc.delete(db=db)
            
        self.env.log.debug("Deleting all sub catalogs in this catalog id '%s'" % self['id'])
        for tcat in self.list_subcatalogs(db=db):
            tcat.delete(db=db)
        
        return True

    def post_delete(self, db):
        """
        Deletes the test plans associated to this catalog and the status 
        of the test cases in those plans and their status change 
        history.
        """
        self.env.log.debug("Deleting all test plans related to this catalog id '%s'" % self['id'])

        for tp in self.list_testplans(db):
            tp.delete(db=db)

        AbstractTestDescription.post_delete(self, db)

    def create_instance(self, key):
        return TestCatalog(self.env, key['id'])

    @classmethod
    def list_root_catalogs(cls, env):
        """
        Returns a list of the root-level catalogs.
        """
        tc_search = cls(env)
        tc_search['page_name'] ='TC_TT%'
        
        for tc in tc_search.list_matching_objects(exact_match=False):
            # Only return root catalogs
            if tc['page_name'].count('_') == 1:
                yield tc
   
    def get_search_results(self, req, terms, filters):
        if not 'testcatalog' in filters:
            return

        for result in AbstractTestDescription.get_search_results(self, req, terms, filters):
            if 'TC' not in result[0].rpartition("_TT")[2]:
                yield result
           
   
class TestCase(AbstractTestDescription):

    # Fields that must not be modified directly by the user
    protected_fields = ('id', 'page_name', 'exec_order')

    def __init__(self, env, id=None, page_name=None, title=None, description=None, exec_order=0, db=None):
    
        self.exec_order = exec_order
        AbstractTestDescription.__init__(self, env, 'testcase', id, page_name, title, description, db)
        
    def get_enclosing_catalog(self):
        """
        Returns the catalog containing this test case.
        """
        page_name = self.values['page_name']
        cat_id = page_name.rpartition('TT')[2].rpartition('_')[0]
        cat_page = page_name.rpartition('_TC')[0]
        
        return TestCatalog(self.env, cat_id, cat_page)
        
    def create_instance(self, key):
        return TestCase(self.env, key['id'])

    def set_order(self, new_order, db=None):
        """
        Changes the order of the test case in the current catalog.
        """

        if new_order != self['exec_order']:
            @self.env.with_transaction(db)
            def do_move_to(db):
                self['exec_order'] = new_order
                
                self.save_changes('System', "Changed execution order", 
                    datetime.now(utc), db)

    def move_to(self, tcat, new_order=-1, delete_tcip=True, db=None):
        """ 
        Moves the test case into a different catalog.
        
        delete_tcip: True to delete the status of the test case in any plan
                          and the corresponding history,
                     False to keep them.
        
        Note: the test case keeps its ID, and the wiki page is moved 
        into the new name. This way, the page change history is kept.
        """

        @self.env.with_transaction(db)
        def do_move_to(db):
            # Remove the test case from the ordered list of the old catalog
            old_cat = self.get_enclosing_catalog()
            old_cat.remove_testcase_from_order(self)

            t_new_order = new_order
            if t_new_order == -1:
                t_new_order = tcat.get_last_order(db) + 1
            
            # Add it to the ordered list of the new catalog
            tcat.insert_testcase_into_order(self, t_new_order)
        
            # Rename the wiki page
            new_page_name = tcat['page_name'] + '_TC' + self['id']

            cursor = db.cursor()
            cursor.execute("UPDATE wiki SET name = %s WHERE name = %s", 
                (new_page_name, self['page_name']))

            # Invalidate Trac 0.12 page name cache
            try:
                del WikiSystem(self.env).pages
            except:
                pass

            # TODO Move wiki page attachments
            #from trac.attachment import Attachment
            #Attachment.delete_all(self.env, 'wiki', self.name, db)
            
            if delete_tcip:
                # Remove test case from all the plans
                tcip_search = TestCaseInPlan(self.env)
                tcip_search['id'] = self.values['id']
                for tcip in tcip_search.list_matching_objects(db=db):
                    tcip.delete(db)

            # Update self properties and save
            self['page_name'] = new_page_name
            self['exec_order'] = t_new_order
            self.wikipage = WikiPage(self.env, new_page_name)
            
            self.save_changes('System', "Moved to a different catalog", 
                datetime.now(utc), db)

    def get_related_tickets(self, db=None):
        """
        Returns an iterator over the IDs of the ticket opened against 
        this test case.
        """
        self.env.log.debug('>>> get_related_tickets')
    
        if not db:
            db = self.env.get_read_db()
        
        cursor = db.cursor()
        cursor.execute("SELECT id FROM ticket WHERE id in " +
            "(SELECT ticket FROM ticket_custom WHERE name='testcaseid' AND value=%s)",
            (self.values['page_name'],))
            
        for row in cursor:
            self.env.log.debug('    ---> Found ticket %s' % row[0])
            yield row[0]

        self.env.log.debug('<<< get_related_tickets')

    def pre_insert(self, db):
        """
        Sets the execution order to the last of the catalog, 
        if not explicitly specified.
        """
        AbstractTestDescription.pre_insert(self, db)

        if self['exec_order'] is None or self['exec_order'] == -1:
            tcat = self.get_enclosing_catalog()
            last_order = tcat.get_last_order(db)

            self.env.log.debug("last_order: %s" % last_order)
            
            self['exec_order'] = last_order + 1

        # Inserts the test case into the enclosing catalog, 
        # in the right position.
        tcat = self.get_enclosing_catalog()
        tcat.insert_testcase_into_order(self, self['exec_order'], db)
            
        return True

    def post_delete(self, db):
        """
        Deletes the test case from all plans and its status change 
        history.
        """
        self.env.log.debug("Deleting the case case from all plans and its status change history")

        cursor = db.cursor()
        
        # Delete test cases in plan
        cursor.execute('DELETE FROM testcaseinplan WHERE id = %s', (self['id'],))

		# TODO Delete from testcaseinplan_custom and testcaseinplan_change

        # Delete test case status history
        cursor.execute('DELETE FROM testcasehistory WHERE id = %s', (self['id'],))

        if self['exec_order'] is not None and self['exec_order'] != -1:
            tcat = self.get_enclosing_catalog()
            tcat.remove_testcase_from_order(self)

        AbstractTestDescription.post_delete(self, db)
        
    def get_search_results(self, req, terms, filters):
        if not 'testcase' in filters:
            return
            
        for result in AbstractTestDescription.get_search_results(self, req, terms, filters):
            if 'TC' in result[0].rpartition("_TT")[2]:
                yield result

        
class TestCaseInPlan(AbstractVariableFieldsObject):
    """
    This object represents a test case in a test plan.
    It keeps the latest test execution status (aka verdict).
    
    The status, as far as this class is concerned, can be just any 
    string.
    The plugin logic, anyway, currently recognizes only three hardcoded
    statuses, but this can be evolved without need to modify also this
    class. 
    
    The history of test execution status changes is instead currently
    kept in another table, testcasehistory, which is not backed by any
    python class. 
    This is a duplication, since the 'changes' table also keeps track
    of status changes, so the testcasehistory table may be removed in 
    the future.
    """
    
    # Fields that must not be modified directly by the user
    protected_fields = ('id', 'planid', 'page_name', 'page_version', 'status')

    def __init__(self, env, id=None, planid=None, page_name=None, page_version=-1, status=None, db=None):
        """
        The test case in plan is related to a test case, the 'id' and 
        'page_name' arguments, and to a test plan, the 'planid' 
        argument.
        """
        self.values = {}

        self.values['id'] = id
        self.values['planid'] = planid
        self.values['page_name'] = page_name
        self.values['page_version'] = page_version
        self.values['status'] = status

        key = self.build_key_object()
    
        AbstractVariableFieldsObject.__init__(self, env, 'testcaseinplan', key, db)

    def get_key_prop_names(self):
        return ['id', 'planid']
        
    def create_instance(self, key):
        return TestCaseInPlan(self.env, key['id'], key['planid'])
        
    def set_status(self, status, author, db=None):
        """
        Sets the execution status of the test case in the test plan.
        This method immediately writes into the test case history, but
        does not write the new status into the database table for this
        test case in plan.
        You need to call 'save_changes' to achieve that.
        """
        status = status.lower()
        self['status'] = status

        @self.env.with_transaction(db)
        def do_set_status(db):
            cursor = db.cursor()
            sql = 'INSERT INTO testcasehistory (id, planid, time, author, status) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(sql, (self.values['id'], self.values['planid'], to_any_timestamp(datetime.now(utc)), author, status))

    def list_history(self, db=None):
        """
        Returns an ordered list of status changes, along with timestamp
        and author, starting from the most recent.
        """
        if not db:
            db = self.env.get_read_db()
        
        cursor = db.cursor()

        sql = "SELECT time, author, status FROM testcasehistory WHERE id=%s AND planid=%s ORDER BY time DESC"
        
        cursor.execute(sql, (self.values['id'], self.values['planid']))
        for ts, author, status in cursor:
            yield ts, author, status.lower()

    def get_related_tickets(self, db=None):
        """
        Returns an iterator over the IDs of the ticket opened against 
        this test case and this test plan.
        """
        self.env.log.debug('>>> get_related_tickets')
    
        if not db:
            db = self.env.get_read_db()

        cursor = db.cursor()
        cursor.execute("SELECT id FROM ticket WHERE id in " +
            "(SELECT ticket FROM ticket_custom WHERE name='testcaseid' AND value=%s) " +
            "AND id in " +
            "(SELECT ticket FROM ticket_custom WHERE name='planid' AND value=%s) ",
            (self.values['page_name'], self.values['planid']))
            
        for row in cursor:
            self.env.log.debug('    ---> Found ticket %s' % row[0])
            yield row[0]

        self.env.log.debug('<<< get_related_tickets')

    def update_version(self):
        """
        Updates the wiki page version reference to be the latest available version.
        """
        self.env.log.debug('>>> update_version')

        wikipage = WikiPage(self.env, self.values['page_name'])
        self['page_version'] = wikipage.version
        
        self.env.log.debug('<<< update_version')
        
    def delete_history(self, db=None):
        """
        Deletes all entries in the testcasehistory related to this test case in plan
        """
        self.env.log.debug('>>> delete_history')

        @self.env.with_transaction(db)
        def do_delete_history(db):
            cursor = db.cursor()
            
            # Delete test case status history
            cursor.execute('DELETE FROM testcasehistory WHERE id = %s and planid = %s', (self['id'], self['planid']))

        self.env.log.debug('<<< delete_history')

    
class TestPlan(AbstractVariableFieldsObject):
    """
    A test plan represents a particular instance of test execution
    for a test catalog.
    You can create any number of test plans on any test catalog (or 
    sub-catalog).
    A test plan is associated to a test catalog, and to every 
    test case in it, with the initial state equivalent to 
    "to be executed".
    The association with test cases is achieved through the 
    TestCaseInPlan objects.
    
    For optimization purposes, a TestCaseInPlan is created in the
    database only as soon as its status is changed (i.e. from "to be
    executed" to something else).
    So you cannot always count on the fact that a TestCaseInPlan 
    actually exists for every test case in a catalog, when a particular
    test plan has been created for it.
    """
    
    # Fields that must not be modified directly by the user
    protected_fields = ('id', 'catid', 'page_name', 'name', 'author', 'time', 'contains_all', 'freeze_tc_versions')
    
    selected_tcs = []

    def __init__(self, env, id=None, catid=None, page_name=None, name=None, author=None, contains_all=1, snapshot=0, selected_tcs=[], db=None):
        """
        A test plan has an ID, generated at creation time and 
        independent on those for test catalogs and test cases.
        It is associated to a test catalog, the 'catid' and 'page_name'
        arguments.
        It has a name and an author.
        """
        self.values = {}

        self.values['id'] = id
        self.values['catid'] = catid
        self.values['page_name'] = page_name
        self.values['name'] = name
        self.values['author'] = author
        self.values['contains_all'] = contains_all
        self.values['freeze_tc_versions'] = snapshot

        self.selected_tcs = selected_tcs

        key = self.build_key_object()
    
        AbstractVariableFieldsObject.__init__(self, env, 'testplan', key, db)

    def create_instance(self, key):
        return TestPlan(self.env, key['id'])

    def post_insert(self, db):
        """
        If only some test cases must be in the plan, then create the
        corresponding TestCaseInPlan objects and relate them to this plan.
        """
        
        self.env.log.debug(">>> post_insert")

        if not self.values['contains_all']:
            # Create a TestCaseInPlan for each test case specified by the User
            from testmanager.api import TestManagerSystem
            default_status = TestManagerSystem(self.env).get_default_tc_status()

            author = self.values['author']

            for tc_page_name in self.selected_tcs:
                if tc_page_name != '':
                    tc_id = tc_page_name.rpartition('TC')[2]
                    tcip = TestCaseInPlan(self.env, tc_id, self.values['id'])
                    if not tcip.exists:
                        tc = TestCase(self.env, tc_id)
                        tcip['page_name'] = tc['page_name']
                        if self.values['freeze_tc_versions']:
                            # Set the wiki page version to the current latest version
                            tcip['page_version'] = tc.wikipage.version
                        tcip.set_status(default_status, author)
                        tcip.insert()
                    
        elif self.values['freeze_tc_versions']:
            # Create a TestCaseInPlan for each test case in the catalog, and
            # set the wiki page version to the current latest version
            tcat = TestCatalog(self.env, self.values['catid'], self.values['page_name'])

            from testmanager.api import TestManagerSystem
            default_status = TestManagerSystem(self.env).get_default_tc_status()

            author = self.values['author']

            for tc in tcat.list_testcases(deep=True):
                tcip = TestCaseInPlan(self.env, tc.values['id'], self.values['id'])
                if not tcip.exists:
                    tcip['page_name'] = tc['page_name']
                    tcip['page_version'] = tc.wikipage.version
                    tcip.set_status(default_status, author)
                    
                    tcip.insert()

        self.env.log.debug("<<< post_insert")
                    
    def post_delete(self, db):
        self.env.log.debug("Deleting this test plan %s" % self['id'])
        
        # Remove all test cases (in plan) from this plan
        #self.env.log.debug("Deleting all test cases in the plan...")
        #tcip_search = TestCaseInPlan(self.env)
        #tcip_search['planid'] = self.values['id']
        #for tcip in tcip_search.list_matching_objects(db=db):
        #    self.env.log.debug("Deleting test case in plan, with id %s" % tcip['id'])
        #    tcip.delete(db)

        cursor = db.cursor()
        
        # Delete test cases in plan
        cursor.execute('DELETE FROM testcaseinplan WHERE planid = %s', (self['id'],))

		# TODO Delete from testcaseinplan_custom and testcaseinplan_change

        # Delete test case status history
        cursor.execute('DELETE FROM testcasehistory WHERE planid = %s', (self['id'],))

    def get_related_tickets(self, db=None):
        pass

    def get_selected_testcases(self, db=None):
        """
        If this test plan does not contain all the test cases,
        returns a list of the contained test cases.
        Otherwise, returns None.
        """
        self.env.log.debug('>>> get_selected_testcases')
        
        if not db:
            db = self.env.get_read_db()

        cursor = db.cursor()

        cursor.execute('SELECT id FROM testcaseinplan WHERE planid = %s', (self.values['id'],))

        for row in cursor:
            tcip_id = row[0]
            yield TestCaseInPlan(self.env, tcip_id, self.values['id'])
            
        self.env.log.debug('<<< get_selected_testcases')      

        
class TestManagerModelProvider(Component):
    """
    This class provides the data model for the test management plugin.
    
    The actual data model on the db is created starting from the
    SCHEMA declaration below.
    For each table, we specify whether to create also a '_custom' and
    a '_change' table.
    
    This class also provides the specification of the available fields
    for each class, being them standard fields and the custom fields
    specified in the trac.ini file.
    The custom field specification follows the same syntax as for
    Tickets.
    Currently, only 'text' type of custom fields are supported.
    """

    implements(IConcreteClassProvider, IEnvironmentSetupParticipant)

    SCHEMA = {
                'testmanager_templates':  
                    {'table':
                        Table('testmanager_templates', key = ('id', 'name', 'type'))[
                              Column('id'),
                              Column('name'),
                              Column('type'),
                              Column('description'),
                              Column('content')],
                     'has_custom': False,
                     'has_change': False,
                     'version': 1},
                'testconfig':
                    {'table':
                        Table('testconfig', key = ('propname'))[
                          Column('propname'),
                          Column('value')],
                     'has_custom': False,
                     'has_change': False,
                     'version': 1},
                'testcatalog':  
                    {'table':
                        Table('testcatalog', key = ('id'))[
                              Column('id'),
                              Column('page_name')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 1},
                'testcase':  
                    {'table':
                        Table('testcase', key = ('id'))[
                              Column('id'),
                              Column('page_name'),
                              Column('exec_order', type='int')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 2},
                'testcaseinplan':  
                    {'table':
                        Table('testcaseinplan', key = ('id', 'planid'))[
                              Column('id'),
                              Column('planid'),
                              Column('page_name'),
                              Column('page_version', type='int'),
                              Column('status')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 2},
                'testcasehistory':  
                    {'table':
                        Table('testcasehistory', key = ('id', 'planid', 'time'))[
                              Column('id'),
                              Column('planid'),
                              Column('time', type=get_timestamp_db_type()),
                              Column('author'),
                              Column('status'),
                              Index(['id', 'planid', 'time'])],
                     'has_custom': False,
                     'has_change': False,
                     'version': 1},
                'testplan':
                    {'table':
                        Table('testplan', key = ('id'))[
                              Column('id'),
                              Column('catid'),
                              Column('page_name'),
                              Column('name'),
                              Column('author'),
                              Column('time', type=get_timestamp_db_type()),
                              Column('contains_all', type='int'),
                              Column('freeze_tc_versions', type='int'),
                              Index(['id']),
                              Index(['catid'])],
                     'has_custom': True,
                     'has_change': True,
                     'version': 2}
            }

    FIELDS = {
                'testcatalog': [
                    {'name': 'id', 'type': 'text', 'label': N_('ID')},
                    {'name': 'page_name', 'type': 'text', 'label': N_('Wiki page name')}
                ],
                'testcase': [
                    {'name': 'id', 'type': 'text', 'label': N_('ID')},
                    {'name': 'page_name', 'type': 'text', 'label': N_('Wiki page name')},
                    {'name': 'exec_order', 'type': 'int', 'label': N_('Order')}
                ],
                'testcaseinplan': [
                    {'name': 'id', 'type': 'text', 'label': N_('ID')},
                    {'name': 'planid', 'type': 'text', 'label': N_('Plan ID')},
                    {'name': 'page_name', 'type': 'text', 'label': N_('Wiki page name')},
                    {'name': 'page_version', 'type': 'int', 'label': N_('Wiki page version')},                    
                    {'name': 'status', 'type': 'text', 'label': N_('Status')}
                ],
                'testplan': [
                    {'name': 'id', 'type': 'text', 'label': N_('ID')},
                    {'name': 'catid', 'type': 'text', 'label': N_('Catalog ID')},
                    {'name': 'page_name', 'type': 'text', 'label': N_('Wiki page name')},
                    {'name': 'name', 'type': 'text', 'label': N_('Name')},
                    {'name': 'author', 'type': 'text', 'label': N_('Author')},
                    {'name': 'time', 'type': 'time', 'label': N_('Created')},
                    {'name': 'contains_all', 'type': 'int', 'label': N_('Contains all Test Cases')},
                    {'name': 'freeze_tc_versions', 'type': 'int', 'label': N_('Freeze Test Case versions')}
                ]
            }
            
    METADATA = {'testcatalog': {
                        'label': "Test Catalog", 
                        'searchable': True,
                        'has_custom': True,
                        'has_change': True
                    },
                'testcase': {
                        'label': "Test Case", 
                        'searchable': True,
                        'has_custom': True,
                        'has_change': True
                    },
                'testcaseinplan': {
                        'label': "Test Case in a Plan", 
                        'searchable': False,
                        'has_custom': True,
                        'has_change': True
                    },
                'testplan': {
                        'label': "Test Plan", 
                        'searchable': False,
                        'has_custom': True,
                        'has_change': True
                    }
                }

            
    # IConcreteClassProvider methods
    def get_realms(self):
            yield 'testcatalog'
            yield 'testcase'
            yield 'testcaseinplan'
            yield 'testplan'

    def get_data_models(self):
        return self.SCHEMA

    def get_fields(self):
        return copy.deepcopy(self.FIELDS)
        
    def get_metadata(self):
        return self.METADATA
        
    def create_instance(self, realm, key=None):
        self.env.log.debug(">>> create_instance - %s %s" % (realm, key))

        obj = None
        
        if realm == 'testcatalog':
            if key is not None:
                obj = TestCatalog(self.env, key['id'])
            else:
                obj = TestCatalog(self.env)
        elif realm == 'testcase':
            if key is not None:
                obj = TestCase(self.env, key['id'])
            else:
                obj = TestCase(self.env)
        elif realm == 'testcaseinplan':
            if key is not None:
                obj = TestCaseInPlan(self.env, key['id'], key['planid'])
            else:
                obj = TestCaseInPlan(self.env)
        elif realm == 'testplan':
            if key is not None:
                obj = TestPlan(self.env, key['id'])
            else:
                obj = TestPlan(self.env)
        
        self.env.log.debug("<<< create_instance")

        return obj

    def check_permission(self, req, realm, key_str=None, operation='set', name=None, value=None):
        if 'TEST_VIEW' not in req.perm:
            raise PermissionError('TEST_VIEW', realm)
            
        if operation == 'set' and 'TEST_MODIFY' not in req.perm:
            raise PermissionError('TEST_MODIFY', realm)


    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        if self._need_upgrade(db):
            return True
        
        for realm in self.SCHEMA:
            realm_schema = self.SCHEMA[realm]

            if need_db_create_for_realm(self.env, realm, realm_schema, db) or \
                need_db_upgrade_for_realm(self.env, realm, realm_schema, db):
                    
                return True
                
        return False

    def upgrade_environment(self, db=None):
        # Create or update db
        @self.env.with_transaction(db)
        def do_upgrade_environment(db):
            for realm in self.SCHEMA:
                realm_schema = self.SCHEMA[realm]

                if need_db_create_for_realm(self.env, realm, realm_schema, db):
                    create_db_for_realm(self.env, realm, realm_schema, db)

                elif need_db_upgrade_for_realm(self.env, realm, realm_schema, db):
                    upgrade_db_for_realm(self.env, 'testmanager.upgrades', realm, realm_schema, db)
                    
            # Create default values for configuration properties and initialize counters
            db_insert_or_ignore(self.env, 'testconfig', 'NEXT_CATALOG_ID', '0', db)
            db_insert_or_ignore(self.env, 'testconfig', 'NEXT_TESTCASE_ID', '0', db)
            db_insert_or_ignore(self.env, 'testconfig', 'NEXT_PLAN_ID', '0', db)
            
            db.commit()

            # Fix templates with a blank id
            if self._check_blank_id_templates(db):
                self._fix_blank_id_templates(db)
                db.commit()
                self.env.log.info(_("""
    Test Manager templates with blank IDs have been fixed.\n
    Please go to the Administration panel, in the Test Manager Templates
    section, and check the associations between templates and Test Cases 
    and Test Catalogs.\n
    You will have to manually fix any misconfiguration you should find.
                    """))
          
            # Create the basic "TC" Wiki page, used as the root test catalog
            tc_page = WikiPage(self.env, 'TC')
            if not tc_page.exists:
                tc_page.text = ' '
                tc_page.save('System', '', '127.0.0.1')
            
                db.commit()
            
            if self._need_upgrade(db):
                # Set custom ticket field to hold related test case
                custom = self.config['ticket-custom']
                config_dirty = False
                if 'testcaseid' not in custom:
                    custom.set('testcaseid', 'text')
                    custom.set('testcaseid.label', _("Test Case"))
                    config_dirty = True
                if 'planid' not in custom:
                    custom.set('planid', 'text')
                    custom.set('planid.label', _("Test Plan"))
                    config_dirty = True

                # Set config section for test case outcomes
                if 'test-outcomes' not in self.config:
                    self.config.set('test-outcomes', 'green.SUCCESSFUL', _("Successful"))
                    self.config.set('test-outcomes', 'yellow.TO_BE_TESTED', _("Untested"))
                    self.config.set('test-outcomes', 'red.FAILED', _("Failed"))
                    self.config.set('test-outcomes', 'default', 'TO_BE_TESTED')
                    config_dirty = True

                if 'testmanager' not in self.config:
                    self.config.set('testmanager', 'ticket_summary_option', 'full_path')
                    self.config.set('testmanager', 'ticket_summary_text', '')
                    self.config.set('testmanager', 'ticket_summary_num_catalogs', '1')
                    self.config.set('testmanager', 'ticket_summary_separator', ' - ')
                    config_dirty = True

                if config_dirty:
                    self.config.save()

    def _need_upgrade(self, db):
        # Check for custom ticket field to hold related test case
        custom = self.config['ticket-custom']
        if 'testcaseid' not in custom or 'planid' not in custom:
            self.env.log.debug('TestManager needs to be upgraded: missing custom ticket fields.')
            return True

        # Check for config section for test case outcomes
        if 'test-outcomes' not in self.config:
            self.env.log.debug('TestManager needs to be upgraded: missing custom test outcomes.')
            return True

        # Check for templates with blank IDs. This was a bug in 1.5.2 that will
        # be fixed here
        if self._check_blank_id_templates(db):
            return True

        self.env.log.debug('No need to upgrade TestManager for trac.ini matters.')
        return False

    def _check_blank_id_templates(self, db):
        self.env.log.debug('Checking for templates with blank IDs.')

        cursor = db.cursor()
        try:
            sql = "SELECT count(id) FROM testmanager_templates WHERE id=''" 
            cursor.execute(sql)
            
            row = cursor.fetchone()

            if row is not None and int(row[0]) > 0:
                return True

        except:
            self.env.log.error("Error retrieving test manager templates")
            self.env.log.error(formatExceptionInfo())

        return False

    def _fix_blank_id_templates(self, db):
        @self.env.with_transaction(db)
        def do_fix_blank_id_templates(db):
            cursor = db.cursor()

            items = []

            # Copy contents of all templates with a blank id
            self.env.log.debug("Copying contents of all templates with a blank ID")
            sql = "SELECT id, name, type, description, content FROM testmanager_templates WHERE id = ''" 
            cursor.execute(sql)
            for id_, name, type_, description, content in cursor:
                template = { 'id': id_, 'name': name, 'type': type_, 'description': description, 'content': content }
                items.append(template)

            # Delete all templates with a blank id
            self.env.log.debug("Deleting templates with a blank ID")
            sql = "DELETE FROM testmanager_templates WHERE id = ''" 
            cursor.execute(sql)

            # Add the template contents back in, with ids starting with '500'
            next_id = 500
            for item in items:
                self.env.log.debug("Adding the templates back in with a correct id, starting with id='500'")
                cursor.execute("""
                    INSERT INTO testmanager_templates (id, name, type, description, content) 
                        VALUES (%s,%s,%s,%s,%s)
                """, (str(next_id), item['name'], item['type'], item['description'], item['content']))
                
                next_id += 1


