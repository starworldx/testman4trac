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

var urlAddress = baseurl + "/teststats?content=render";
var chartTabs = null;

function addBookmark() {
	var sel = document.getElementById("dt_frm").testplan;
	var tplan = sel.options[sel.options.selectedIndex].innerHTML;
	
	var title = "Test Case statistics (" + tplan + ") "+ start_date + " - " + end_date; 

	if (window.sidebar) { /* Mozilla Firefox Bookmark */
		window.sidebar.addPanel(title, urlAddress, "");
	} else if (window.external) { 
		if (window.external.AddFavorite) { /* IE Favorite */
			window.external.AddFavorite(urlAddress, title); 
		}
	} else if (window.opera) {
		if (window.print) { /* Opera Hotlist */
			return true; 
		}
	}
}

function labelFormatter(label, series) {
	return '<div style="font-size:8pt; text-align:center; padding:2px; color:black; background-color: #EEEEEE;">' + label + '<br/>' + Math.round(series.percent) + '%</div>';
}

function isDataEmpty(arr) {
	var isEmpty = true;
	for (var i=0; i<arr.length; i++) {
		if (arr[i]['data'] != 0) {
			isEmpty = false;
			break;
		}
	}
	
	return isEmpty;
}

(function($) {
	$(document).ready(function() {
		function updateCharts() {
			var data = [];
			
			/***************** FIRST CHART: Test activity ****************/
			
			$.ajax({
				dataType: "json",
				url: baseurl + "/teststats?content=chartdata"+rqstr(),
				async: false
			}).done(function ( ajaxData ) {
				data = ajaxData;
			});

			var flotBarPlaceholder = $("#flotBarChartId");
			flotBarPlaceholder.unbind();
			
			$.plot(flotBarPlaceholder, data['testActivity'].series, {
				xaxis: {
						ticks: data['testActivity'].xaxis
					},
				yaxis: {
						min: 0
					},
				legend: {
						show: true,
						backgroundColor: "#EEEEEE",
						backgroundOpacity: 0.5,
						container: $("#flotBarChartLegendId")
					}				
				});
			
			/***************** SECOND CHART: Test current status ****************/

			var flotPiePlaceholder = $("#flotPieChartId");
			var flotPieChartEmptyId = $("#flotPieChartEmptyId");
			var flotPiePlaceholderReplacement = $("#flotPieChartReplacementId");
			
			if ($("#testplan").val() == '__all') {
				flotPiePlaceholder.hide();
				flotPieChartEmptyId.hide();
				flotPiePlaceholderReplacement.show();
			} else {
				flotPiePlaceholderReplacement.hide();
				
				if (isDataEmpty(data['testStatus'].series)) {
					flotPiePlaceholder.hide();
					flotPieChartEmptyId.show();
				} else {
					flotPiePlaceholder.show();
					flotPieChartEmptyId.hide();
					
					flotPiePlaceholder.unbind();
				
					$.plot(flotPiePlaceholder, data['testStatus'].series, {
						series: {
								pie: { 
									show: true,
									radius: 1,
									label: {
										show: true,
										radius: 1,
										formatter: labelFormatter,
										background: {
											color: "#EEEEEE",
											opacity: 0.8
										}
									}
								}							
							},
						legend: {
								show: true,
								backgroundColor: "#EEEEEE",
								backgroundOpacity: 0.5,
								container: $("#flotPieChartLegendId")
							}						
					});
				}
			}

			/***************** THIRD CHART: Tickets against plans ****************/
			
			var flotTicketPlaceholder = $("#flotTicketChartId");
			flotTicketPlaceholder.unbind();
			
			$.plot(flotTicketPlaceholder, data['ticketsTrend'].series, {
				xaxis: {
						ticks: data['ticketsTrend'].xaxis
					},
				yaxis: {
						min: 0
					},
				legend: {
						show: true,
						backgroundColor: "#EEEEEE",
						backgroundOpacity: 0.5,
						container: $("#flotTicketChartLegendId")
					}
				});
		}
		
		$("#updateChartButtonId").click(function () {
			setProvided();
			updateCharts();
			updateStaticURL();
		});

		function rqstr() {
			
			return  "&start_date=" + $("#start_date").val() + 
				"&end_date=" + $("#end_date").val() +
				"&resolution=" + $("#resolution").val() +
				"&testplan=" + $("#testplan").val();
		}

		function updateStaticURL(){
			urlAddress = baseurl + "/teststats?content=render" + rqstr();
			
			$("#static_url").html(urlAddress);
			$("#export_excel").attr("href", baseurl + "/teststats?content=downloadcsv" + rqstr());
		}

		function setProvided(res, mile){
			if (!res) {
				res = resolution;
			}
			
			$("#resolution").selectedIndex = {1:0, 7:1, 14:2, 30:3, 60:4, 90:5, 180:6, 360:7}[res];
		}

		setProvided();
		updateCharts();
		updateStaticURL();
		
		chartTabs = $('#tabs').tabs(
			{
				select: function(event, ui) {
					switch (ui.index) {
						case 0:
							$('#period_container').show();
							$('#bookmark_container').show();
							break;
						case 1:
							$('#period_container').hide();
							$('#bookmark_container').hide();
							break;
						case 2:
							$('#period_container').show();
							$('#bookmark_container').hide();
							break;
					}
			   }
			}
		);
		
	});
})(jQuery_testmanager);	
