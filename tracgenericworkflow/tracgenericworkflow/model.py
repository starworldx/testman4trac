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

from trac.core import Component, implements
from trac.db import Table, Column
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import N_

from tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm


class ResourceWorkflowState(AbstractVariableFieldsObject):
    """
    This object represents the current workflow state of the associated
    resource.
    """
    
    # Fields that must not be modified directly by the user
    protected_fields = ('id', 'res_realm', 'state')

    def __init__(self, env, id_=None, res_realm=None, state='new', db=None):
        """
        The resource workflow state is related to a resource, the 'id' 
        and 'res_realm' arguments.
        The state can be any string.
        """
        self.values = {}

        self.values['id'] = id_
        self.values['res_realm'] = res_realm
        self.values['state'] = state

        key = self.build_key_object()
    
        AbstractVariableFieldsObject.__init__(self, env, 'resourceworkflowstate', key, db)

    def get_key_prop_names(self):
        return ['id', 'res_realm']
        
    def create_instance(self, key):
        return ResourceWorkflowState(self.env, key['id'], key['res_realm'])


class GenericWorkflowModelProvider(Component):
    """
    This class provides the data model for the generic workflow plugin.
    
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
                'resourceworkflowstate':  
                    {'table':
                        Table('resourceworkflowstate', key = ('id', 'res_realm'))[
                              Column('id'),
                              Column('res_realm'),
                              Column('state')],
                     'has_custom': True,
                     'has_change': True,
                     'version': 1}
            }

    FIELDS = {
                'resourceworkflowstate': [
                    {'name': 'id', 'type': 'text', 'label': N_('ID')},
                    {'name': 'res_realm', 'type': 'text', 'label': N_('Resource realm')},
                    {'name': 'state', 'type': 'text', 'label': N_('Workflow state')}
                ]
            }
            
    METADATA = {
                'resourceworkflowstate': {
                        'label': "Workflow State", 
                        'searchable': False,
                        'has_custom': True,
                        'has_change': True
                    },
                }

            
    # IConcreteClassProvider methods
    def get_realms(self):
            yield 'resourceworkflowstate'

    def get_data_models(self):
        return self.SCHEMA

    def get_fields(self):
        return self.FIELDS
        
    def get_metadata(self):
        return self.METADATA
        
    def create_instance(self, realm, key=None):
        obj = None
        
        if realm == 'resourceworkflowstate':
            if key is not None:
                obj = ResourceWorkflowState(self.env, key['id'], key['res_realm'])
            else:
                obj = ResourceWorkflowState(self.env)
        
        return obj

    def check_permission(self, req, realm, key_str=None, operation='set', name=None, value=None):
        pass

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        for realm in self.SCHEMA:
            realm_metadata = self.SCHEMA[realm]

            if need_db_create_for_realm(self.env, realm, realm_metadata, db) or \
                need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                
                return True
                
        return False

    def upgrade_environment(self, db=None):
        # Create or update db
        @self.env.with_transaction(db)
        def do_upgrade_environment(db):
            for realm in self.SCHEMA:
                realm_metadata = self.SCHEMA[realm]

                if need_db_create_for_realm(self.env, realm, realm_metadata, db):
                    create_db_for_realm(self.env, realm, realm_metadata, db)

                elif need_db_upgrade_for_realm(self.env, realm, realm_metadata, db):
                    upgrade_db_for_realm(self.env, 'tracgenericworkflow.upgrades', realm, realm_metadata, db)
