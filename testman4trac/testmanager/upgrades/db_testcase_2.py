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

from testmanager.model import TestManagerModelProvider

def do_upgrade(env, ver, db_backend, db):
    """
    Add 'exec_order' column to testcase table
    """
    cursor = db.cursor()
    
    realm = 'testcase'
    cursor.execute("CREATE TEMPORARY TABLE %(realm)s_old AS SELECT * FROM %(realm)s" % {'realm': realm})
    cursor.execute("DROP TABLE %(realm)s" % {'realm': realm})

    table_metadata = TestManagerModelProvider(env).get_data_models()[realm]['table']

    env.log.info("Updating table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    cursor = db.cursor()

    cursor.execute("INSERT INTO %(realm)s (id,page_name,exec_order) "
                   "SELECT id,page_name,0 FROM %(realm)s_old" % {'realm': realm})
    cursor.execute("DROP TABLE %(realm)s_old" % {'realm': realm})

