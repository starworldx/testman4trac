/* -*- coding: utf-8 -*-
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
*/

/******************************************************/
/**         Test case, catalog, plan creation         */
/******************************************************/

(function($) {
		$(function() {

            $( "#createTestCatalogForm" ).submit(function( event ) {
                var form = $(this);
                var testCatalogName = $("input[name='title']", form).val();
                
                if (testCatalogName == null || testCatalogName.length < 4) {
                    $('#catErrorMsgSpan').html(_("You must specify a name. Minimum length is 4 characters."));
                    event.preventDefault();
                } else {
                    $('#catErrorMsgSpan').html('');
                }

                return;
            });


            $( "#createTestCaseForm" ).submit(function( event ) {
                var form = $(this);
                var testCaseName = $("input[name='title']", form).val();
                
                if (testCaseName == null || testCaseName.length < 4) {
                    $('#errorMsgSpan').html(_("You must specify a name. Minimum length is 4 characters."));
                    event.preventDefault();
                } else {
                    $('#errorMsgSpan').html('');
                }

                return;
            });


            $( "#createTestPlanForm" ).submit(function( event ) {
                var form = $(this);
                
                if ($("input[name='mustSubmit']", form).val() === 'false') {
                    var testPlanName = $("input[name='title']", form).val();

                    if (testPlanName == null || testPlanName.length < 4) {
                        $('#errorMsgSpan2').html(_("You must specify a name. Minimum length is 4 characters."));
                    } else {
                        $('#errorMsgSpan2').html('');

                        $("#dialog_testplan").dialog({width: 640, height: 430, modal: true});
                    }

                    event.preventDefault();
                }
                    
                return;
            });
		});
})(jQuery_testmanager);

function createTestPlanConfirm(catName) {
    var testPlanName = $('#createTestPlanForm').find('input[name="title"]').val();
    var testplanContainsAll = "true";
    var testplanSnapshot = "false";

    /*
	The following should work... but doesn't in case one has first selected some test cases from the tree.
    var testplanContainsAll = $("input[name='testplan_contains_all']:checked").val();
    var testplanSnapshot = $("input[name=testplan_snapshot]:checked").val();
	*/

    var nodes = $("input[name='testplan_contains_all']:checked");
    for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];
        if (node.name == 'testplan_contains_all') {
            testplanContainsAll = node.value;
        }
    }

    nodes = $("input[name='testplan_snapshot']:checked");
    for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];
        if (node.name == 'testplan_snapshot') {
            testplanSnapshot = node.value;
        }
    }

    var selectedTestCases = "";
    if (testplanContainsAll == 'false') {
        selectedTestCases = getSelectedTestCases();
    }

    var form = $('#createTestPlanForm');

    $("input[name='containsAll']", form).val(testplanContainsAll);
    $("input[name='snapshot']", form).val(testplanSnapshot);
    $("input[name='selectedTCs']", form).val(selectedTestCases);

    $("input[name='mustSubmit']", form).val('true');
    $('#createTestPlanForm').submit();
}

function createTestPlanCancel() {
	(function($) {
        $(function() {
            $("#dialog_testplan").dialog('close');
        });
    })(jQuery_testmanager);	
}

function addTestCaseToTestplanDialog() {
	(function($) {
		$(function() {
			$("#dialog_select_testplan").dialog({width: 640, height: 430, modal: true});
		});
	})(jQuery_testmanager);	
}

function addTestCaseToPlan(tcId, tcatId) {
	(function($) {
		$(function() {
			var planids = $("input[name='selected_planid']:checked");
			
			if (planids && planids.length > 0) {
				var planIdList = "";
				
				for (var i=0; i<planids.length; i++) {
					planIdList += $(planids[i]).val();
					if (i < planids.length - 1) {
						planIdList += ",";
					}
				}

				var url = baseLocation+"/testcreate?type=testcaseinplan&tcatId="+tcatId+"&tcId="+tcId+"&planid="+planIdList;
				window.location = url;
			}
		});
	})(jQuery_testmanager);	
}

function addTestCaseToPlanCancel() {
	(function($) {
        $(function() {
            $("#dialog_select_testplan").dialog('close');
        });
    })(jQuery_testmanager);	
}

function duplicateTestCase(tcName, catName) { 
	var url = baseLocation+'/testcreate?type=testcase&duplicate=true&tcId='+tcName+'&path='+catName; 
	window.location = url;
}

function updateTestCase(tcName, planId) {
    var url = baseLocation+"/testcreate?type=testplan&update=true&tcId="+tcName+"&planid="+planId;
    window.location = url;
}

function removeTestCase(tcName, planId) {
    if (confirm(_("Are you sure you want to remove the test case from the plan?"))) {
		var url = baseLocation+"/testdelete?type=testcaseinplan&tcId="+tcName+"&planid="+planId;
		window.location = url;
	}
}

function creaTicket(tcName, planId, planName, summary) {
    var fullSummary = "";
    
    switch(ticketSummaryOption) {
        case 'empty':
            break;

        case 'fixed_text':
            fullSummary = ticketSummaryText + ticketSummarySeparator;
            break;

        case 'last_n_catalogs':
        case 'full_path':
        default:
            var tokens = $('span[name=breadcrumb]').map(function() { return this.innerHTML; }).get();

            var start = 1;
            
            if (ticketSummaryOption == 'last_n_catalogs' && ticketSummaryNumCatalogs < tokens.length) {
                start = tokens.length - ticketSummaryNumCatalogs + 1;
            }
            
            for (var i=start; i<tokens.length; i++) {
                fullSummary += tokens[i] + ticketSummarySeparator;
            }
        
            fullSummary += summary + ticketSummarySeparator;
    }

    fullSummary += _("[Insert problem summary]");

	var url = baseLocation+'/newticket?testcaseid='+tcName+'&planid='+planId+'&planname='+planName+'&summary='+stripLessSpecialChars(fullSummary)+'&description=Test%20Case:%20[wiki:'+tcName+'?planid='+planId+'],%20Test%20Plan:%20'+planName+'%20('+planId+')'; 
	window.location = url;
}

function showTickets(tcName, planId, planName){ 
	var url = baseLocation+'/query?testcaseid=~'+tcName+'&planid='+planId; 
	window.location = url;
}

function duplicateTestCatalog(catName){
    if (confirm(_("Are you sure you want to duplicate the test catalog and all its contained test cases?"))) {
        var url = baseLocation+'/testcreate?type=catalog&duplicate=true&path='+catName; 
        window.location = url;
    }
}

function deleteTestPlan(url){
    if (confirm(_("Are you sure you want to delete the test plan and the state of all its contained test cases?"))) {
        window.location = url;
    }
}

function cloneTestPlan(catId, planId){
	(function($) {
		$(function() {
			$("#dialog_clone_testplan").dialog({width: 500, height: 300, modal: true});
		});
	})(jQuery_testmanager);	
}

function cloneTestPlanConfirm(planId) {
	(function($) {
		$(function() {
            var newPlanNameInput = document.getElementById('new_cloned_testplan_name');
            var testPlanName = newPlanNameInput.value; 
            var tplanName = stripLessSpecialChars(testPlanName); 

            var url = baseLocation+"/testclone?type=testplan&planId="+planId+"&newName="+tplanName;
            window.location = url;
		});
	})(jQuery_testmanager);	
}

function cloneTestPlanCancel() {
	(function($) {
        $(function() {
            $("#dialog_clone_testplan").dialog('close');
        });
    })(jQuery_testmanager);	
}

/******************************************************/
/**    Move or copy test case into another catalog    */
/******************************************************/

function checkMoveTCDisplays() {
    displayNode('copiedTCMessage', isPasteEnabled());
    displayNode('pasteTCHereMessage', isPasteEnabled());
    displayNode('pasteTCHereButton', isPasteEnabled(), 'inline');

    displayNode('copiedMultipleTCsMessage', isMultiplePasteEnabled());
    displayNode('pasteMultipleTCsHereMessage', isMultiplePasteEnabled());
    displayNode('pasteMultipleTCsHereButton', isMultiplePasteEnabled(), 'inline');
}

function isPasteEnabled() {
    if (getCookie('TestManager_TestCase')) {
        return true;
    }
    
    return false;
}

function isMultiplePasteEnabled() {
    if (getCookie('TestManager_MultipleTestCases')) {
        return true;
    }
    
    return false;
}

function showSelectionCheckboxes(id) {
	/* toggleAll(true); */

    var nodes=null;
    if (document.getElementById("ticketContainer") !== null) {
        nodes=document.getElementById("ticketContainer").getElementsByTagName('input');
    }
    
    if (document.getElementById("testcaseList") !== null) {
        nodes=document.getElementById("testcaseList").getElementsByTagName('input');
    }

	for (var i=0;i<nodes.length;i++) {
		var el=nodes.item(i);
		
		if (el.getAttribute("name") && el.getAttribute("name") == "select_tc_checkbox") {
			el.style.display = "block";
		}
	}
}

function copyTestCaseToClipboard(tcId) {
    setCookie('TestManager_TestCase', tcId, 1, '/', '', '');
    setTimeout('window.location="'+window.location+'"', 100);
}

function copyMultipleTestCasesToClipboard() {
	var selectedTestCases = getSelectedTestCases();

    setCookie('TestManager_MultipleTestCases', selectedTestCases, 1, '/', '', '');
    setTimeout('window.location="'+window.location+'"', 100);
}

function getSelectedTestCases() {
	var selectedTestCases = "";
	var nodes;

	if (document.getElementById("ticketContainer") !== null) {
	    nodes=document.getElementById("ticketContainer").getElementsByTagName('input');
	}
	if (document.getElementById("testcaseList") !== null) {
	    nodes=document.getElementById("testcaseList").getElementsByTagName('input');
	}
	
	for (var i=0;i<nodes.length;i++) {
		var el=nodes.item(i);
		
		if (el.getAttribute("name") && el.getAttribute("name") == "select_tc_checkbox") {
			if (el.checked) {
				selectedTestCases += el.value + ',';
			}
		}
	}

    return selectedTestCases;
}

function pasteTestCaseIntoCatalog(catName) {
    var tcId = getCookie('TestManager_TestCase');
    
    if (tcId != null) {
        deleteCookie('TestManager_TestCase', '/', '');
        var url = baseLocation+"/testcreate?type=testcase&paste=true&path="+catName+"&tcId="+tcId;
        window.location = url;
    }
}

function pasteMultipleTestCasesIntoCatalog(catName) {
    var tcIds = getCookie('TestManager_MultipleTestCases');
    
    if (tcIds != null) {
        deleteCookie('TestManager_MultipleTestCases', '/', '');
        var url = baseLocation+"/testcreate?type=testcase&paste=true&multiple=true&path="+catName+"&tcId="+tcIds;
        window.location = url;
    }
}

function cancelTCMove() {
    deleteCookie('TestManager_TestCase', '/', '');
    setTimeout('window.location="'+window.location+'"', 100);
}

function cancelTCsCopy() {
    deleteCookie('TestManager_MultipleTestCases', '/', '');
    setTimeout('window.location="'+window.location+'"', 100);
}

/******************************************************/
/**         Import and export Test Cases              */
/******************************************************/

function importTestCasesIntoCatalog(catName) {
	(function($) {
        $(function() {
            $("#dialog_import").dialog({width: 640, height: 430, modal: true});
        });
    })(jQuery_testmanager);	
}

function importTestCasesCancel() {
	(function($) {
        $(function() {
            $("#dialog_import").dialog('close');
        });
    })(jQuery_testmanager);	
}

function exportTestCasesFromCatalog(catName) {
	(function($) {
        $(function() {
            $("#dialog_export").dialog({width: 640, height: 300, modal: true});
        });
    })(jQuery_testmanager);	
}

function exportTestCasesCancel() {
	(function($) {
        $(function() {
            $("#dialog_export").dialog('close');
        });
    })(jQuery_testmanager);	
}

/******************************************************/
/**                 Tree view widget                  */
/******************************************************/

/** Configuration property to specify whether non-matching search results should be hidden. */ 
var selectHide = true;
/** Configuration property to specify whether matching search results should be displayed in bold font. */
var selectBold = true;

var selectData = {};
var deselectData = {};
var htimer = null;
var searchResults = 0;

function toggleAll(tableId, isexpand) {
    var nodes=document.getElementById(tableId).getElementsByTagName("span");
    for(var i=0;i<nodes.length;i++) {
        if(nodes.item(i).getAttribute("name") === "toggable") {
            if (isexpand) {
                expand(nodes.item(i).id);
            } else {
                collapse(nodes.item(i).id);
            }
        }
    }
}

function collapse(id) {
    el = document.getElementById(id);
    if (el.getAttribute("name") === "toggable") {
        el.firstChild['expanded'] = false;
        el.firstChild.innerHTML = '<img class="iconElement" src="'+baseLocation+'/chrome/testmanager/images/plus.png" />';
        document.getElementById(el.id+"_list").style.display = "none";
    }
}

function expand(id) {
    el = document.getElementById(id);
    if (el.getAttribute("name") === "toggable") {
        el.firstChild['expanded'] = true;
        el.firstChild.innerHTML = '<img class="iconElement" src="'+baseLocation+'/chrome/testmanager/images/minus.png" />';
        document.getElementById(el.id+"_list").style.display = "";
    }
}

function toggle(id) {
    var el=document.getElementById(id);
    if (el.firstChild['expanded']) {
        collapse(id);
    } else {
        expand(id);
    }
}

function highlight(tableId, str) {
    clearSelection(tableId);
    if (str && str !== "") {
        var res=[];
        var tks=str.split(" ");
        for (var i=0;i<tks.length;i++) {
            res[res.length]=new RegExp(regexpescape(tks[i].toLowerCase()), "g");
        }
        var nodes=document.getElementById(tableId).getElementsByTagName("a");
        for(var i=0;i<nodes.length;i++) {
            var n=nodes.item(i);
            if (n.nextSibling) {
                if (filterMatch(n, n.nextSibling, res)) {
                    select(tableId, n);
                } else {
                    deselect(tableId, n);
                }
            }
        }

        document.getElementById(tableId+'_searchResultsNumberId').innerHTML = _("Results: ")+searchResults;
    }
}

function regexpescape(text) {
    return text.replace(/[-[\]{}()+?.,\\\\^$|#\s]/g, "\\\\$&").replace(/\*/g,".*");
}

function filterMatch(node1,node2,res) {
    var name=(node1.innerText + ' ' + (node2 ? (node2.innerText ? node2.innerText : node2.textContent) : '')).toLowerCase();
    var match=true;
    for (var i=0;i<res.length;i++) {
        match=match && name.match(res[i]);
    } 
    return match;
}

function clearSelection(tableId) {
    toggleAll(tableId, false);
    
    if (tableId in selectData) {
        for (var i=0;i<selectData[tableId].length;i++) {
            selectData[tableId][i].style.fontWeight="normal";
            selectData[tableId][i].style.display="";
        };
    }
    
    selectData[tableId]=[];
    
    if (tableId in deselectData) {
	    for (var i=0;i<deselectData[tableId].length;i++) {
	        if (selectHide) {
	            deselectData[tableId][i].style.display="";
	        }
	    };
    }
    
    deselectData[tableId]=[];
    searchResults = 0;
    
    document.getElementById(tableId+"_searchResultsNumberId").innerHTML = '';
}

function select(tableId, node) {
    searchResults++;

    do {
        if(node.tagName ==="UL" && node.id.indexOf("b_") === 0) {
            expand(node.id.substr(0,node.id.indexOf("_list")));
        };

        if(node.tagName === "LI") {
            if (selectBold) {
                node.style.fontWeight = "bold";
            };
            
            if (selectHide) {
                node.style.display = "block";
            };
            
            selectData[tableId][selectData[tableId].length]=node;
        };
        node=node.parentNode;
    } while (node.id!==tableId);
}

function deselect(tableId, node) {
    do {
        if (node.tagName === "LI") {
            if (selectHide && node.style.display==="") {
                node.style.display = "none";
                deselectData[tableId][deselectData[tableId].length]=node;
            }
        };
        
        node=node.parentNode;
    } while (node.id!==tableId);
}

function starthighlight(tableId, str,now) {
    if (htimer) {
        clearTimeout(htimer);
    } 
    if (now) {
        highlight(tableId, str);
    } else {
        htimer = setTimeout(function() {
                                highlight(tableId, str);
                            },500);
    }
}

function checkFilter(tableId, now) {
    var f=document.getElementById("tcFilter");
    if (f) {
    	var rootEl = document.getElementById(tableId);
        if (rootEl !== null) {
        	if (rootEl.tagName.toLowerCase() == "div") {
        		starthighlight(f.value,now);
        	} else {
                starthighlightTable(f.value,now);
        	}
        }
    }
}

function underlineLink(id) {
    el = document.getElementById(id);
    el.style.backgroundColor = '#EEEEEE';
    el.style.color = '#BB0000';
    el.style.textDecoration = 'underline';
}

function removeUnderlineLink(id) {
    el = document.getElementById(id);
    el.style.backgroundColor = 'white';
    el.style.color = 'black';
    el.style.textDecoration = 'none';
}

/******************************************************/
/**                 Tree table widget                 */
/******************************************************/

function starthighlightTable(tableId, str,now) {
    if (htimer) {
        clearTimeout(htimer);
    } 
    if (now) {
        highlightTable(tableId, str);
    } else {
        htimer = setTimeout(function() {
                                highlightTable(tableId, str);
                            },500);
    }
}

function highlightTable(tableId, str) {
    clearSelectionTable(tableId);
    if (str && str !== "") {
        var res=[];
        var tks=str.split(" ");
        for (var i=0;i<tks.length;i++) {
            res[res.length]=new RegExp(regexpescape(tks[i].toLowerCase()), "g");
        }
        var nodes=document.getElementById(tableId).getElementsByTagName("tr");
        for(var i=0;i<nodes.length;i++) {
            var n=nodes.item(i);
            if (filterMatchTable(n, res)) {
                selectRow(tableId, n);
            } else {
                deselectRow(tableId, n);
            }
        }

        document.getElementById(tableId+'_searchResultsNumberId').innerHTML = _("Results: ")+searchResults;
    }
}

function filterMatchTable(node, res) {
    var name = "";
    
    while (node.tagName !== "TR") {
        node = node.parentNode;
    }
    
    if (node.getAttribute("name") === "testcatalog") {
        return false;
    }
    
    node = node.firstChild;
    while (node != null) {
        if (node.tagName === "TD") {
            name += ' ' + (node.innerText ? node.innerText : node.textContent);
        }
        
        node = node.nextSibling;
    }
    
    name = name.toLowerCase();

    var match=true;
    for (var i=0;i<res.length;i++) {
        match=match && name.match(res[i]);
    }
    
    return match;
}

function clearSelectionTable(tableId) {
	if (tableId in selectData) {
	    for (var i=0;i<selectData[tableId].length;i++) {
	        selectData[tableId][i].className="";
	    };
	}
    
    selectData[tableId]=[];
    
	if (tableId in deselectData) {
	    for (var i=0;i<deselectData[tableId].length;i++) {
	        deselectData[tableId][i].className="";
	    };
	}
	
    deselectData[tableId]=[];
    searchResults = 0;
    
    document.getElementById(tableId+"_searchResultsNumberId").innerHTML = '';
}

function selectRow(tableId, node) {
    searchResults++;

    while (node.tagName !== "TR") {
        node = node.parentNode;
    }

    node.className = "rowSelected";

    selectData[tableId][selectData[tableId].length]=node;
}

function deselectRow(tableId, node) {
    while (node.tagName !== "TR") {
        node = node.parentNode;
    }

    node.className = "rowHidden";
    
    deselectData[tableId][deselectData[tableId].length]=node;
}

function showPencil(id) {
    $('#'+id).show();
}

function hidePencil(id) {
    $('#'+id).hide();
}

/******************************************************/
/**        Test case in plan status management        */
/******************************************************/

function changestate(tc, planid, path, newStatus, newStatusColor, newLabel) {

    var url = baseLocation+"/teststatusupdate";
    
    var params = {id: tc, planid: planid, status: newStatus, path: path};
    
    result = doAjaxCall(url, "GET", params);

    /* Handle errors in the Ajax call */
    if (result == 'OK') {
        oldIconSpan = document.getElementById("tcStatus"+currStatusColor);
        oldIconSpan.style.border="";
        
        newIconSpan = document.getElementById("tcStatus"+newStatusColor);
        newIconSpan.style.border="2px solid black";
        
        displayNode("tcTitleStatusIcon"+currStatusColor, false);
		
        $("#tcTitleStatusIcon"+newStatusColor).prop('title', newLabel);
        displayNode("tcTitleStatusIcon"+newStatusColor, true);
		
        currStatus = newStatus;
        currStatusColor = newStatusColor;
    } else {
        (function($) {
            $(function() {
                $("#dialog_error").dialog({width: 320, height: 150, modal: true});
            });
        })(jQuery_testmanager);	
    }
}

function changestateOnPlan(imgNode, tc, planid, newStatus, newStatusColor, newLabel) {
    var url = baseLocation+"/teststatusupdate";

    var params = {id: tc, planid: planid, status: newStatus};

    result = doAjaxCall(url, "GET", params);
    
    /*
	Handle errors in the Ajax call
	*/
    if (result == 'OK') {
        $(imgNode).attr('title', newLabel);
        $(imgNode).attr('src', '../chrome/testmanager/images/'+newStatusColor+'.png');
    } else {
        (function($) {
            $(function() {
                $("#dialog_error").dialog({width: 320, height: 150, modal: true});
            });
        })(jQuery_testmanager);	
    }
}

function bindTCStatusMenus() {
    if (buildStatusChangeMenu) {
        (function($) {
            $(function() {
                $(".statusMenuAnchor").bind('click', function(event) {
                    event.stopPropagation();
                
					var $target = $(event.target);
					
					var imgNode = $(this).find("img");
					
                    var params = $(this).attr("name").split(",");
					var tcid = params[0];
					var planid = params[1];
					var path = params[2];
					var oldStatus = params[3];
					var oldColor = params[4];
					var oldLabel = params[5];
					
					var newMenu = $("#statusmenuContainer").clone();
					newMenu.attr("id", "statusmenuContainer_"+tcid);
					newMenu.appendTo($(this));
					
					$("#statusmenuContainer_"+tcid).show();
					$("#statusmenuContainer_"+tcid+" > ul").menu({
						select: function( event, ui ) {
								event.stopPropagation();
								
								var currItemName = ui.item.attr("name");
								if (currItemName != null && currItemName.length > 0) {
									var newParams = currItemName.split("|");
									var newStatus = newParams[0];
									var newColor = newParams[1];
									var newLabel = newParams[2];

									changestateOnPlan(imgNode, tcid, planid, newStatus, newColor, newLabel);
									
									$("#statusmenuContainer_"+tcid+" > ul").menu("destroy");
									$("#statusmenuContainer_"+tcid).remove();
								}
							}
					}).popup();
					
					$("#statusmenuContainer_"+tcid+" > ul").css({display: "inline-block"});
					
					/* To close the menu when clicking outside of it */
					$(document).on(
							"click.statusmenuContainer_"+tcid,     /* provide a namespace for the 'click' event handler */
							":not(#statusmenuContainer_"+tcid+")",
							function(){
								$("#statusmenuContainer_"+tcid).hide();
								/* Remove this event handler */
								$(document).off("click.statusmenuContainer_"+tcid);
							}
						);
					
				});
				
                $(".statusSingleMenuAnchor").bind('click', function(event) {
                    event.stopPropagation();
                
					var target = $(event.target);
					
                    var params = $(this).attr("name").split(",");
					var color = params[0];
					var tcid = params[1];
					var planid = params[2];
					var path = params[3];
					var oldStatus = params[4];
					var oldColor = params[5];
					var oldLabel = params[6];
					
					$("#statusSingleMenu_"+color).show();
					$("#statusSingleMenu_"+color+" > ul").menu({
						select: function( event, ui ) {
								event.stopPropagation();
								
								var currItemName = ui.item.attr("name");
								if (currItemName != null && currItemName.length > 0) {
									var newParams = currItemName.split("|");
									var newStatus = newParams[0];
									var newColor = newParams[1];
									var newLabel = newParams[2];

									changestate(tcid, planid, path, newStatus, newColor, newLabel);
									
									$("#statusSingleMenu_"+color).hide();
								}
							}
					}).popup();
					
					$("#statusSingleMenu_"+color+" > ul").css({display: "inline-block"});
					
					/* To close the menu when clicking outside of it */
					$(document).on(
							"click.statusSingleMenu_"+color,     /* provide a namespace for the 'click' event handler */
							":not(#statusSingleMenu_"+color+")",
							function(){
								$("#statusSingleMenu_"+color).hide();
								/* Remove this event handler */
								$(document).off("click.statusSingleMenu_"+color);
							}
						);
						
				});
				
			});
        })(jQuery_testmanager);	
    }
}

/******************************************************/
/**                Draggable test cases               */
/******************************************************/

/*
 * TODO:
 * 1) Supportare il drag di interi cataloghi
 * 2) Supportare la copia di test case con Ctrl
 */

function organizeTestCatalog(catName) {
	(function($) {
        $(function() {
            $("#dialog_organize").dialog({width: 900, height: 500, modal: true});

			$('#testcaseOrganizeList').nestedSortable({
				handle: 'div',
				listType: 'ul',
				items: 'li',
				protectRoot: false,
				rootID: 'testcaseOrganizeList',
				toleranceElement: '> div',
				isAllowed: canDropItem
			});

			$("#testcaseOrganizeList").sortableTree();

        });
    })(jQuery_testmanager);	
}

function organizeCatalogCancel() {
	(function($) {
        $(function() {
            $("#dialog_organize").dialog('close');
        });
    })(jQuery_testmanager);	
}

function canDropItem(item, parent) {

	if (item.attr('name') == 'testcase' && (parent == null || parent.attr('name') == 'testcatalog')) {
		return true;
	}
	
	return false; 
}

function postCatalogOrganization() {
	(function($) {
		var hiered = JSON.stringify($('#testcaseOrganizeList').nestedSortable('toHierarchy', {startDepthCount: 0}));
		
		$("div [name=test_list]").val(hiered);
		
		document.organize_form_id.submit();
		
    })(jQuery_testmanager);	
}

function dump(arr,level) {
	var dumped_text = "";
	if(!level) level = 0;

	/*
	The padding given at the beginning of the line.
	*/
	var level_padding = "";
	for(var j=0;j<level+1;j++) level_padding += "    ";

	if(typeof(arr) == 'object') { /* Array/Hashes/Objects */
		for(var item in arr) {
			var value = arr[item];

			if(typeof(value) == 'object') { /* If it is an array, */
				dumped_text += level_padding + "'" + item + "' ...\n";
				dumped_text += dump(value,level+1);
			} else {
				dumped_text += level_padding + "'" + item + "' => \"" + value + "\"\n";
			}
		}
	} else { /* Strings/Chars/Numbers etc. */
		dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
	}
	return dumped_text;
}

/******************************************************/
/**                  Utility functions                */
/******************************************************/

function expandCollapseSection(nodeId) {
    /* In Trac 0.12 should do nothing, because a listener is
     * already in charge of handling sections */
}

function stripSpecialChars(str) {
    result = str.replace(/[ ',;:àèéìòù£§<>!"%&=@#\[\]\-\\\\^\$\.\|\?\*\+\(\)\{\}]/g, '');
    return result;
}

function stripLessSpecialChars(str) {
    result = str.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/[;#&\?]/g, '');
    return result;
}

function displayNode(id, show, mode) {
    if (show) {
        $('#'+id).show();
    } else {
        $('#'+id).hide();
    }
}

function displayNodes(name, show, mode) {
    if (show) {
        $("[name='"+name+"']").show();
    } else {
        $("[name='"+name+"']").hide();
    }
}

function doAjaxCall(url, method, params) {
	var responseText = "ERROR";

    try {
		headers = {};
        if (method == "POST") {
            headers = {"Content-type": "application/x-www-form-urlencoded"};
            params["__FORM_TOKEN"] = getCookie('trac_form_token');
        }

        $.ajax({
          async: false,
          type: method,
          url: url,
          data: params,
          dataType: "text",
          headers: headers,
          success: function(data) {
              responseText = data;
            },
          error: function() {
              responseText = 'ERROR';
			}
        });
        
    } catch (e) {
        responseText = 'ERROR';
    }
	
    return responseText;
}

var editingFields = {};

function showEditingPencil(name) {
    if (!editingFields[name]) {
        showPencil("field_pencilIcon"+name);
    }
}

function editField(name, type) {
    displayNode('custom_field_value_'+name, false);
    displayNode('container_custom_field_'+name, true);
    displayNode('update_button_'+name, true);
    editingFields[name] = true;
    hidePencil("field_pencilIcon"+name);
}

function sendUpdate(realm, name, type) {
   	var objKeyField = document.getElementById("obj_key_field");
    var objKey = objKeyField.value;

   	var objPropsField = document.getElementById("obj_props_field");
    var objProps = objPropsField.value;

    var value = null;
    if (type == 'radio') {
        value = $("input:radio[name='custom_field_"+name+"']:checked").val();
    } else if (type == 'checkbox') {
        value = $('#custom_field_'+name).checked() ? '1' : '0';
    } else {
        value = $('#custom_field_'+name).val();
    }

    var url = baseLocation+"/propertyupdate";

    /*
     * var params = {realm: realm, key: objKey, props: objProps, name: name, value: encodeURIComponent(value)};
     */
    var params = {realm: realm, key: objKey, props: objProps, name: name, value: value};
    
    result = doAjaxCall(url, "GET", params);

    /*
	Handle result of the Ajax call
	*/
    if (result == 'OK') {
        if (type == 'textarea') {
            value = replaceAll('\n\r', '<br />', value);
            value = replaceAll('\n', '<br />', value);
        }
        
        $("#custom_field_value_"+name).html(value);

        displayNode('custom_field_value_'+name, true);
        displayNode('container_custom_field_'+name, false);
        displayNode('update_button_'+name, false);
        delete editingFields[name];

    } else {
        (function($) {
            $(function() {
                $("#dialog_error").dialog({width: 320, height: 150, modal: true});
            });
        })(jQuery_testmanager);	
    }
}

function getLocale() {
	if ( navigator ) {
		if ( navigator.language ) {
			return navigator.language;
		}
		else if ( navigator.browserLanguage ) {
			return navigator.browserLanguage;
		}
		else if ( navigator.systemLanguage ) {
			return navigator.systemLanguage;
		}
		else if ( navigator.userLanguage ) {
			return navigator.userLanguage;
		}
	}
}

function include(filename) {
	var head = document.getElementsByTagName('head')[0];
	
	script = document.createElement('script');
	script.src = filename;
	script.type = 'text/javascript';
	
	head.appendChild(script);
}

function loadMessageCatalog() {
	var lc = getLocale();
	include('../chrome/testmanager/js/' + lc + '.js');
}

function escapeRegExp(str) {
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function replaceAll(find, replace, str) {
  return str.replace(new RegExp(escapeRegExp(find), 'g'), replace);
}

/**
 * Adds the specified function, by name or by pointer, to the window.onload() queue.
 * 
 * Usage:
 *
 * addLoadHandler(nameOfSomeFunctionToRunOnPageLoad); 
 *
 * addLoadHandler(function() { 
 *   <more code to run on page load>
 * }); 
 */
function addLoadHandler(func) { 
    var oldonload = window.onload; 
    if (typeof window.onload != 'function') { 
        window.onload = func; 
    } else { 
        window.onload = function() { 
            if (oldonload) { 
                oldonload(); 
            } 
            func(); 
        };
    } 
}

/**
 * Do some checks as soon as the page is loaded.
 */
addLoadHandler(function() {
        checkFilter(true);
        checkMoveTCDisplays();
        bindTCStatusMenus();
		/* loadMessageCatalog(); */
    });
