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
from trac.web.chrome import ITemplateProvider, INavigationContributor


try:
    from testmanager.api import _, tag_, N_
except ImportError:
	from trac.util.translation import _, N_
	tag_ = _

class TestManagerTemplateProvider(Component):
    """Provides templates and static resources for the TestManager plugin."""

    implements(ITemplateProvider)

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
        return [('testmanager', resource_filename(__name__, 'htdocs'))]


class TestManager(Component):
    """Implements the /testmanager handler and the Test Manager tab."""

    implements(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if 'TEST_VIEW' in req.perm:
            return 'testmanager'

    def get_navigation_items(self, req):
        if 'TEST_VIEW' in req.perm:
            yield ('mainnav', 'testmanager',
                tag.a(_("Test Manager"), href=req.href.wiki()+'/TC', accesskey='M'))


