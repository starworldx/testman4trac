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
from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.resource import Resource
from trac.web.api import ITemplateStreamFilter

from tracgenericclass.util import get_string_from_dictionary
from tracgenericworkflow.api import IWorkflowOperationProvider, \
    ResourceWorkflowSystem


# Workflow support
class TestManagerWorkflowInterface(Component):
    """Adds workflow capabilities to the TestManager plugin."""
    
    implements(IWorkflowOperationProvider, ITemplateStreamFilter)

    # IWorkflowOperationProvider methods
    # Just a sample operation
    def get_implemented_operations(self):
        self.log.debug(">>> TestManagerWorkflowInterface - get_implemented_operations")
        self.log.debug("<<< TestManagerWorkflowInterface - get_implemented_operations")

        yield 'sample_operation'

    def get_operation_control(self, req, action, operation, res_wf_state, resource):
        self.log.debug(">>> TestManagerWorkflowInterface - get_operation_control: %s" % operation)

        if operation == 'sample_operation':
            id = 'action_%s_operation_%s' % (action, operation)
            speech = 'Hello World!'

            control = tag.input(type='text', id=id, name=id, 
                                    value=speech)
            hint = "Will sing %s" % speech

            self.log.debug("<<< TestManagerWorkflowInterface - get_operation_control")
            
            return control, hint
        
        return None, ''
        
    def perform_operation(self, req, action, operation, old_state, new_state, res_wf_state, resource):
        self.log.debug("---> Performing operation %s while transitioning from %s to %s."
            % (operation, old_state, new_state))

        speech = req.args.get('action_%s_operation_%s' % (action, operation), 'Not found!')

        self.log.debug("        The speech is %s" % speech)


    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        page_name = req.args.get('page', 'WikiStart')
        planid = req.args.get('planid', '-1')

        if page_name == 'TC':
            # The root catalog does not have workflows
            return stream

        if page_name.startswith('TC') and filename == 'wiki_view.html':
            self.log.debug(">>> TestManagerWorkflowInterface - filter_stream")
            req.perm.require('TEST_VIEW')
            
            # Determine which object is being displayed (i.e. realm), 
            # based on Wiki page name and the presence of the planid 
            # request parameter.
            realm = None
            if page_name.find('_TC') >= 0:
                if not planid or planid == '-1':
                    realm = 'testcase'
                    key = {'id': page_name.rpartition('_TC')[2]}
                else:
                    realm = 'testcaseinplan'
                    key = {'id': page_name.rpartition('_TC')[2], 'planid': planid}
            else:
                if not planid or planid == '-1':
                    realm = 'testcatalog'
                    key = {'id': page_name.rpartition('_TT')[2]}
                else:
                    realm = 'testplan'
                    key = {'id': planid}

            id = get_string_from_dictionary(key)
            res = Resource(realm, id)

            rwsystem = ResourceWorkflowSystem(self.env)
            workflow_markup = rwsystem.get_workflow_markup(req, '..', realm, res)
            
            self.log.debug("<<< TestManagerWorkflowInterface - filter_stream")

            return stream | Transformer('//div[contains(@class,"wikipage")]').after(workflow_markup) 

        return stream

