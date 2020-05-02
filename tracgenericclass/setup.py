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

from setuptools import setup

setup(
    name='TracGenericClass',
    version='1.1.7',
    packages=['tracgenericclass'],
    package_data={'tracgenericclass' : ['*.txt', 'templates/*.html', 'htdocs/*.*', 'htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.*']},
    author = 'Roberto Longobardi',
    author_email='otrebor.dev@gmail.com',
    license='Modified BSD, same as Trac. See the file COPYING contained in the package.',
    url='http://trac-hacks.org/wiki/TestManagerForTracPlugin',
    download_url='https://sourceforge.net/projects/testman4trac/files/',
    description='Test management plugin for Trac - Trac Generic Class component',
    long_description='A Trac plugin to create Test Cases, organize them in catalogs and track their execution status and outcome. This module provides a framework to help creating classes on Trac that: are persisted on the DB, support change history, Support extensibility through custom properties that the User can specify declaratively in the trac.ini file. Also provides an intermediate class to build objects that wrap Wiki pages, plus additional properties.',
    keywords='trac plugin generic class framework persistence test case management project quality assurance statistics stats charts charting graph',
    entry_points = {'trac.plugins': ['tracgenericclass = tracgenericclass']}
    )
