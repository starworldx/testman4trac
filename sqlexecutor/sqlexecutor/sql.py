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

from genshi.builder import tag
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor

from tracgenericclass.util import *


class SqlExecutor(Component):
    """SQL Executor."""

    implements(IPermissionRequestor, IRequestHandler, ITemplateProvider, INavigationContributor)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['SQL_RUN']

        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if 'SQL_RUN' in req.perm:
            return 'sqlexecutor'

    def get_navigation_items(self, req):
        if 'SQL_RUN' in req.perm:
            yield ('mainnav', 'sqlexecutor',
                tag.a(_("SQL Executor"), href=fix_base_location(req)+'/sqlexec', accesskey='Q'))


    # IRequestHandler methods

    def match_request(self, req):
        return (req.path_info.startswith('/sqlexec') and 'SQL_RUN' in req.perm)

    def process_request(self, req):
        """
        Executes a generic SQL.
        """

        req.perm.require('SQL_RUN')
        
        if req.path_info.startswith('/sqlexec'):
            sql = req.args.get('sql', '')
            format = req.args.get('format', '')
            result = []
            message = ""
            
            if not sql == '':
                self.env.log.debug(sql)

                try:
                    db = self.env.get_db_cnx()
                    cursor = db.cursor()
                    cursor.execute(sql)
                    
                    for row in cursor:
                        curr_row = []
                        for i in row:
                            if isinstance(i, basestring):
                                curr_row.append(to_unicode(i))
                            elif isinstance(i, long):
                                curr_row.append(to_unicode(str(from_any_timestamp(i).isoformat()) + ' (' + str(i) + ')'))
                            else:
                                curr_row.append(to_unicode(str(i)))
                            
                        result.append(curr_row)

                    db.commit()
                    
                    message = "Query executed successfully."
                    
                    self.env.log.debug(result)
                except:
                    message = formatExceptionInfo()
                    db.rollback()
                    self.env.log.debug("SqlExecutor - Exception: ")
                    self.env.log.debug(message)

            if format == 'tab':
                tsv_result = ''

                for row in result:
                    for col in row:
                        tsv_result += '"' + col.replace('"','""') + '"\t'
                    tsv_result += '\n'
                
                tsv_result = tsv_result.strip()
                
                if isinstance(tsv_result, unicode): 
                    tsv_result = tsv_result.encode('utf-8') 

                req.send_header("Content-Disposition", "filename=sqlresult.tsv")
                req.send_header("Content-Length", len(tsv_result))
                req.send_header("Content-Type", "text/tab-separated-values;charset=utf-8")
                req.write(tsv_result)
                return
            else:
                data = {'sql': sql, 'result': result, 'message': message, 'baseurl': fix_base_location(req)}
            
            return 'result.html', data, None


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('sqlexecutor', resource_filename(__name__, 'htdocs'))]

       
