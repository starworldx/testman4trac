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

from trac.admin.web_ui import IAdminPanelProvider
from trac.core import Component, implements
from trac.mimeview.api import Context
from trac.web.chrome import add_notice, add_warning, add_stylesheet
from trac.wiki.formatter import format_to_html

from testmanager.api import TestManagerSystem
from tracgenericclass.model import GenericClassModelProvider
from tracgenericclass.util import formatExceptionInfo


try:
    from testmanager.api import _, tag_, N_
except ImportError:
	from trac.util.translation import _, N_
	tag_ = _

class TestManagerAdmin(Component):
    """
    Provide the functionality to add, edit and create
    templates for TestCases and TestCatalogs
    """

    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods:
    #
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield('testmanager', 'Test Manager', 'settings', _("Settings"))
            yield('testmanager', 'Test Manager', 'templates', _("Templates"))

    def render_admin_panel(self, req, cat, page, component):
        if page == 'settings':
            return self._render_settings(req, cat, page, component)
        if page == 'templates':
            return self._render_templates(req, cat, page, component)


    def _render_settings(self, req, cat, page, component):
        req.perm.assert_permission('TRAC_ADMIN')

        data = {}

        try:
            if req.method == 'POST':
                default_days_back = req.args.get('default_days_back', '90')
                default_interval = req.args.get('default_interval', '7')
                testplan_sortby = req.args.get('testplan_sortby', 'custom')
                open_new_window = req.args.get('open_new_window', 'False')
                testcatalog_default_view = req.args.get('testcatalog_default_view', 'tree')
                testplan_default_view = req.args.get('testplan_default_view', 'tree')

                self.env.config.set('testmanager', 'default_days_back', default_days_back)
                self.env.config.set('testmanager', 'default_interval', default_interval)
                self.env.config.set('testmanager', 'testplan.sortby', testplan_sortby)
                self.env.config.set('testmanager', 'testcase.open_new_window', ('False', 'True')[open_new_window == 'on'])
                self.env.config.set('testmanager', 'testcatalog.default_view', testcatalog_default_view)
                self.env.config.set('testmanager', 'testplan.default_view', testplan_default_view)

                _set_columns_visible(self.env, 'testcatalog', req.args, self.env.config)
                _set_columns_visible(self.env, 'testplan', req.args, self.env.config)
                
                _set_columns_total_operation(self.env, 'testcatalog', req.args, self.env.config)
                _set_columns_total_operation(self.env, 'testplan', req.args, self.env.config)
                
                self.env.config.save()
                add_notice(req, _("Settings saved"))
        except:
            self.env.log.error(formatExceptionInfo())
            add_warning(req, _("Error saving the settings"))

        data['default_days_back'] = self.env.config.get('testmanager', 'default_days_back', '90')
        data['default_interval'] = self.env.config.get('testmanager', 'default_interval', '7')
        data['testplan_sortby'] = self.env.config.get('testmanager', 'testplan.sortby', 'custom')
        data['open_new_window'] = self.env.config.get('testmanager', 'testcase.open_new_window', 'False')
        data['testcatalog_default_view'] = self.env.config.get('testmanager', 'testcatalog.default_view', 'tree')
        data['testplan_default_view'] = self.env.config.get('testmanager', 'testplan.default_view', 'tree')
        
        testcatalog_columns, foo, bar = get_all_table_columns_for_object(self.env, 'testcatalog', self.env.config)
        testplan_columns, foo, bar = get_all_table_columns_for_object(self.env, 'testplan', self.env.config)
        
        data['testcatalog_columns'] = testcatalog_columns
        data['testplan_columns'] = testplan_columns
        
        return 'admin_settings.html', data

    def _render_templates(self, req, cat, page, component):
        req.perm.assert_permission('TRAC_ADMIN')

        for key, value in req.args.items():
            self.env.log.debug("Key: %s, Value: %s", key, value)

        testmanagersystem = TestManagerSystem(self.env)

        context = Context.from_request(req)

        data = {}

        data['template_overview'] = True
        data['edit_template'] = False

        data['tc_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCASE)
        data['tcat_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCATALOG)
        data['tcat_list'] = testmanagersystem.get_testcatalogs()
        data['tcat_selected'] = testmanagersystem.get_default_tcat_template_id()
        data['tc_selected'] = testmanagersystem.get_default_tc_template_id()

        if req.method == 'POST':
            
            # add a Test Case template?
            if req.args.get('tc_add'):
                tc_name = req.args.get('tc_add_name')
                self.env.log.debug("Add new TC-template: %s" % tc_name)

                if len(tc_name) > 0:
                    if testmanagersystem.template_exists(tc_name, testmanagersystem.TEMPLATE_TYPE_TESTCASE):
                        data['tc_add_name'] = tc_name
                        add_warning(req, _("A Test Case template with that name already exists"))
                    else:
                        data['template_overview'] = False
                        data['edit_template'] = True
                        data['t_edit_type'] = testmanagersystem.TEMPLATE_TYPE_TESTCASE
                        data['t_edit_name'] = tc_name
                        data['t_edit_action'] = 'ADD'
                else:
                    add_warning(req, _("Please enter a Template name first"))

            # add a Test Catalog template?
            if req.args.get('tcat_add'):
                tcat_name = req.args.get('tcat_add_name')
                self.env.log.debug("Add new TCat-template: %s" % tcat_name)

                if len(tcat_name) > 0:
                    if testmanagersystem.template_exists(tcat_name, testmanagersystem.TEMPLATE_TYPE_TESTCATALOG):
                        data['tcat_add_name'] = tcat_name
                        add_warning(req, _("A Test Catalog template with that name already exists"))
                    else:
                        data['template_overview'] = False
                        data['edit_template'] = True
                        data['t_edit_type'] = testmanagersystem.TEMPLATE_TYPE_TESTCATALOG
                        data['t_edit_name'] = tcat_name
                        data['t_edit_action'] = 'ADD'
                else:
                    add_warning(req, _("Please enter a Template name first"))

            # delete a Test Case template?
            if req.args.get('tc_del'):
                tc_sel = req.args.get('tc_sel')
                tc_default = testmanagersystem.get_default_tc_template_id()
                tc_to_delete = []
                
                if isinstance(tc_sel, basestring):
                    tc_to_delete.append(tc_sel)
                else:
                    tc_to_delete = tc_sel

                for t_id in tc_to_delete:
                    t = testmanagersystem.get_template_by_id(t_id)
                    if t_id == tc_default:
                        add_warning(req, _("Template '%s' not removed as it is currently the default template") % t['name'])
                        continue
                    
                    if testmanagersystem.template_in_use(t_id):
                        add_warning(req, _("Template '%s' not removed as it is in use for a Test Catalog") % t['name'])
                        continue
                    
                    self.env.log.debug("remove test case template with id: " + t_id)
                    if not testmanagersystem.remove_template(t_id):
                        add_warning(req, _("Error deleting Test Case template '%s'") % t['name'])
                    else:
                        add_notice(req, _("Test Case template '%s' deleted") % t['name'])
                    
                data['tc_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCASE)
                data['tcat_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCATALOG)

            # delete a Test Catalog template?
            if req.args.get('tcat_del'):
                tcat_sel = req.args.get('tcat_sel')
                tcat_default = testmanagersystem.get_default_tcat_template_id()
                tcat_to_delete = []
                
                if isinstance(tcat_sel, basestring):
                    tcat_to_delete.append(tcat_sel)
                else:
                    tcat_to_delete = tcat_sel
                    
                for t_id in tcat_to_delete:
                    t = testmanagersystem.get_template_by_id(t_id)
                    if t_id == tcat_default:
                        add_warning(req, _("Template '%s' not removed as it is currently the default template") % t['name'])
                        continue
                    
                    self.env.log.debug("remove test catalog template with id: " + t_id)
                    if not testmanagersystem.remove_template(t_id):
                        add_warning(req, _("Error deleting Test Catalog template '%s'") % t['name'])
                    else:
                        add_notice(req, _("Test Catalog template '%s' deleted") % t['name'])
                        
                data['tc_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCASE)
                data['tcat_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCATALOG)

            # save default Test Catalog template
            if req.args.get('tcat_default_save'):
                tcat_default = req.args.get('tcat_default')
                if testmanagersystem.set_config_property('TEST_CATALOG_DEFAULT_TEMPLATE', tcat_default):
                    add_notice(req, _("Default Test Catalog template updated"))
                    data['tcat_selected'] = tcat_default
                else:
                    add_warning(req, _("Failed to update default Test Catalog template"))

            # save default Test Case template
            if req.args.get('tc_default_save'):
                tc_default = req.args.get('tc_default')
                if testmanagersystem.set_config_property('TEST_CASE_DEFAULT_TEMPLATE', tc_default):
                    add_notice(req, _("Default Test Case template updated"))
                    data['tc_selected'] = tc_default
                else:
                    add_warning(req, _("Failed to update default Test Catalog template"))

            # save templates for TestCatalogs
            if req.args.get('tc_templates_save'):
                warning = False
                for key, value in req.args.items():
                    self.env.log.debug("checking key: " + key)
                    if 'TC_TEMPLATE_FOR_TCAT_' in key:
                        self.env.log.debug("saving tc-template for: %s, value: %s" % (key, value))
                        if not testmanagersystem.set_config_property(key, value):
                            warning = True
                if warning:
                    add_warning(req, _("Failed to update Test Case templates"))
                else:
                    add_notice(req, _("Default Test Case templates updated"))
                    data['tcat_list'] = testmanagersystem.get_testcatalogs()

            # preview template
            if req.args.get('t_edit_preview'):
                data['template_overview'] = False
                data['edit_template'] = True
                data['t_edit_id'] = req.args.get('t_edit_id')
                data['t_edit_type'] = req.args.get('t_edit_type')
                data['t_edit_name'] = req.args.get('t_edit_name')
                data['t_edit_description'] = req.args.get('t_edit_description')
                data['t_edit_content'] = req.args.get('t_edit_content')
                data['t_edit_action'] = req.args.get('t_edit_action')
                data['t_show_preview'] = True
                data['t_preview_content'] = format_to_html(self.env, context, req.args.get('t_edit_content'))

            # save an edited template?
            if req.args.get('t_edit_save'):
                t_id = req.args.get('t_edit_id')
                t_type = req.args.get('t_edit_type')
                t_name = req.args.get('t_edit_name')
                t_desc = req.args.get('t_edit_description')
                t_cont = req.args.get('t_edit_content')
                t_action = req.args.get('t_edit_action')

                testmanagersystem.save_template(t_id, t_name, t_type, t_desc, t_cont, t_action)

                data['template_overview'] = True
                data['edit_template'] = False
                data['tc_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCASE)
                data['tcat_templates'] = testmanagersystem.get_templates(testmanagersystem.TEMPLATE_TYPE_TESTCATALOG)
                add_notice(req, _("Template saved"))

        else:
            # method 'GET' (template selected for 'edit')
            if component:
                t_type = req.args.get('t_type')
                t_id = component
                self.env.log.debug("component: " + component)
                template = testmanagersystem.get_template_by_id(t_id)

                data['t_edit_id'] = template['id']
                data['t_edit_type'] = template['type']
                data['t_edit_name'] = template['name']
                data['t_edit_description'] = template['description']
                data['t_edit_content'] = template['content']
                data['t_edit_action'] = 'EDIT'

                data['template_overview'] = False
                data['edit_template'] = True

        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'testmanager/css/admin.css')
        return 'admin_templates.html', data

        
def get_all_table_columns_for_object(env, objtype, settings):
    genericClassModelProvider = GenericClassModelProvider(env)
    
    tcat_fields = genericClassModelProvider.get_custom_fields_for_realm('testcatalog')
    tcat_has_custom = tcat_fields is not None and len(tcat_fields) > 0
    
    tc_fields = genericClassModelProvider.get_custom_fields_for_realm('testcase')
    tc_has_custom = tc_fields is not None and len(tc_fields) > 0

    if objtype == 'testplan':
        tcip_fields = genericClassModelProvider.get_custom_fields_for_realm('testcaseinplan')
        tcip_has_custom = tcip_fields is not None and len(tcip_fields) > 0
    else:
        tcip_fields = False
        tcip_has_custom = None

    custom_ctx = {
        'testcatalog': [tcat_has_custom, tcat_fields],
        'testcase': [tc_has_custom, tc_fields],
        'testcaseinplan': [tcip_has_custom, tcip_fields]
        }
   
    result = []
    result_map = {}
    
    # Common columns
    result.append({'name': 'title', 'label': _("Name"), 'visible': _is_column_visible(objtype, 'title', settings), 'totals': _get_column_total_operation(objtype, 'title', settings)})
            
    # Custom testcatalog columns
    if tcat_has_custom:
        for f in tcat_fields:
            result.append(_get_column_settings(objtype, f, settings))

    # Base testcase columns
    result.append({'name': 'id', 'label': _("ID"), 'visible': _is_column_visible(objtype, 'id', settings), 'totals': _get_column_total_operation(objtype, 'id', settings)})

    # Custom testcase columns
    if tc_has_custom:
        for f in tc_fields:
            result.append(_get_column_settings(objtype, f, settings))

    if objtype == 'testplan':
        # Base testcaseinplan columns
        result.append({'name': 'status', 'label': _("Status"), 'visible': _is_column_visible(objtype, 'status', settings), 'totals': _get_column_total_operation(objtype, 'status', settings)})
        result.append({'name': 'author', 'label': _("Author"), 'visible': _is_column_visible(objtype, 'author', settings), 'totals': _get_column_total_operation(objtype, 'author', settings)})
        result.append({'name': 'time', 'label': _("Last Change"), 'visible': _is_column_visible(objtype, 'time', settings), 'totals': _get_column_total_operation(objtype, 'time', settings)})

        # Custom testcaseinplan columns
        if tcip_has_custom:
            for f in tcip_fields:
                result.append(_get_column_settings(objtype, f, settings))

    # Full test case description
    result.append({'name': 'description', 'label': _("Description"), 'visible': _is_column_visible(objtype, 'description', settings), 'totals': _get_column_total_operation(objtype, 'description', settings)})

    for r in result:
        result_map[r['name']] = r
    
    return result, result_map, custom_ctx
    
def _get_column_settings(objtype, field, settings):
    return {'name': field['name'], 'label': field['label'], 'visible': _is_column_visible(objtype, field['name'], settings), 'totals': _get_column_total_operation(objtype, field['name'], settings)}

def _is_column_visible(objtype, column_name, settings):
    visible = settings.get('testmanager', objtype + '.visible_'+column_name)
    
    if visible is None or visible == '' or visible == 'True':
        return 'True'
    
    return 'False'
    
def _set_columns_visible(env, objtype, args, settings):
    columns, foo, bar = get_all_table_columns_for_object(env, objtype, settings)

    for column in columns:
        col_name = objtype + '.' + column['name']
        if args.get(col_name, '') == 'on':
            settings.remove('testmanager', objtype + '.visible_'+column['name'])
        else:
            settings.set('testmanager', objtype + '.visible_'+column['name'], 'False')

def _get_column_total_operation(objtype, column_name, settings):
    operation = settings.get('testmanager', objtype + '.totals_'+column_name)
    
    if operation is None or operation == '':
        return None
    
    return operation
    
def _set_columns_total_operation(env, objtype, args, settings):
    columns, foo, bar = get_all_table_columns_for_object(env, objtype, settings)

    for column in columns:
        arg_name = 'totals.' + objtype + '_' + column['name']
        if args.get(arg_name, 'none') != 'none':
            settings.set('testmanager', objtype + '.totals_'+column['name'], args.get(arg_name))
        else:
            settings.remove('testmanager', objtype + '.totals_'+column['name'])
