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

import os
import re
import shutil
import sys
import traceback

from datetime import datetime

from trac.core import *
from trac.db import with_transaction

    
def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    
    excTb = traceback.format_tb(trbk, maxTBlevel)
    
    tracestring = ""
    for step in excTb:
        tracestring += step + "\n"
    
    return "Error name: %s\nArgs: %s\nTraceback:\n%s" % (excName, excArgs, tracestring)


checked_utimestamp = False
has_utimestamp = False
checked_compatibility = False
has_read_db = False
    
def to_any_timestamp(date_obj):
    global checked_utimestamp
    global has_utimestamp

    if not checked_utimestamp:
        check_utimestamp()

    if has_utimestamp:
        from trac.util.datefmt import to_utimestamp
        return to_utimestamp(date_obj)
    else:
        # Trac 0.11
        from trac.util.datefmt import to_timestamp
        return to_timestamp(date_obj)

def from_any_timestamp(ts):
    global checked_utimestamp
    global has_utimestamp

    if not checked_utimestamp:
        check_utimestamp()

    if has_utimestamp:
        from trac.util.datefmt import from_utimestamp
        return from_utimestamp(ts)
    else:
        # Trac 0.11
        from trac.util.datefmt import utc
        return datetime.fromtimestamp(ts, utc)

def get_db(env, db=None):
    raise TracError('get_db function is deprecated!')

def get_db_for_write(env, db=None):
    raise TracError('get_db_for_write function is deprecated!')

def check_utimestamp():
    global checked_utimestamp
    global has_utimestamp

    try:
        from trac.util.datefmt import to_utimestamp, from_utimestamp
        has_utimestamp = True
    except:
        # Trac 0.11
        has_utimestamp = False

    checked_utimestamp = True

def check_compatibility(env):
    global checked_compatibility
    global has_read_db

    try:
        if env.get_read_db():
            has_read_db = True
    except:
        # Trac 0.11
        has_read_db = False

    checked_compatibility = True

def to_list(params=[]):
    result = []
    
    for i in params:
        if isinstance(i, list):
            for v in i:
                result.append(v)
        else:
            result.append(i)
    
    return tuple(result)
  

def get_dictionary_from_string(str):
    result = {}

    sub = str.partition('{')[2].rpartition('}')[0]
    tokens = sub.split(",")

    for tok in tokens:
        name = remove_quotes(tok.partition(':')[0])
        value = remove_quotes(tok.partition(':')[2])
        
        result[name] = value

    return result


def get_string_from_dictionary(dictionary, values=None):
    if values is None:
        values = dictionary
    
    result = '{'
    for i, k in enumerate(dictionary):
        result += "'"+k+"':'"+values[k]+"'"
        if i < len(dictionary)-1:
            result += ","
    
    result += '}'
    
    return result


def remove_quotes(str, quote='\''):
    return str.partition(quote)[2].rpartition(quote)[0]


def compatible_domain_functions(domain, function_name_list):
    return lambda x: x, lambda x: x, lambda x: x, lambda x: x

def get_timestamp_db_type():
    global checked_utimestamp
    global has_utimestamp

    if not checked_utimestamp:
        check_utimestamp()

    if has_utimestamp:
        return 'int64'
    else:
        # Trac 0.11
        return 'int'
    
def upload_file_to_subdir(env, req, subdir, param_name, target_filename):
    upload = param_name
    
    if isinstance(upload, unicode) or not upload.filename:
        raise TracError('You must provide a file.')
    
    txt_filename = upload.filename.replace('\\', '/').replace(':', '/')
    txt_filename = os.path.basename(txt_filename)
    if not txt_filename:
        raise TracError('You must provide a file.')
        
    target_dir = os.path.join(env.path, 'upload', subdir)
    
    if not os.access(target_dir, os.F_OK):
        os.makedirs(target_dir)
        
    target_path = os.path.join(target_dir, target_filename)
    
    try:
        target_file = open(target_path, 'w')
        shutil.copyfileobj(upload.file, target_file)
    finally:
        target_file.close()


def db_insert_or_ignore(env, tablename, propname, value, db=None):
    if db_get_config_property(env, tablename, propname, db) is None:
        db_set_config_property(env, tablename, propname, value, db)

def db_get_config_property(env, tablename, propname, db=None):
    if not db:
        db = env.get_read_db()
        
    cursor = db.cursor()
    
    sql = "SELECT value FROM %s WHERE propname=%%s" % tablename
    row = None
    
    try:
        cursor.execute(sql, (propname,))
        row = cursor.fetchone()
    except:
        pass

    if not row or len(row) == 0:
        return None
        
    return row[0]
        
def db_set_config_property(env, tablename, propname, value, db=None):
    @env.with_transaction(db)
    def do_db_set_config_property(db):
        cursor = db.cursor()

        sql = "SELECT COUNT(*) FROM %s WHERE propname = %%s" % tablename
        cursor.execute(sql, (propname,))

        row = cursor.fetchone()
        if row is not None and int(row[0]) > 0:
            cursor.execute("""
                           UPDATE %s
                               SET value = %%s
                               WHERE propname = %%s 
                           """ % tablename, (str(value), propname))
        else:
            cursor.execute("""
                           INSERT INTO %s (propname,value)
                               VALUES (%%s,%%s)
                           """ % tablename, (propname, str(value)))

    return True

def list_available_tables(dburi, cursor):
    if dburi.startswith('sqlite:'): 
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND NOT name='sqlite_sequence'
            """
    elif dburi.startswith('postgres:'): 
        query = """
            SELECT tablename FROM pg_tables
            WHERE schemaname = ANY (current_schemas(false))
            """
    elif dburi.startswith('mysql:'): 
        query = "SHOW TABLES" 
    else: 
        raise TracError('Unsupported %s database' % dburi.split(':')[0]) 
    cursor.execute(query) 

    return sorted([row[0] for row in cursor]) 

def fix_base_location(req):
    return req.href('/').rstrip('/')


## {{{ http://code.activestate.com/recipes/550804/ (r2)
# The list of symbols that are included by default in the generated
# function's environment
SAFE_SYMBOLS = ["list", "dict", "tuple", "set", "long", "float", "object",
                "bool", "callable", "True", "False", "dir",
                "frozenset", "getattr", "hasattr", "abs", "cmp", "complex",
                "divmod", "id", "pow", "round", "slice", "vars",
                "hash", "hex", "int", "isinstance", "issubclass", "len",
                "map", "filter", "max", "min", "oct", "chr", "ord", "range",
                "reduce", "repr", "str", "type", "zip", "xrange", "None",
                "Exception", "KeyboardInterrupt"]
# Also add the standard exceptions
__bi = __builtins__
if type(__bi) is not dict:
    __bi = __bi.__dict__
for k in __bi:
    if k.endswith("Error") or k.endswith("Warning"):
        SAFE_SYMBOLS.append(k)
del __bi

def createFunctionFromString(sourceCode, args="", additional_symbols=dict()):
  """
  Create a python function from the given source code
  
  \param sourceCode A python string containing the core of the
  function. Might include the return statement (or not), definition of
  local functions, classes, etc. Indentation matters !
  
  \param args The string representing the arguments to put in the function's
  prototype, such as "a, b", or "a=12, b",
  or "a=12, b=dict(akey=42, another=5)"

  \param additional_symbols A dictionary variable name =>
  variable/funcion/object to include in the generated function's
  closure

  The sourceCode will be executed in a restricted environment,
  containing only the python builtins that are harmless (such as map,
  hasattr, etc.). To allow the function to access other modules or
  functions or objects, use the additional_symbols parameter. For
  example, to allow the source code to access the re and sys modules,
  as well as a global function F named afunction in the sourceCode and
  an object OoO named ooo in the sourceCode, specify:
      additional_symbols = dict(re=re, sys=sys, afunction=F, ooo=OoO)

  \return A python function implementing the source code. It can be
  recursive: the (internal) name of the function being defined is:
  __TheFunction__. Its docstring is the initial sourceCode string.

  Tests show that the resulting function does not have any calling
  time overhead (-3% to +3%, probably due to system preemption aleas)
  compared to normal python function calls.
  """
  # Include the sourcecode as the code of a function __TheFunction__:
  s = "def __TheFunction__(%s):\n" % args
  s += "\t" + "\n\t".join(sourceCode.split('\n')) + "\n"

  # Byte-compilation (optional)
  byteCode = compile(s, "<string>", 'exec')  

  # Setup the local and global dictionaries of the execution
  # environment for __TheFunction__
  bis   = dict() # builtins
  globs = dict()
  locs  = dict()

  # Setup a standard-compatible python environment
  bis["locals"]  = lambda: locs
  bis["globals"] = lambda: globs
  globs["__builtins__"] = bis
  globs["__name__"] = "SUBENV"
  globs["__doc__"] = sourceCode

  # Determine how the __builtins__ dictionary should be accessed
  if type(__builtins__) is dict:
    bi_dict = __builtins__
  else:
    bi_dict = __builtins__.__dict__

  # Include the safe symbols
  for k in SAFE_SYMBOLS:
    # try from current locals
    try:
      locs[k] = locals()[k]
      continue
    except KeyError:
      pass
    # Try from globals
    try:
      globs[k] = globals()[k]
      continue
    except KeyError:
      pass
    # Try from builtins
    try:
      bis[k] = bi_dict[k]
    except KeyError:
      # Symbol not available anywhere: silently ignored
      pass

  # Include the symbols added by the caller, in the globals dictionary
  globs.update(additional_symbols)

  # Finally execute the def __TheFunction__ statement:
  eval(byteCode, globs, locs)
  # As a result, the function is defined as the item __TheFunction__
  # in the locals dictionary
  fct = locs["__TheFunction__"]
  # Attach the function to the globals so that it can be recursive
  del locs["__TheFunction__"]
  globs["__TheFunction__"] = fct
  # Attach the actual source code to the docstring
  fct.__doc__ = sourceCode
  return fct
## end of http://code.activestate.com/recipes/550804/ }}}

# Example:
#
# import sys, re
#
# f = createFunction("print a\nprint b", "a=3, b=4", 
#                    additional_symbols = dict(re=re, sys=sys,
#                                              afunction=F, ooo=OoO))
# f()
# f(12)
# f(b=7, a=8)
# f(9, 10)
