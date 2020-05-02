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

from trac.util import get_reporter_id

from testmanager.api import TestManagerSystem
from testmanager.model import TestCatalog, TestCase, TestCaseInPlan, TestPlan
from tracgenericclass.util import formatExceptionInfo
from trac.core import Component, implements


try:
    # Check that tracrpc plugin is available. Otherwise, an ImportError exception will be raised.
    from tracrpc.api import IXMLRPCHandler


    __all__ = ['TestManagerRPC']

    class TestManagerRPC(Component):
        implements(IXMLRPCHandler)

        def __init__(self):
            self.testmanagersys = TestManagerSystem(self.env)

        def xmlrpc_namespace(self):
            return 'testmanager'

        def xmlrpc_methods(self):
            yield ('TEST_MODIFY', ((str, str, str, str),(str, str, str, str, dict)), self.createTestCatalog)
            yield ('TEST_MODIFY', ((str, str, str, str),(str, str, str, str, dict)), self.createTestCase)
            yield ('TEST_PLAN_ADMIN', ((str, str, str),(str, str, str, dict)), self.createTestPlan)
            yield (None, ((bool, str, str),), self.deleteTestObject)
            yield (None, ((bool, str, str),(bool, str, str, dict)), self.modifyTestObject)
            yield (None, ((bool, str, str, str),), self.setTestCaseStatus)
            yield ('TEST_VIEW', ((list, str),(list, str, str)), self.listTestCases)
            yield ('TEST_VIEW', ((list, str),), self.getTestCatalog)
            yield ('TEST_VIEW', ((list, str),(list, str, str)), self.getTestCase)
            yield ('TEST_VIEW', ((list, str, str),), self.getTestPlan)
            yield ('TEST_VIEW', ((list,),), self.listRootCatalogs)
            yield ('TEST_VIEW', ((list, str),), self.listSubCatalogs)
            yield ('TEST_VIEW', ((list, str),), self.listTestPlans)

        def createTestCatalog(self, req, parent_catalog_id, title, description, customfields = {}):
            """ Creates a new test catalog, in the parent catalog specified, 
            with the specified title and description.
            To create a root catalog, specify '' as the parent catalog.
            Returns the generated object ID, or '-1' if an error occurs. """
            
            result = '-1'
            try:
                id_ = self.testmanagersys.get_next_id('catalog')

                pagename = None
                if parent_catalog_id is not None and parent_catalog_id != '':
                    # Check parent catalog really exists, and get its page_name
                    tcat = TestCatalog(self.env, parent_catalog_id)
                    if not tcat.exists:
                        self.env.log.error("Input parent test catalog with ID %s not found." % parent_catalog_id)
                        return result
                        
                    pagename = tcat['page_name'] + '_TT' + id_
                else:
                    pagename = 'TC_TT' + id_

                author = get_reporter_id(req, 'author')
                
                new_tc = TestCatalog(self.env, id_, pagename, title, description)
                new_tc.author = author
                new_tc.remote_addr = req.remote_addr
                
                for custom_field_name in customfields:
                    new_tc[custom_field_name] = customfields[custom_field_name]
                
                # This also creates the Wiki page
                new_tc.insert()
                result = id_
                
            except:
                self.env.log.error("Error adding test catalog with title '%s' in catalog with ID %s!" % (title, parent_catalog_id))
                self.env.log.error(formatExceptionInfo())
            
            return id_

        def createTestCase(self, req, catalog_id, title, description, customfields = {}):
            """ Creates a new test case, in the catalog specified, with the 
            specified title and description.
            Returns the generated object ID, or '-1' if an error occurs. """
            
            result = '-1'
            try:
                if catalog_id is None or catalog_id == '':
                    self.env.log.error("Cannot create a test plan on the root catalog container.")
                    return result
                
                # Check catalog really exists, and get its page_name
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                    return result
                
                author = get_reporter_id(req, 'author')
                
                id_ = self.testmanagersys.get_next_id('testcase')
                pagename = tcat['page_name'] + '_TC' + id_

                new_tc = TestCase(self.env, id_, pagename, title, description)
                new_tc.author = author
                new_tc.remote_addr = req.remote_addr
                
                for custom_field_name in customfields:
                    new_tc[custom_field_name] = customfields[custom_field_name]

                # This also creates the Wiki page
                new_tc.insert()
                result = id_
                
            except:
                self.env.log.error("Error adding test case with title '%s' in catalog with ID %s!" % (title, catalog_id))
                self.env.log.error(formatExceptionInfo())
            
            return id_

        def createTestPlan(self, req, catalog_id, name, customfields = {}):
            """ Creates a new test plan, on the catalog specified, with the 
            specified name.
            Returns the generated object ID, or '-1' if an error occurs. """
            
            result = '-1'
            try:
                # Check catalog really exists, and get its page_name
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                    return result
                
                author = get_reporter_id(req, 'author')
                
                id_ = self.testmanagersys.get_next_id('testplan')
                pagename = tcat['page_name']

                new_tp = TestPlan(self.env, id_, catalog_id, pagename, name, author)
                
                for custom_field_name in customfields:
                    new_tp[custom_field_name] = customfields[custom_field_name]

                new_tp.insert()
                result = id_
                
            except:
                self.env.log.error("Error adding test plan with name '%s' for catalog with ID %s!" % (name, catalog_id))
                self.env.log.error(formatExceptionInfo())
            
            return result

        def deleteTestObject(self, req, objtype, id_):
            """ Deletes the test object of the specified type identified
            by the given id. 
            Returns True if successful, False otherwise. """
            
            try:
                # Check the object exists
                obj = None
                if objtype == 'testcatalog':
                    req.perm.require('TEST_MODIFY')
                    obj = TestCatalog(self.env, id_)
                elif objtype == 'testcase':
                    req.perm.require('TEST_MODIFY')
                    obj = TestCase(self.env, id_)
                elif objtype == 'testplan':
                    req.perm.require('TEST_PLAN_ADMIN')
                    obj = TestPlan(self.env, id_)

                if not obj.exists:
                    self.env.log.error("Input test object of type %s with ID %s not found." % (objtype, id_))
                    return False

                obj.delete()
                
            except:
                self.env.log.error("Error deleting test object of type %s with ID %s." % (objtype, id_))
                self.env.log.error(formatExceptionInfo())
                return False
            
            return True

        def modifyTestObject(self, req, objtype, id_, attributes={}):
            """ Modifies the test object of the specified type identified
            by the given id.
            For testcaseinplan objects, also the 'planid' attrribute is required 
            te be specified in the attributes dictionary.
            Returns True if successful, False otherwise. """

            try:
                # Check the object exists
                obj = None
                if objtype == 'testcatalog':
                    req.perm.require('TEST_MODIFY')
                    obj = TestCatalog(self.env, id_)
                elif objtype == 'testcase':
                    req.perm.require('TEST_MODIFY')
                    obj = TestCase(self.env, id_)
                elif objtype == 'testplan':
                    req.perm.require('TEST_PLAN_ADMIN')
                    obj = TestPlan(self.env, id_)
                elif objtype == 'testcaseinplan':
                    req.perm.require('TEST_EXECUTE')
                    if not 'planid' in attributes:
                        self.env.log.error("'planid' attribute must be provided.")
                        
                    # Note: Test case in plan objects may not exist if their status has not been set yet
                    obj = TestCaseInPlan(self.env, id_, attributes['planid'])

                if not obj.exists:
                    self.env.log.error("Input test object of type %s with ID %s not found." % (objtype, id_))
                    return False

                author = get_reporter_id(req, 'author')

                for k, v in attributes.iteritems():
                    if k == 'title':
                        obj.title = v
                    elif k == 'description':
                        obj.description = v
                    else:
                        obj[k] = v
                    
                obj.author = author
                obj.remote_addr = req.remote_addr
                obj.save_changes(author, "Changed through RPC.")

            except:
                self.env.log.error("Error modifying test object of type %s with ID %s." % (objtype, id_))
                self.env.log.error(formatExceptionInfo())
                return False
            
            return True

        def setTestCaseStatus(self, req, testcase_id, plan_id, status):
            """ Sets the test case status.
            Returns True if successful, False otherwise. """
            
            try:
                author = get_reporter_id(req, 'author')

                tcip = TestCaseInPlan(self.env, testcase_id, plan_id)
                if tcip.exists:
                    tcip.set_status(status, author)
                    tcip.save_changes(author, "Status changed")
                else:
                    tc = TestCase(self.env, testcase_id)
                    tcip['page_name'] = tc['page_name']
                    tcip.set_status(status, author)
                    tcip.insert()

            except:
                self.env.log.error("Error setting the test case status with ID %s on plan %s to %s!" % (testcase_id, plan_id, status))
                self.env.log.error(formatExceptionInfo())
                return False

            return True
                
        def getTestCatalog(self, req, catalog_id):
            """ Returns the catalog properties.
            The result is in the form, all strings:
            (wiki_page_name, title, description, customfields) """
            
            try:
                # Check catalog really exists
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                else:
                    customfields = []
                    self._append_custom_fields(tcat, customfields)

                    return (tcat['page_name'], tcat.title, tcat.description, customfields)

            except:
                self.env.log.error("Error getting the test catalog with ID %s!" % catalog_id)
                self.env.log.error(formatExceptionInfo())
                
        def getTestCase(self, req, testcase_id, plan_id=''):
            """ Returns the test case properties.
            If plan_id is provided, also the status of the test case in the
            plan will be returned.
            Each result is in the form, all strings:
                If plan_id is NOT provided:
                    (wiki_page_name, title, description, customfields)
                If plan_id is provided:
                    (wiki_page_name, title, description, status, customfields) """
            
            try:
                # Check test case really exists
                tc = TestCase(self.env, testcase_id)
                if not tc.exists:
                    self.env.log.error("Input test case with ID %s not found." % testcase_id)
                else:
                    customfields = []
                    self._append_custom_fields(tc, customfields)

                    if plan_id is None or plan_id == '':
                        return (tc['page_name'], tc.title, tc.description, customfields)
                    else:
                        tcip = TestCaseInPlan(self.env, testcase_id, plan_id)
                        self._append_custom_fields(tcip, customfields)
                        return (tc['page_name'], tc.title, tc.description, tcip['status'], customfields)

            except:
                self.env.log.error("Error getting the test case with ID %s!" % testcase_id)
                self.env.log.error(formatExceptionInfo())
                
        def getTestPlan(self, req, plan_id, catalog_id):
            """ Returns the test plan properties.
            The result is in the form, all strings:
            (wiki_page_name, name, customfields) """
            
            try:
                # Check test plan really exists
                tp = TestPlan(self.env, plan_id, catalog_id)
                if not tp.exists:
                    self.env.log.error("Input test plan with ID %s on catalog %s not found." % (plan_id, catalog_id))
                else:
                    customfields = []
                    self._append_custom_fields(tp, customfields)

                    return (tp['page_name'], tp['name'], customfields)

            except:
                self.env.log.error("Error getting the test plan with ID %s on catalog %s." % (plan_id, catalog_id))
                self.env.log.error(formatExceptionInfo())
                
        def listRootCatalogs(self, req):
            """ Returns a iterator over the root-level test catalogs.
            Each result is in the form, all strings:
            (test_catalog_id, wiki_page_name, title, description, customfields) """
            
            try:
                for tc in TestCatalog.list_root_catalogs(self.env):
                    customfields = []
                    self._append_custom_fields(tc, customfields)

                    yield (tc['id'], tc['page_name'], tc.title, tc.description, customfields)
                
            except:
                self.env.log.error("Error listing the root-level test catalogs!")
                self.env.log.error(formatExceptionInfo())

        def listSubCatalogs(self, req, catalog_id):
            """ Returns a iterator over the direct sub-catalogs of the specified 
            catalog.
            Each result is in the form, all strings:
            (test_catalog_id, wiki_page_name, title, description, customfields) """
            
            try:
                # Check catalog really exists
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                else:
                    for tc in tcat.list_subcatalogs():
                        customfields = []
                        self._append_custom_fields(tc, customfields)

                        yield (tc['id'], tc['page_name'], tc.title, tc.description, customfields)
                
            except:
                self.env.log.error("Error listing the test catalogs!")
                self.env.log.error(formatExceptionInfo())

        def listTestPlans(self, req, catalog_id):
            """ Returns a iterator over the test plans associated 
            to the specified catalog.
            Each result is in the form, all strings:
            (testplan_id, name, customfields) """
            
            try:
                # Check catalog really exists
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                else:
                    for tp in tcat.list_testplans():
                        customfields = []
                        self._append_custom_fields(tp, customfields)

                        yield (tp['id'], tp['name'], customfields)
                
            except:
                self.env.log.error("Error listing the test plans!")
                self.env.log.error(formatExceptionInfo())

        def listTestCases(self, req, catalog_id, plan_id=''):
            """ Returns a iterator over the test cases directly in the 
            specified catalog (no sub-catalogs).
            If plan_id is provided, also the status of the test case in the
            plan will be returned.
            Each result is in the form, all strings:
                If plan_id is NOT provided:
                    (testcase_id, wiki_page_name, title, description, customfields)
                If plan_id is provided:
                    (testcase_id, wiki_page_name, status, customfields) """
            
            try:
                # Check catalog really exists
                tcat = TestCatalog(self.env, catalog_id)
                if not tcat.exists:
                    self.env.log.error("Input test catalog with ID %s not found." % catalog_id)
                else:
                    tc_list = {}
                    if plan_id is None or plan_id == '':
                        for tc in tcat.list_testcases():
                            # Returned object is a TestCase
                            customfields = []
                            self._append_custom_fields(tc, customfields)

                            tc_list[tc['exec_order']] = (tc['id'], tc['page_name'], tc.title, tc.description, customfields)
                    else:
                        for tcip in tcat.list_testcases(plan_id):
                            # Returned object is a TestCaseInPlan
                            customfields = []
                            self._append_custom_fields(tcip, customfields)

                            tc_list[tcip['exec_order']] = (tcip['id'], tcip['page_name'], tcip['status'], customfields)

                    for key in sorted(tc_list.keys()):
                        yield tc_list[key]
                
            except:
                self.env.log.error("Error listing the test cases in the catalog with ID %s!" % catalog_id)
                self.env.log.error(formatExceptionInfo())

        def _append_custom_fields(self, obj, customfields):
            for field in obj.fields:
                if field.get("custom"):
                    customtuple = (field.get('name'), obj[field.get('name')], field.get('label'))
                    customfields.append(customtuple)

except ImportError:
    print "\n\nError importing optional Trac XML-RPC Plugin. No XML-RPC remote interface will be available."
    print "If you require XML-RPC access to the Test Manager, download and install it from http://trac-hacks.org/wiki/XmlRpcPlugin.\n\n"
