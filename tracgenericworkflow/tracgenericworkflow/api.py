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
from trac.core import Interface, Component, implements, ExtensionPoint, \
    TracError
from trac.resource import Resource, get_resource_url
from trac.util import get_reporter_id
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider

from tracgenericclass.util import formatExceptionInfo
from tracgenericworkflow.model import ResourceWorkflowState


class IWorkflowTransitionListener(Interface):
    """
    Extension point interface for components that require notification
    when objects transition between states.
    """

    def object_transition(self, res_wf_state, resource, action, old_state, new_state):
        """
        Called when an object has transitioned to a new state.

        :param res_wf_state: the ResourceWorkflowState  
                             transitioned from old_state to new_state
        :param resource: the Resource object transitioned.
        :param action: the action been performed.
        """


class IWorkflowTransitionAuthorization(Interface):
    """
    Extension point interface for components that wish to augment the
    state machine at runtime, by allowing or denying each transition
    based on the object and the current and new states.
    """

    def is_authorized(self, res_wf_state, resource, action, old_state, new_state):
        """
        Called before allowing the transition.
        Return True to allow for the transition, False to deny it.
        
        :param res_wf_state: the ResourceWorkflowState being 
                             transitioned from old_state to new_state
        :param resource: the Resource object being transitioned.
        :param action: the action being performed.
        """


class IWorkflowOperationProvider(Interface):
    """
    Extension point interface for components willing to implement
    custom workflow operations.
    """

    def get_implemented_operations(self):
        """
        Return custom actions provided by the component.

        :rtype: `basestring` generator
        """

    def get_operation_control(self, req, action, operation, res_wf_state, resource):
        """
        Asks the provider to provide UI control to let the User 
        perform the specified operation on the given resource.
        This control(s) will be rendered inside a form and the values
        will be eventually available to this provvider in the 
        perform_operation method, to actually perform the operation.
        
        :param req: the http request.
        :param action: the action being performed by the User.
        :param operation: the name of the operation to be rendered.
        :param res_wf_state: the ResourceWorkflowState  
                             transitioned from old_state to new_state
        :param resource: the Resource object transitioned.
        :return: a Genshi tag with the required control(s) and a string 
                 with the operation hint.
        """
        
    def perform_operation(self, req, action, operation, old_state, new_state, res_wf_state, resource):
        """
        Perform the specified operation on the given resource, which 
        has transitioned from the given old to the given new state.

        :param req: the http request, which parameters contain the 
                    input fields (provided by means of 
                    'get_operation_control') that the User has now 
                    valorized.
        :param res_wf_state: the ResourceWorkflowState  
                             transitioned from old_state to new_state
        :param resource: the Resource object transitioned.
        """


class ResourceWorkflowSystem(Component):
    """
    Generic Resource workflow system for Trac.
    """

    implements(IRequestHandler, ITemplateProvider)

    transition_listeners = ExtensionPoint(IWorkflowTransitionListener)
    transition_authorizations = ExtensionPoint(IWorkflowTransitionAuthorization)
    operation_providers = ExtensionPoint(IWorkflowOperationProvider)

    actions = {}
    _operation_providers_map = None
    
    def __init__(self, *args, **kwargs):
        """
        Parses the configuration file to find all the workflows defined.
        
        To define a workflow state machine for a particular resource
        realm, add a "<realm>-resource_workflow" section in trac.ini
        and describe the state machine with the same syntax as the
        ConfigurableTicketWorkflow component.
        """
        
        Component.__init__(self, *args, **kwargs)

        from trac.ticket.default_workflow import parse_workflow_config

        for section in self.config.sections():
            if section.find('-resource_workflow') > 0:
                self.log.debug("ResourceWorkflowSystem - parsing config section %s" % section)
                realm = section.partition('-')[0]
                raw_actions = list(self.config.options(section))

                self.actions[realm] = parse_workflow_config(raw_actions)

        self._operation_providers_map = None


    # Workflow state machine management

    def get_available_actions(self, req, realm, resource=None):
        """
        Returns a list of (weight, action) tuples, for the specified 
        realm,  that are valid for this request and the current state.
        """
        self.log.debug(">>> ResourceWorkflowSystem - get_available_actions")

        # Get the list of actions that can be performed

        user_perm = None
        if resource is not None:
            user_perms = req.perm(resource)
            rws = ResourceWorkflowState(self.env, resource.id, realm)
            if rws.exists:
                curr_state = rws['state']
            else:
                curr_state = 'new'
        
        allowed_actions = []
        
        if realm in self.actions:
            for action_name, action_info in self.actions[realm].items():
                oldstates = action_info['oldstates']
                if oldstates == ['*'] or curr_state in oldstates:
                    # This action is valid in this state. 
                    # Check permissions if possible.
                    if user_perms is not None:
                        required_perms = action_info['permissions']
                        if not self._is_action_allowed(user_perms, required_perms):
                            continue
                            
                    allowed_actions.append((action_info['default'],
                                            action_name))

        self.log.debug("<<< ResourceWorkflowSystem - get_available_actions")

        return allowed_actions

    def _is_action_allowed(self, user_perms, required_perms):
        if not required_perms:
            return True
        for permission in required_perms:
            if permission in user_perms:
                return True
        return False

    def get_all_states(self, realm):
        """
        Return a set with all the states described by the configuration
        for the specified realm.
        Returns an empty set if none.
        """
        all_states = set()
        
        if realm in self.actions:
            for action_name, action_info in self.actions[realm].items():
                all_states.update(action_info['oldstates'])
                all_states.add(action_info['newstate'])
            all_states.discard('*')

        return all_states
        
    def get_action_markup(self, req, realm, action, resource=None):
        self.log.debug('get_action_markup: action "%s"' % action)

        id = None
        if resource is not None:
            id = resource.id
            
        rws = ResourceWorkflowState(self.env, id, realm)

        this_action = self.actions[realm][action]
        status = this_action['newstate']        
        operations = this_action['operations']

        controls = [] # default to nothing
        hints = []
        
        for operation in operations:
            self.env.log.debug(">>>>>>>>>>>>>>> "+operation)
            provider = self.get_operation_provider(operation)
            self.env.log.debug (provider)
            
            if provider is not None:
                control, hint = provider.get_operation_control(req, action, operation, rws, resource)
                
                controls.append(control)
                hints.append(hint)
        
        if 'leave_status' not in operations:
            if status != '*':
                hints.append(_(" Next status will be '%(name)s'", name=status))

        return (this_action['name'], tag(*controls), '. '.join(hints))

    def get_workflow_markup(self, req, base_href, realm, resource):
            rws = ResourceWorkflowState(self.env, resource.id, realm)

            # action_controls is an ordered list of "renders" tuples, where
            # renders is a list of (action_key, label, widgets, hints) representing
            # the user interface for each action
            action_controls = []
            sorted_actions = self.get_available_actions(
                req, realm, resource=resource)
            
            if len(sorted_actions) > 0:
                for action in sorted_actions:
                    first_label = None
                    hints = []
                    widgets = []

                    label, widget, hint = self.get_action_markup(req, realm, action[1], resource)

                    if not first_label:
                        first_label = label

                    widgets.append(widget)
                    hints.append(hint)

                    action_controls.append((action[1], first_label, tag(widgets), hints))

                form = tag.form(id='resource_workflow_form', 
                        name='resource_workflow_form', 
                        action=base_href+'/workflowtransition', 
                        method='get')(
                            tag.input(name='id', type='hidden', value=resource.id),
                            tag.input(name='res_realm', type='hidden', value=realm)
                        )
                
                form.append(tag.div()(
                        tag.span()("Current state: %s" % rws['state']),
                        tag.br(), tag.br()
                    ))
                
                for i, ac in enumerate(action_controls):
                    # The default action is the first in the action_controls list.
                    if i==0:
                        is_checked = 'true'
                    else:
                        is_checked = None
                    
                    form.append(tag.input(name='selected_action', type='radio', value=ac[0], checked=is_checked)(
                        ac[1],
                        tag.div()(
                            ac[2],
                            ac[3]
                            )
                        ))
                
                form.append(tag.span()(
                                tag.br(),
                                tag.input(id='resource_workflow_form_submit_button', type='submit', value='Perform Action')
                                ))
            else:
                form = tag('')

            return form


    # Workflow operations management
    
    def get_operation_provider(self, operation_name):
        """Return the component responsible for providing the specified
        custom workflow operation

        :param operation_name: the operation name
        :return: a `Component` implementing `IWorkflowOperationProvider`
                 or `None`
        """
        # build a dict of operation keys to IWorkflowOperationProvider
        # implementations
        if not self._operation_providers_map:
            map = {}
            for provider in self.operation_providers:
                for operation_name in provider.get_implemented_operations() or []:
                    map[operation_name] = provider
            self._operation_providers_map = map
        
        if operation_name in self._operation_providers_map:
            return self._operation_providers_map.get(operation_name)
        else:
            return None

    def get_known_operations(self):
        """
        Return a list of all the operation names of 
        operation providers.
        """
        operation_names = []
        for provider in self.operation_providers:
            for operation_name in provider.get_implemented_operations() or []:
                operation_names.append(operation_name)
                
        return operation_names


    # IRequestHandler methods
    # Workflow transition implementation

    def match_request(self, req):
        return req.path_info.startswith('/workflowtransition')

    def process_request(self, req):
        """Handles requests to perform a state transition."""

        author = get_reporter_id(req, 'author')

        if req.path_info.startswith('/workflowtransition'):
            # Check permission
            #req.perm.require('TEST_EXECUTE')
        
            selected_action = req.args.get('selected_action')
        
            id = req.args.get('id')
            res_realm = req.args.get('res_realm')

            res = Resource(res_realm, id)
            rws = ResourceWorkflowState(self.env, id, res_realm)

            if rws.exists:
                curr_state = rws['state']
            else:
                curr_state = 'new'

            this_action = self.actions[res_realm][selected_action]
            new_state = this_action['newstate']
            
            if new_state == '*':
                new_state = curr_state

            self.env.log.debug("Performing action %s. Transitioning the resource %s in realm %s from the state %s to the state %s" % (selected_action, id, res_realm, curr_state, new_state))
            
            try:
                # Check external authorizations
                for external_auth in self.transition_authorizations:
                    if not external_auth.is_authorized(rws, res, selected_action, curr_state, new_state):
                        TracError("External authorization to the workflow transition denied.")

                # Perform operations
                operations = this_action['operations']

                for operation in operations:
                    provider = self.get_operation_provider(operation)
                    
                    if provider is not None:
                        provider.perform_operation(req, selected_action, operation, curr_state, new_state, rws, res)
                    else:
                        self.env.log.debug("Unable to find operation provider for operation %s" % operation)

                # Transition the resource to the new state
                if rws.exists:
                    if not new_state == curr_state:
                        # Check that the resource is still in the state it 
                        # was when the User browsed it
                        if rws['state'] == curr_state:
                            rws['state'] = new_state
                            try:
                                rws.save_changes(author, "State changed")
                            except:
                                self.log.debug("Error saving the resource %s with id %s" % (res_realm, id))
                        else:
                            TracError("Resource with id %s has already changed state in the meanwhile. Current state is %s." % (id, rws['state']))
                else:
                    rws['state'] = new_state
                    rws.insert()
                
                # Call listeners
                for listener in self.transition_listeners:
                    listener.object_transition(rws, res, selected_action, curr_state, new_state)
            except:
                self.env.log.debug(formatExceptionInfo())
                raise

            # Redirect to the resource URL.
            href = get_resource_url(self.env, res, req.href)
            req.redirect(href)
        
        return 'empty.html', {}, None


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
        return [('tracgenericworkflow', resource_filename(__name__, 'htdocs'))]


        
