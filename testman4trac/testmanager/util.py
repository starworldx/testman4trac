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

from trac.util.text import CRLF


def get_page_title(text):
    result = None
    
    if text is not None:
        result = text.split('\n')[0].strip('\r\n').strip('= \'')

    if result == None:
        if text is not None:
            result = text
        else:
            result = ''
    
    return result
    
def get_page_description(text):
    result = None
    
    if text is not None:
        result = text.partition(CRLF)[2]

    if result == None:
        if text is not None:
            result = text
        else:
            result = ''
        
    return result
 
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)
    
quotes_escape_table = {
    "'": "\\'",
    }

def quotes_escape(text):
    return "".join(quotes_escape_table.get(c,c) for c in text)

