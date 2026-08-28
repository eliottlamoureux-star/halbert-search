/* <![CDATA[ */

var globalError = "";
var whatRequest = "";

function processChangeu(responseText, responseStatus, responseXML) {
	if (responseStatus == 200) {// 200 means "OK"
		var resource = eval('(' + responseText + ')');
		if(resource.whatRequest == 'loadUser') {
			changeLoadUser(resource.responseJSON);
		} else if(resource.whatRequest == 'updateUser') {
			changeDiv('user_msg_div',resource.responseJSON);
			NLBfadeBg('user_msg_div','#009900','#FFFFFF','1000');
			changeDiv('user_msg_div_2',resource.responseJSON);
			NLBfadeBg('user_msg_div_2','#009900','#FFFFFF','1000');
			loadUser(affId);
		}
	} else {// anything else means a problem
		//alert("There was a problem in the returned data:\n");
	}
}


function loadUser() {
	url  =  '/dap/admin/ajax/loadUserAjax.php';
	var request = new ajaxObject(url,processChangeu);
	request.update('userId=' + affId + '&whatRequest=loadUser');
}


function changeLoadUser(user){
	form = document.UserProfileForm;
	
	if(user[0].opted_out == "Y") {
		form.opted_out.checked = false;
	} else if(user[0].opted_out == "N") {
		form.opted_out.checked = true;
	}
	
	if( (user[0].user_name != null) && (user[0].user_name != "") ) {
		form.user_name.readOnly = true;
		form.user_name.style.background="#CCCCCC";
	}
	
}

function updateUser(form) {
 
	var u_opted_out;
	if(form.u_opted_out) {
		if(form.u_opted_out.checked) {
			u_opted_out = "N";
		} else {
			u_opted_out = "Y";
		}
		form.u_opted_out.value = u_opted_out;
	}
	
	if( form.u_first_name && (form.u_first_name.value == "") ){
		swal(unescape(MSG_MISSING_INFO));
		form.u_first_name.focus();
		return false; 
	}
	
	if( form.u_email && !validateEmailJS(form.u_email.value) ){
		swal(unescape(MSG_EMAIL_INVALID));
		form.u_email.focus();
		return false; 
	}
	
	if(document.getElementById('pass').style.display !="none"){		
		if(form.u_password && (form.u_password.value.length > 20)){
			swal(unescape(MSG_PASSWORD_LENGTH));
			form.u_password.focus();
			return false;
		}
			
		if(form.u_password && (form.u_password.value != "") && !validatePassword(form.u_password.value)) {
			swal(unescape(MSG_INVALID_PASS));
			form.u_password.focus();
			return false;
		}
		
		if(form.u_password && (form.u_password.value != "") && (form.u_password.value != form.password_repeat.value) ) {
			swal(unescape(MSG_PASSWORDS_MISMATCH));
			form.u_password.focus();
			return false; 
		}
	}
	
	for(i=0; i < form.elements.length; i++) {
		//document.FormName.elements[i].getAttribute("required")
		if( (form.elements[i].getAttribute("required") == "Y") && (form.elements[i].value == "") ){
			swal(unescape("Sorry, " + form.elements[i].getAttribute("realname") + " is a required field"));
			form.elements[i].focus();
			return false;
		}
		//var first_name = document.getElementById('u_first_name');
		//alert(first_name.getAttribute("required"));
	}
	
	
	form.action = '/dap/userProfileSubmit.php';
	form.submit();
}

function doWarning(form) {
	if(form.u_opted_out.checked) return;
	
	//Else, it means that user is trying to optout
	var check_box = confirm(MSG_OPTOUT_WARNING);
	if (check_box==true) { 
		// Output when OK is clicked
		return; 
	} else {
		// Output when Cancel is clicked
		form.u_opted_out.checked = true;
		return;
	}
}

function addCustomValue(customFieldName) {
	var name = customFieldName.name;
	var value = customFieldName.value;
	var customArray = new Array();
//	alert ("customFieldName=" + name);
//	alert ("customFieldName=" + value);
	var namevalue = name + "||" + value;
	customArray = removeItems(customArray, namevalue);
	customArray.push(namevalue);
	document.UserProfileForm.customArray.value = customArray;
 //  alert ("back - customArray=" + customArray);
	
}

function removeItems(array, item) {
	var i = 0;
	while (i < array.length) {
	//	alert("array=" + array[i]);
	//	alert("item=" + item);
		if (array[i] == item) {
			array.splice(i, 1);
		} else {
			i++;
		}
	}
	return array;
}

/* ]]> */
