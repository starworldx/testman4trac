import xmlrpclib 

#
# Remember to change the following URL with your information!!!
#
# For example: 
#
# trac_project_url = "http://anonymous@localhost:8000/my_test_project/rpc"
#
# trac_project_url = "http://user@yourserver:port/yourproject/rpc"
trac_project_url = "http://anonymous@localhost:8000/test01/rpc"

print ""
print "-------- Connecting to '%s'" % trac_project_url
print ""

server = xmlrpclib.ServerProxy(trac_project_url)


print ">> Creating test catalog"
root_cat = server.testmanager.createTestCatalog('', "Test Root Catalog RPC", "This is a wonderful catalog.")
print root_cat

print ">> Creating sub-catalog"
sub_cat = server.testmanager.createTestCatalog(root_cat, "Test Sub-Catalog RPC", "This is a wonderful sub-catalog.", {'remarks': 'These are the Remarks'})
print sub_cat

print ">> Creating two test cases in the root catalog"
tc_1 = server.testmanager.createTestCase(root_cat, "Test Case 1", "This is a wonderful test case.", {'component': 'Framework'})
print tc_1
tc_2 = server.testmanager.createTestCase(root_cat, "Test Case 2", "This is an even more wonderful test case.", {'testeffort': '1000'})
print tc_2

print ">> Creating two test cases in the sub-catalog"
tc_3 = server.testmanager.createTestCase(sub_cat, "Test Case Sub 3", "This is a wonderful test case.")
print tc_3
tc_4 = server.testmanager.createTestCase(sub_cat, "Test Case Sub 4", "This is an even more wonderful test case.")
print tc_4

print ">> Listing root-level catalogs"
for tc in server.testmanager.listRootCatalogs():
    for v in tc:
        print v

print ">> Listing sub-catalogs of root test catalog"
for tc in server.testmanager.listSubCatalogs(root_cat):
    for v in tc:
        print v

print ">> Listing test cases in root test catalog"
for tc in server.testmanager.listTestCases(root_cat):
    for v in tc:
        print v

print ">> Creating a test plan on the root catalog"
tplan = server.testmanager.createTestPlan(root_cat, "Test Root Plan RPC", {'longdescription': 'This is a veeeeeery long description.'})
print tplan

print ">> Listing test plans available on specified test catalog"
for tp in server.testmanager.listTestPlans(root_cat):
    for v in tp:
        print v

print ">> Listing test cases for root test plan on root test catalog, with their status"
for tc in server.testmanager.listTestCases(root_cat, tplan):
    for v in tc:
        print v

print ">> Getting root test catalog properties"
for v in server.testmanager.getTestCatalog(root_cat):
    print v

print ">> Modifying root test catalog title and description"
print server.testmanager.modifyTestObject('testcatalog', root_cat, {'title': "Test Root Catalog Modified", 'description': "This is no more a wonderful catalog."})

print ">> Verifying root test catalog properties has been changed"
for v in server.testmanager.getTestCatalog(root_cat):
    print v

print ">> Getting first test case properties"
for v in server.testmanager.getTestCase(tc_1):
    print v

print ">> Getting test plan on root catalog properties"
for v in server.testmanager.getTestPlan(tplan, root_cat):
    print v

print ">> Verifying root test catalog properties has been changed"
for v in server.testmanager.getTestCatalog(root_cat):
    print v

#
# These simple functions leverage the base functions to demostrate some more articulated usage.
#

# Recursive function to print a whole sub-plan and its contained test cases
def printSubCatalog(cat_id, indent):
    tcat = server.testmanager.getTestCatalog(cat_id)

    indent_blanks = ''
    for i in range(indent):
        indent_blanks += '    '

    print indent_blanks + tcat[1]

    for subc in server.testmanager.listSubCatalogs(cat_id):
        subc_id = subc[0]
        printSubCatalog(subc_id, indent + 1)

    for tc in server.testmanager.listTestCases(cat_id):
        tc_title = tc[2]
        print indent_blanks + '    ' + tc_title

# Recursive function to print a whole sub-catalog and its contained test cases with status
def printSubPlan(cat_id, plan_id, indent):
    tcat = server.testmanager.getTestCatalog(cat_id)

    indent_blanks = ''
    for i in range(indent):
        indent_blanks += '    '

    print indent_blanks + tcat[1]

    for subc in server.testmanager.listSubCatalogs(cat_id):
        subc_id = subc[0]
        printSubPlan(subc_id, plan_id, indent + 1)

    for tcip in server.testmanager.listTestCases(cat_id, plan_id):
        tc_id = tcip[0]
        tc_status = tcip[2]
        tc = server.testmanager.getTestCase(tc_id)
        tc_title = tc[1]
        print indent_blanks + '    ' + tc_title + ": "+tc_status

# Entry point to print a whole test plan and its contained test cases with status
def printPlan(cat_id, plan_id):
    p = server.testmanager.getTestPlan(plan_id, cat_id)
    
    print p[1]

    printSubPlan(cat_id, plan_id, 0)


# Now, let's use the functions defined above

print ">> Printing complete test catalog tree"
printSubCatalog(root_cat, 0)

print ">> Printing complete test plan tree"
printPlan(root_cat, tplan)

print ">> Setting test case status (note: this actually creates the TestCaseInPlan object into the DB)"
print server.testmanager.setTestCaseStatus(tc_2, tplan, 'successful')

print ">> Printing test case status just set"
for v in server.testmanager.getTestCase(tc_2, tplan):
    print v

print ">> Changing test case status"
print server.testmanager.setTestCaseStatus(tc_2, tplan, 'failed')

print ">> Modifying test case in plan custom field"
print server.testmanager.modifyTestObject('testcaseinplan', tc_2, {'planid': tplan, 'operating_system': "Macosx"})

print ">> Verifying the test case status and custom field have been changed"
for v in server.testmanager.getTestCase(tc_2, tplan):
    print v

print ">> Printing again complete test plan tree, showing modified test case status"
printPlan(root_cat, tplan)
