var user_active_progress = 0;
var checkajax_is_run = 1;
jQuery(document).ready(function(){

	var startDateTime = jQuery('#start_date_hidden').val();
	//check_user_are_in_screen();
	var lesson_id_hidden = jQuery('#lesson_id_hidden').val();
	var course_id_hidden = jQuery('#course_id_hidden').val();
	random_id = 'mycoursepage_'+course_id_hidden+'_'+lesson_id_hidden;
	TimeMe.initialize({
		currentPageName: random_id
	});
	TimeMe.callWhenUserLeaves(function(){
		//console.log("The user is not currently viewing the page!");
		TimeMe.stopTimer(random_id);
		DAPcountStopTimer(random_id);
		update_dap_lession_time();
	});

	// Executes every time a user returns
	TimeMe.callWhenUserReturns(function(){
		TimeMe.startTimer(random_id);
		//console.log("The user has come back!");
		if (jQuery.isFunction(window.DAPcountStartTimer)) {
			DAPcountStartTimer(random_id);
		}
	});

	setInterval((function() {
		update_dap_lession_time(1);
	}), 60000);

	jQuery(".markas_completed_btn").click(function(event) {  
		update_dap_lession_time();
	});


	 	jQuery(document).on('click', ".dap-xp-sticky-opener", function(){
	    jQuery('.dap-xp-sticky-opener').parents('.dap-xp-sticky').toggleClass('dap-xp-sticky-active');	    
		});

		jQuery(document).on('click', ".cancel-animation-popup", function(){
	    jQuery(".animation_container").hide();
	    jQuery(".dap_lesson_player_audio").remove();
	    jQuery("html").removeClass("dap-celebration-animation-on");    
		});

		/*setTimeout(function() { 
       jQuery('.dap-xp-sticky-opener').parents('.dap-xp-sticky').removeClass('dap-xp-sticky-active');
    }, 5000);*/

    jQuery(".dap-btn-mark-as-complate").on("click", function(){
		jQuery(".markas_completed_btn_outer .markas_completed_btn, .dap-next-or-mark-btn-wrapper .markas_completed_btn").click();
	});

	jQuery(".dap-btn-mark-as-complate-next").on("click", function(e){
		e.preventDefault();
		var next_btn_lesson = jQuery(".next_btn_cont").css('display');
		if (next_btn_lesson != 'none' && (typeof next_btn_lesson !== 'undefined')) {
			jQuery(".next_btn_cont").click();
			
		}
	});

		var prev_url_lesson = jQuery("#prev_url_lesson").val();
		if (prev_url_lesson != '') {
			jQuery('#dap_header_back_brn').show();
			jQuery('#dap_header_back_brn').attr('href', prev_url_lesson);
		}



		/*var next_btn_lesson = jQuery(".next_btn_cont").css('display');
		var markas_completed_btn = jQuery(".markas_completed_btn").css('display');
		if (next_btn_lesson != 'none' && (typeof next_btn_lesson !== 'undefined')) {
			var next_btn_lesson_link = jQuery(".next_btn_cont").attr('href');
			var next_btn_lesson_text = jQuery(".next_btn_cont").text();

			next_btn_lesson_text = next_btn_lesson_text.replace('»', '');

			jQuery('#dap_header_lesson_complete_button_next').attr('href', next_btn_lesson_link);
			jQuery('#dap_header_lesson_complete_button_next .dap-course-header-navigation-btn-text').text(next_btn_lesson_text);
			jQuery('#dap_header_lesson_complete_button_next').show();
		}else if (markas_completed_btn != 'none' && (typeof markas_completed_btn !== 'undefined')) {
			jQuery('#dap_header_lesson_complete_button').show();
		}*/

});

jQuery(window).on("load", function () {
    var next_btn_lesson = jQuery(".next_btn_cont").css('display');
	var markas_completed_btn = jQuery(".markas_completed_btn").css('display');
	if (next_btn_lesson != 'none' && (typeof next_btn_lesson !== 'undefined')) {
		var next_btn_lesson_link = jQuery(".next_btn_cont").attr('href');
		var next_btn_lesson_text = jQuery(".next_btn_cont").text();

		next_btn_lesson_text = next_btn_lesson_text.replace('»', '');

		jQuery('#dap_header_lesson_complete_button_next').attr('href', next_btn_lesson_link);
		jQuery('#dap_header_lesson_complete_button_next .dap-course-header-navigation-btn-text').text(next_btn_lesson_text);
		jQuery('#dap_header_lesson_complete_button_next').show();
	}else if (markas_completed_btn != 'none' && (typeof markas_completed_btn !== 'undefined')) {
	    
	    if(jQuery('.dap-next-or-mark-btn-msg-wrapper .lesson_container').is(':visible')){
            //jQuery('.dap-course-header-navigation-btn.dap-btn-mark-as-complate').hide();
        }else{
		    jQuery('#dap_header_lesson_complete_button').show();
        }
	}
});
//TimeMe.getTimeOnCurrentPageInSeconds();


function update_dap_lession_time(checkrunforcefully = 0){
	
	if (jQuery('.dap-timer-wrapper').hasClass('dap-timer-wrapper')) {
		if(checkrunforcefully == 1){
			checkajax_is_run = 1;
		}
		var ajaxurl = dap_course.ajaxurl;
		var course_id = jQuery('#course_id_hidden').val();
		var module_id = jQuery('#module_id_hidden').val();
		var lesson_id = jQuery('#lesson_id_hidden').val();
		var user_id = jQuery('#user_id_hidden').val();
		var start_date = jQuery('#start_date_hidden').val();
		if(user_id != ''){
			var total_in_second = TimeMe.getTimeOnCurrentPageInSeconds().toFixed(0);
			if(checkajax_is_run == 1){
				checkajax_is_run = 0;
				jQuery.post(ajaxurl, {
						action: "dap_lesson_time_spent_update",
						course_id: course_id,
						module_id: module_id,
						lesson_id: lesson_id,
						user_id: user_id,			
						start_date: start_date,
						total_second: total_in_second,
						pre_sec: user_active_progress
					}, function(response) {	
						//jQuery('#start_date_hidden').val(response)
						user_active_progress = response;
						checkajax_is_run = 1;
				}).fail(function(jqXHR, textStatus, error){
				   checkajax_is_run = 1;
				});;
			}
		}
	}
}

function makeid(length) {
    var result           = '';
    var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    var charactersLength = characters.length;
    for ( var i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * 
 charactersLength));
   }
   return result;
}

function dap_confetti_animation(){
	for(i=0; i<100; i++) {
		// Random rotation
		var randomRotation = Math.floor(Math.random() * 360);
		  // Random Scale
		var randomScale = Math.random() * 1;
		// Random width & height between 0 and viewport
		var randomWidth = Math.floor(Math.random() * Math.max(document.documentElement.clientWidth, window.innerWidth || 0));
		var randomHeight =  Math.floor(Math.random() * Math.max(document.documentElement.clientHeight, window.innerHeight || 500));

		// Random animation-delay
		var randomAnimationDelay = Math.floor(Math.random() * 15);
		console.log(randomAnimationDelay);

		// Random colors
		var colors = ['#0CD977', '#FF1C1C', '#FF93DE', '#5767ED', '#FFC61C', '#8497B0']
		var randomColor = colors[Math.floor(Math.random() * colors.length)];

		// Create confetti piece
		var confetti = document.createElement('div');
		confetti.className = 'dap-modal-animation-confetti';
		confetti.style.top=randomHeight + 'px';
		confetti.style.right=randomWidth + 'px';
		confetti.style.backgroundColor=randomColor;
		// confetti.style.transform='scale(' + randomScale + ')';
		confetti.style.obacity=randomScale;
		confetti.style.transform='skew(15deg) rotate(' + randomRotation + 'deg)';
		confetti.style.animationDelay=randomAnimationDelay + 's';

		var confettiWrapper = document.getElementById("dap-modal-animation-confetti-wrapper");
		if(confettiWrapper){
			confettiWrapper.appendChild(confetti);
		}
	}
}

window.onload = function() {

jQuery.fn.DAPScrollTo = function(elem, speed) { 
	if (jQuery(this).length && jQuery(elem).length) {
		 jQuery(this).animate({
	        scrollTop:  jQuery(this).scrollTop() - jQuery(this).offset().top + jQuery(elem).offset().top 
	    }, speed == undefined ? 1000 : speed); 
	    return this; 
	}
   
};

}