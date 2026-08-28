var check_ajax_status = 0;
var request_unread_message;
var ajaxLoading = false;
var chat_get_response = false;
jQuery(document).ready(function(){

	if (jQuery('#user-chat-popup').length){
		dap_live_chat_html_content_ajax();
	}

	jQuery(window).on('storage', dap_message_receive);

	 if (jQuery("#user-chat-popup").length && jQuery("#user-chat-popup").html().length > 0) {
		jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight")}, 10);

		jQuery('.dap-chat-visitor-body-expanding-widget-textarea').on('input', function() {
			if (jQuery.trim(jQuery(this).val()) != '') {
				jQuery('button.dap-chat-visitor-body-chat-send-button').addClass('dap-active');
			}else{
				jQuery('button.dap-chat-visitor-body-chat-send-button').removeClass('dap-active');
			}
		});

		
	}

	

});

jQuery(document).on('click','button.dap-chat-visitor-body-chat-send-button', function(){
	dap_message_ajax_send_message();
});

jQuery(document).on('click','.dap-chat-button-wrapper', function(){
	jQuery('.dap-chat-application-wrapper').toggleClass('dap-chatbox-open');
	
	jQuery('.dap-chat-visitor-chat-widget').addClass('chat-message-loading');

	if (jQuery('.dap-chat-application-wrapper').hasClass('dap-chatbox-open')) {
	    jQuery('a.dap-chat-button-wrapper').removeClass('have-chat-msg');
	   // request_unread_message.abort();
      	ajaxLoading = false;
	    dap_get_unread_message_ajax(1, 1);
	}
});
jQuery(document).on('click','.dap-chat-close-icon', function(){
	jQuery('.dap-chat-application-wrapper').removeClass('dap-chatbox-open');
});

function dap_chat_keypress_event(){
	jQuery(".dap-chat-visitor-body-expanding-widget-textarea").keypress(function(event) {
	    if (event.which == 13) {
	        event.preventDefault();
	        dap_message_ajax_send_message();
	    }
	});

    jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').on('scroll', function() {
       if(jQuery(this).scrollTop() <= 1000){
          var msg_count = jQuery('#message-total-count').val();
          var start_from_count = jQuery('#message-start-from').val();
          if (check_ajax_status == 0 && parseInt(msg_count) >= parseInt(start_from_count)) {
          	request_unread_message.abort();
          	ajaxLoading = false;
            dap_message_ajax_get_message();
          }
       }
	});

  var ajax_request_time = 20000;
  if (jQuery('#message-ajax-request').val() != '') {
    ajax_request_time = parseInt(jQuery('#message-ajax-request').val())*1000;
  }

	setInterval(function() {
		if (chat_get_response) {
	 		dap_get_unread_message_ajax();
		}
	}, ajax_request_time);
}

function dap_live_chat_html_content_ajax(){
  var ajaxurl = dap_livelink_common_ajax_object.ajax_url;
  var course_id_define =  jQuery('#course_id_hidden').val();
  var course_id = 0;
	if (typeof course_id_define !== "undefined") {
	   course_id = course_id_define;
	}
  var pageurl = jQuery('#user-chat-popup').attr('data-pageurl');
    jQuery.ajax({
      url: ajaxurl,
      type:'POST',
      data:{
        action : 'dap_live_chat_html_content',
        course_id : course_id,
        permalink : pageurl
      } ,
      success: function(response){
		if (response != '') {
			jQuery('#user-chat-popup').html(response);
			dap_message_ajax_get_message(1);
			dap_get_unread_message_ajax();
			chat_get_response = true;
			dap_chat_keypress_event();
		}
		 

      }
  });
}


function dap_message_ajax_send_message(){
	var chat_message = jQuery('.dap-chat-visitor-body-expanding-widget-textarea').val();
	if (jQuery.trim(chat_message) != '') {

		var dap_chat_today = new Date();
    	var dap_chat_time = dap_chat_today.getHours() + ":" + dap_chat_today.getMinutes();

		jQuery('.dap-chat-hidden-html-for-user .dap-chat-update-user-written-msg').text(chat_message);
		jQuery('.dap-chat-hidden-html-for-user .dap-chat-message-send-time').text(dap_chat_time);

		var user_msg = jQuery('.dap-chat-hidden-html-for-user').html();
		jQuery('.dap-chat-visitor-body-primary-message').append(user_msg);

		dap_message_broadcast({'command':'setsendmsg', 'user_msg': user_msg});

		jQuery('.dap-chat-visitor-body-expanding-widget-textarea').val('');
		jQuery('button.dap-chat-visitor-body-chat-send-button').removeClass('dap-active');
		jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight")}, 10);
		
		const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;


		

		var form_chat_data = new FormData();
		form_chat_data.append("action", 'dap_add_user_chat_message' );
		form_chat_data.append("user_msg", chat_message);
		form_chat_data.append("timezone", timezone);

		 var course_name =  jQuery('#course_name_hidden').val();
		if (typeof course_name !== "undefined") {
		   form_chat_data.append("course_name", course_name);
		}

		var lesson_name =  jQuery('#lesson_name_hidden').val();
		if (typeof lesson_name !== "undefined") {
		   form_chat_data.append("lesson_name", lesson_name);
		}
		form_chat_data.append("page_url", window.location.href);


		var ajaxurl = dap_livelink_common_ajax_object.ajax_url;
		jQuery.ajax({ 
			url: ajaxurl,
			method:"POST",
			data: form_chat_data,
			contentType: false,
			cache: false,
			processData: false,
			beforeSend:function(){
			 
			},   
			success:function(output){
			},
		    error: function (xhr, ajaxOptions, thrownError) {
		    // ajaxLoading = false;
		    }
		});
	}

}


function dap_message_ajax_get_message(stopscroll = 0){

	if(!ajaxLoading) {
		ajaxLoading = true;
		jQuery('.chat-dot-typing-wrapper').show();
		check_ajax_status = 1;
		var start_from = jQuery('#message-start-from').val();
	  	var chat_per_request = jQuery('#message-chat-per-request').val();

		const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
		var form_chat_data = new FormData();
		form_chat_data.append("action", 'dap_get_user_chat_message' );
		form_chat_data.append("timezone", timezone );
		form_chat_data.append("start_from", start_from );
		form_chat_data.append("chat_per_request", chat_per_request );
		var ajaxurl = dap_livelink_common_ajax_object.ajax_url;
		jQuery.ajax({ 
			url: ajaxurl,
			method:"POST",
			data: form_chat_data,
			contentType: false,
			cache: false,
			processData: false,
			beforeSend:function(){
			 
			},   
			success:function(response){
				check_ajax_status = 0;
				var response = JSON.parse(response);
				jQuery('.chat-dot-typing-wrapper').hide();
				
				jQuery('#message-total-count').val(response.user_msg_count);
				 var update_start_from = parseInt(start_from) + parseInt(chat_per_request);
				 jQuery('#message-start-from').val(update_start_from);

				var older_screen_height = jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight");
				jQuery('.dap-chat-visitor-body-primary-message').prepend(response.user_msg);
		        var new_screen_height = jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight");
		        var final_scroll_height = new_screen_height - older_screen_height;
		        

		        if (start_from == 0 || stopscroll == 1) {
		          jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight")}, 0);
		        }else{
		          jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: final_scroll_height }, 0);
		        }
		        ajaxLoading = false;
			},
		    error: function (xhr, ajaxOptions, thrownError) {
		     ajaxLoading = false;
		    }
		});
	}
}

function dap_get_unread_message_ajax(update_unread_message_status = 0, scrolltobottom = 0){

	if (jQuery('.dap-chat-application-wrapper').hasClass('dap-chatbox-open')) {
		update_unread_message_status = 1;
	}
	if(!ajaxLoading) {
		ajaxLoading = true;
		//jQuery('.chat-dot-typing-wrapper').show();
		check_ajax_status = 1;
		const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
		var form_chat_data = new FormData();
		form_chat_data.append("action", 'dap_get_user_chat_message' );
		form_chat_data.append("timezone", timezone );
		form_chat_data.append("msg_read_type", 'unread' );
		form_chat_data.append("update_unread_message_status", update_unread_message_status );
		var ajaxurl = dap_livelink_common_ajax_object.ajax_url;
		request_unread_message = jQuery.ajax({ 
			url: ajaxurl,
			method:"POST",
			data: form_chat_data,
			contentType: false,
			cache: false,
			processData: false,
			beforeSend:function(){
			 
			},   
			success:function(response){
				check_ajax_status = 0;
				var response = JSON.parse(response);
				//jQuery('.chat-dot-typing-wrapper').hide();

				
				
				var message_ids = response.message_ids;
		        jQuery.each(message_ids, function(i, object) {
		           jQuery('.dap-chat-visitor-body-primary-message #dap-chat-msg-'+object).remove();
		        });

		        if (update_unread_message_status == 1 ) {
		        	if (response.user_msg != '') {
		        		jQuery('.dap-chat-visitor-body-primary-message').append(response.user_msg);
		        		dap_message_broadcast({'command':'setunreadmsg', 'user_msg': response.user_msg});
		        	}
		        	
					}

				

				var total_record_found = response.total_record_found;
				if (parseInt(total_record_found) != 0) {
		          var total_record_found_org = parseInt(jQuery('#message-total-count').val());
		          var record_start_from = parseInt(jQuery('#message-start-from').val());

		          total_record_found_org = total_record_found_org + total_record_found;
		          record_start_from = record_start_from + total_record_found;

		          jQuery('#message-total-count').val(total_record_found_org);
		          jQuery('#message-start-from').val(record_start_from);

		          var scroll_area_height = jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight");
		          jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: scroll_area_height }, 0);

		        }
		        if (parseInt(response.total_record_found) >= 1 && !jQuery('.dap-chat-application-wrapper').hasClass('dap-chatbox-open')) {
		        	jQuery('a.dap-chat-button-wrapper').attr('data-chatmsg', response.total_record_found);
		        	jQuery('a.dap-chat-button-wrapper').addClass('have-chat-msg');
		        }
		        jQuery('.dap-chat-visitor-chat-widget').removeClass('chat-message-loading');

		        if (scrolltobottom == 1) {
					var scroll_area_height = jQuery('.dap-chat-visitor-body-div-messages-scroll-container-utv').prop("scrollHeight");
		          	jQuery(".dap-chat-visitor-body-div-messages-scroll-container-utv").animate({ scrollTop: scroll_area_height }, 0);
				}

		        ajaxLoading = false;
			},
		    error: function (xhr, ajaxOptions, thrownError) {
		     ajaxLoading = false;
		     jQuery('.dap-chat-visitor-chat-widget').removeClass('chat-message-loading');


		    }
		});
	}
}


function dap_message_broadcast(message)
{
    localStorage.setItem('user_msg',JSON.stringify(message));
    localStorage.removeItem('user_msg');
}


// receive message
//
function dap_message_receive(ev)
{
    if (ev.originalEvent.key!='user_msg') return; // ignore other keys
    var message=JSON.parse(ev.originalEvent.newValue);
    if (!message) return; // ignore empty msg or msg reset

    // here you act on messages.
    // you can send objects like { 'command': 'doit', 'data': 'abcd' }
    if (message.command == 'setunreadmsg'){
    	jQuery('.dap-chat-visitor-body-primary-message').append(message.user_msg);
    }

    if (message.command == 'setsendmsg'){
    	jQuery('.dap-chat-visitor-body-primary-message').append(message.user_msg);
    }

    // etc.
}