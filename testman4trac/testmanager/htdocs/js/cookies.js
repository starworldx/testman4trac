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

/**
 * Returns the value of the specified cookie, or null if the cookie is not found or has no value.
 */
function getCookie( name ) {
	var allCookies = document.cookie.split( ';' );
	var tempCookie = '';
	var cookieName = '';
	var cookieValue = '';
	var found = false;
	var i = '';
	
	for ( i = 0; i < allCookies.length; i++ ) {
		/* split name=value pairs */
		tempCookie = allCookies[i].split( '=' );
		
		
		/* trim whitespace */
		cookieName = tempCookie[0].replace(/^\s+|\s+$/g, '');
	
		if ( cookieName == name ) {
			found = true;
			/* handle case where cookie has no value (i.e. no equal sign)  */
			if ( tempCookie.length > 1 ) {
				cookieValue = unescape( tempCookie[1].replace(/^\s+|\s+$/g, '') );
			}
            
			return cookieValue;
			break;
		}
		tempCookie = null;
		cookieName = '';
	}
    
	if ( !found ) {
		return null;
	}
}

/**
 * Sets a cookie with the input name and value.
 * These are the only required parameters.
 * The expires parameter must be expressed in hours.
 * Generally you don't need to worry about domain, path or secure for most applications.
 * In these cases, do not pass null values, but empty strings.
 */
function setCookie( name, value, expires, path, domain, secure ) {
	var today = new Date();
	today.setTime( today.getTime() );

	if ( expires ) {
		expires = expires * 1000 * 60 * 60;
	}

	var expires_date = new Date( today.getTime() + (expires) );

	document.cookie = name + "=" +escape( value ) +
		( ( expires ) ? ";expires=" + expires_date.toGMTString() : "" ) +
		( ( path ) ? ";path=" + path : "" ) + 
		( ( domain ) ? ";domain=" + domain : "" ) +
		( ( secure ) ? ";secure" : "" );
}

/**
 * Deletes the specified cookie
 */
function deleteCookie( name, path, domain ) {
	if ( getCookie( name ) ) {
        document.cookie = name + "=" +
			( ( path ) ? ";path=" + path : "") +
			( ( domain ) ? ";domain=" + domain : "" ) +
			";expires=Thu, 01-Jan-1970 00:00:01 GMT";
    }
}
