function getCheckedValue(radioObj) {
	if(!radioObj)
		return "";
	var radioLength = radioObj.length;
	if(radioLength == undefined)
		if(radioObj.checked)
			return radioObj.value;
		else
			return "";
	for(var i = 0; i < radioLength; i++) {
		if(radioObj[i].checked) {
			return radioObj[i].value;
		}
	}
	return "";
}

function setCheckedValue(radioObj, newValue) {
	if(!radioObj)
		return;
	var radioLength = radioObj.length;
	if(radioLength == undefined) {
		radioObj.checked = (radioObj.value == newValue.toString());
		return;
	}
	for(var i = 0; i < radioLength; i++) {
		radioObj[i].checked = false;
		if(radioObj[i].value == newValue.toString()) {
			radioObj[i].checked = true;
		}
	}
}

function validateEmailJS(email) {
	var email = trim(email); // value of field with whitespace trimmed off
	var emailFilter = /^[^@]+@[^@.]+\.[^@]*\w\w$/ ;
	var illegalChars= /[\(\)\<\>\,\;\:\\\"\[\]]/ ;

	if (email == "") {
		return false;
	} else if (!emailFilter.test(email)) { //test for valid email format
		return false;
	} else if (email.match(illegalChars)) { // test for illegal characters
		return false;
	}

	return true;
}

function clearDefaultText(form) {
	if ( form.coupon_code.value == "(optional)" ) {
		form.coupon_code.value = "";
	}
}

function resetDefaultText(form) {
	if ( form.coupon_code.value == "" ) {
		form.coupon_code.value = "(optional)";
	}
}


var IE = document.all ? true:false;
if (!IE) document.captureEvents(Event.MOUSEMOVE);
document.onmousemove = getMouseXY;
var mouseX = 0;
var mouseY = 0;

function getMouseXY(e) {
	if (IE) { // grab the x-y pos.s if browser is IE
		mouseX = event.clientX + document.body.scrollLeft;
		mouseY = event.clientY + document.body.scrollTop;
	}
	else {  // grab the x-y pos.s if browser is NS
		mouseX = e.pageX;
		mouseY = e.pageY;
	}  
	if (mouseX < 0){mouseX = 0;}
	if (mouseY < 0){mouseY = 0;}  
	//document.Show.MouseX.value = mouseX;
	//document.Show.MouseY.value = mouseY;
}

//jQuery.noConflict();
//jQuery(document).ready(function($) {
//});    

function toggleImageAndDiv(cid){
	if (document.getElementById("expando_"+cid)) {
		if (document.getElementById("expando_"+cid).className=="expando") { 
			document.getElementById("expando_"+cid).className="expando3";
			showDiv(cid);
		} else { 
			document.getElementById("expando_"+cid).className="expando";
			hideDiv(cid);
		}
	}
}

function toggleImage(cid){
	showDiv(cid);
	document.getElementById("expando_"+cid).className="expando3";
}

function validatePassword(password) {
 
	for(j=0; j<password.length; j++) {
	  if(parseInt(password[j])) continue;
	   var pattern = /^[a-zA-Z_0-9@\#"<=>_\$\^%()*!&+;`\-[]\\\',\.\/\{\}\|\:\? ]+$/;
	  if (pattern.test(password[j])) continue;
 
	} //end for

	return true;
}

function isValidURL(url){
	//var RegExp = /^(([\w]+:)?\/\/)?(([\d\w]|%[a-fA-f\d]{2,2})+(:([\d\w]|%[a-fA-f\d]{2,2})+)?@)?([\d\w][-\d\w]{0,253}[\d\w]\.)+[\w]{2,4}(:[\d]+)?(\/([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)*(\?(&?([-+_~.\d\w]|%[a-fA-f\d]{2,2})=?)*)?(#([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)?$/;
	var RegExp = /(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;

	if(url.substring(0,4) != "http") {
		alert("Sorry, the URL must begin with 'http://...'")
		return false;
	}
	
	if(url.substring(0,16) == "http://localhost") {
		//testing purposes only - for localhost deployment
		return true;
	}
	
	if( RegExp.test(url) ){
		return true;
	} else {
		alert("Sorry, that is an invalid URL. Please enter a valid URL.")
	}
}

function modButton(btn) {
	btn.value = "Pls wait...";
	btn.disabled = true;
}

function unModButton(btn, txt) {
	btn.value = txt;
	btn.disabled = false;
}

function showLongProgressBar(divName, txt){
	document.getElementById(divName).innerHTML = txt + '<img src="/dap/images/progressbar.gif">';
}

function showRoundProgressBar(divName, txt){
	document.getElementById(divName).innerHTML = txt + '<img src="/dap/images/progressbar-round.gif">';
}

function changeDiv(divName,input) {
	document.getElementById(divName).innerHTML = input;
}

function clearDiv(divName) {
	var divNameElem = document.getElementById(divName);
	if(divNameElem) {
		document.getElementById(divName).innerHTML = "";
	}
}

function toggleDiv(input) {
	var divName = document.getElementById(input);
	if(divName.style.display == "none") {
		divName.style.display = "block"; //to hide it
	} else if(divName.style.display == "block") {
		divName.style.display = "none"; //to show it
	}
	return false;
}

function showDiv(input) {
	var divName = document.getElementById(input);
	divName.style.display = "block"; //to show it
}

function hideDiv(input) {
	var divName = document.getElementById(input);
	divName.style.display = "none"; //to hide it
}

function trim(str, chars) {
    return ltrim(rtrim(str, chars), chars);
}

function ltrim(str, chars) {
    chars = chars || "\\s";
    return str.replace(new RegExp("^[" + chars + "]+", "g"), "");
}

function rtrim(str, chars) {
    chars = chars || "\\s";
    return str.replace(new RegExp("[" + chars + "]+$", "g"), "");
}

//Start Fader Script
/*************************************************************
* NLB Background Color Fader v1.0
* Author: Justin Barlow - www.netlobo.com
*
* Description:
* The Background Color Fader allows you to gradually fade the
* background of any HTML element.
*
* Usage:
* Call the Background Color Fader as follows:
*   NLBfadeBg( elementId, startBgColor, endBgColor, fadeTime );
*
* Description of Parameters
*   elementId - The id of the element you wish to fade the
*             background of.
*   startBgColor - The background color you wish to start the
*             fade from.
*   endBgColor - The background color you want to fade to.
*   fadeTime - The duration of the fade in milliseconds.
*************************************************************/

var nlbFade_hextable = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' ]; // used for RGB to Hex and Hex to RGB conversions
var nlbFade_elemTable = new Array( ); // global array to keep track of faded elements
var nlbFade_t = new Array( ); // global array to keep track of fading timers
function NLBfadeBg( elementId, startBgColor, endBgColor, fadeTime )
{
	var timeBetweenSteps = Math.round( Math.max( fadeTime / 300, 30 ) );
	var nlbFade_elemTableId = nlbFade_elemTable.indexOf( elementId );
	if( nlbFade_elemTableId > -1 )
	{
		for( var i = 0; i < nlbFade_t[nlbFade_elemTableId].length; i++ )
			clearTimeout( nlbFade_t[nlbFade_elemTableId][i] );
	}
	else
	{
		nlbFade_elemTable.push( elementId );
		nlbFade_elemTableId = nlbFade_elemTable.indexOf( elementId );
	}
	var startBgColorRGB = hexToRGB( startBgColor );
	var endBgColorRGB = hexToRGB( endBgColor );
	var diffRGB = new Array( );
	for( var i = 0; i < 3; i++ )
		diffRGB[i] = endBgColorRGB[i] - startBgColorRGB[i];
	var steps = Math.ceil( fadeTime / timeBetweenSteps );
	var nlbFade_s = new Array( );
	for( var i = 1; i <= steps; i++ )
	{
		var changes = new Array( );
		for( var j = 0; j < diffRGB.length; j++ )
			changes[j] = startBgColorRGB[j] + Math.round( ( diffRGB[j] / steps ) * i );
		if( i == steps )
			nlbFade_s[i - 1] = setTimeout( 'document.getElementById("'+elementId+'").style.backgroundColor = "'+endBgColor+'";', timeBetweenSteps*(i-1) );
		else
			nlbFade_s[i - 1] = setTimeout( 'document.getElementById("'+elementId+'").style.backgroundColor = "'+RGBToHex( changes )+'";', timeBetweenSteps*(i-1) );
	}
	nlbFade_t[nlbFade_elemTableId] = nlbFade_s;
}
function hexToRGB( hexVal )
{
	hexVal = hexVal.toUpperCase( );
	if( hexVal.substring( 0, 1 ) == '#' )
		hexVal = hexVal.substring( 1 );
	var hexArray = new Array( );
	var rgbArray = new Array( );
	hexArray[0] = hexVal.substring( 0, 2 );
	hexArray[1] = hexVal.substring( 2, 4 );
	hexArray[2] = hexVal.substring( 4, 6 );
	for( var k = 0; k < hexArray.length; k++ )
	{
		var num = hexArray[k];
		var res = 0;
		var j = 0;
		for( var i = num.length - 1; i >= 0; i-- )
			res += parseInt( nlbFade_hextable.indexOf( num.charAt( i ) ) ) * Math.pow( 16, j++ );
		rgbArray[k] = res;
	}
	return rgbArray;
}
function RGBToHex( rgbArray )
{
	var retval = new Array( );
	for( var j = 0; j < rgbArray.length; j++ )
	{
		var result = new Array( );
		var val = rgbArray[j];
		var i = 0;
		while( val > 16 )
		{
			result[i++] = val%16;
			val = Math.floor( val/16 );
		}
		result[i++] = val%16;
		var out = '';
		for( var k = result.length - 1; k >= 0; k-- )
			out += nlbFade_hextable[result[k]];
		retval[j] = padLeft( out, '0', 2 );
	}
	out = '#';
	for( var i = 0; i < retval.length; i++ )
		out += retval[i];
	return out;
}
if (!Array.prototype.indexOf) {
	Array.prototype.indexOf = function( val, fromIndex ) {
		if( typeof( fromIndex ) != 'number' ) fromIndex = 0;
		for( var index = fromIndex, len = this.length; index < len; index++ )
			if( this[index] == val ) return index;
		return -1;
	}
}
function padLeft( string, character, paddedWidth )
{
	if( string.length >= paddedWidth )
		return string;
	else
	{
		while( string.length < paddedWidth )
			string = character + string;
	}
	return string;
}
//End Fader Script
