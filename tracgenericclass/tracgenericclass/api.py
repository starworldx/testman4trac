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

from trac.search import ISearchSource
from trac.util import get_reporter_id
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider

from tracgenericclass.model import GenericClassModelProvider
from trac.core import Interface, Component, ExtensionPoint, implements
from tracgenericclass.util import get_dictionary_from_string,\
    formatExceptionInfo


class IGenericObjectChangeListener(Interface):
    """
    Extension point interface for components that require notification
    when objects are created, modified, or deleted.
    """

    def object_created(self, g_object):
        """Called when an object is created."""

    def object_changed(self, g_object, comment, author, old_values):
        """Called when an object is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """

    def object_deleted(self, g_object):
        """Called when an object is deleted."""


class GenericClassSystem(Component):
    """
    Generic Class system for Trac.
    """

    implements(IRequestHandler, ITemplateProvider, ISearchSource)

    change_listeners = ExtensionPoint(IGenericObjectChangeListener)

        
    # Change listeners management

    def object_created(self, testobject):
        for c in self.change_listeners:
            c.object_created(testobject)

    def object_changed(self, testobject, comment, author):
        for c in self.change_listeners:
            c.object_changed(testobject, comment, author, testobject._old)

    def object_deleted(self, testobject):
        for c in self.change_listeners:
            c.object_deleted(testobject)

       
    # IRequestHandler methods

    def match_request(self, req):
        return (req.path_info.startswith('/propertyupdate'))

    def process_request(self, req):
        """
        Handles Ajax requests to change an object's property.
        """
        author = get_reporter_id(req, 'author')

        if req.path_info.startswith('/propertyupdate'):
            realm = req.args.get('realm')
            key_str = req.args.get('key')
            name = req.args.get('name')
            value = req.args.get('value')
            
            result = 'ERROR'
            
            key = get_dictionary_from_string(key_str)

            try:
                self.env.log.debug("Setting property %s to %s, in %s with key %s" % (name, value, realm, key))
                
                gclass_modelprovider = GenericClassModelProvider(self.env)

                gclass_modelprovider.check_permission(req, realm, key_str, name, value)

                obj = gclass_modelprovider.get_object(realm, key)
                
                # Set the required property
                obj[name] = value
                
                obj.author = author
                obj.remote_addr = req.remote_addr
                if obj is not None and obj.exists:
                    comment = "Property changed"
                    obj.save_changes(author, comment)

                    # Call listeners
                    self.object_changed(obj, comment, author)
                    
                else:
                    self.env.log.debug("Object to update not found. Creating it.")
                    props_str = req.args.get('props')
                    if props_str is not None and not props_str == '':
                        # In order to create an object, additional properties may be required
                        props = get_dictionary_from_string(props_str)
                        obj.set_values(props)
                    obj.insert()

                    # Call listeners
                    self.object_created(obj)

                result = 'OK'

            except:
                self.env.log.debug(formatExceptionInfo())

            req.send_header("Content-Length", len(result))
            req.write(result)
            return 

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
        """
        Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tracgenericclass', resource_filename(__name__, 'htdocs'))]

        
    # ISearchSource methods

    def get_search_filters(self, req):
        gclass_modelprovider = GenericClassModelProvider(self.env)

        for realm in gclass_modelprovider.get_known_realms():
            try:
                gclass_modelprovider.get_class_provider(realm).check_permission(req, realm, key_str=None, operation='search')

                metadata = gclass_modelprovider.get_metadata(realm)
                
                if 'searchable' in metadata and metadata['searchable']:
                    if 'label' in metadata:
                        label = metadata['label']
                    else:
                        label = realm.capitalize()
                    
                    yield (realm, label)
            
            except:
                self.env.log.debug("No permission to search on realm %s." % realm)


    def get_search_results(self, req, terms, filters):
        gclass_modelprovider = GenericClassModelProvider(self.env)

        known_realms = gclass_modelprovider.get_known_realms()
        
        for realm in filters:
            if realm in known_realms:
                metadata = gclass_modelprovider.get_metadata(realm)
                
                if 'searchable' in metadata and metadata['searchable']:
                    obj = gclass_modelprovider.get_object(realm)
                    if obj is not None:
                        for result in obj.get_search_results(req, terms, filters):
                            yield result


