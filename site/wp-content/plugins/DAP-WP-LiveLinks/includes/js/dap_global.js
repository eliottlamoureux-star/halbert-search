jQuery(document).ready(function(){
	//added for loggedin menu showing 2 times in mobile
	var liText = '', liList = jQuery('#et_mobile_nav_menu #mobile_menu li'), listForRemove = [];

	jQuery(liList).each(function () {

	  var text = jQuery(this).text();

	  if (liText.indexOf('|'+ text + '|') == -1)
		liText += '|'+ text + '|';
	  else
		listForRemove.push(jQuery(this));

	});

	jQuery(listForRemove).each(function () { jQuery(this).remove(); });
	
	 dap_screen_resoluation();

	 jQuery(window).resize(function() {
		var dap_screen_res = jQuery(window).width();
		dap_screen_resoluation(dap_screen_res);
	});

	 if (jQuery('#todo_list_customize_template').length){
		var dap_ct_element_tasks_checkbox_tick_color = jQuery('#todo_list_customize_template').find('.dap_add_more_task_text_main').attr('checkbox-tick-color');
		if(typeof dap_ct_element_tasks_checkbox_tick_color != 'undefined' && typeof dap_ct_element_tasks_checkbox_tick_color != undefined){
		   // jQuery('.dap-custom-task-list-main-wrapper .dap_challenge_checkbox-custom-style .custom--checkbox').css('color',dap_ct_element_tasks_checkbox_tick_color);
		}
	}

	dap_error_page_move();
});

if (jQuery('.dap-show-error-page-popup').length) {
	jQuery(window).scroll(function() {
		if (dapIsScrolledIntoView('.dap-show-error-page-popup')) {
			jQuery('body').addClass('dap-error-popup-active');
		}else{
			jQuery('body').removeClass('dap-error-popup-active');
		}
	});
}
function dap_screen_resoluation(dap_screen_res = ''){
	if(dap_screen_res == ''){
		dap_screen_res = jQuery(window).width();
	}
	jQuery('html').css("--dap_screen_res", dap_screen_res+"px");
}

function dap_custom_task_func(){
	jQuery(".dap-custom-task-list-main-wrapper .checkbox_taskcls").change(function(event) {
		event.preventDefault(); 				
		var ajaxurl = "/wp-admin/admin-ajax.php";	 
		var checkbox_val=0;
		var taskid = jQuery(this).val();				  
		var checkbox_checked = jQuery(this).prop("checked");
		if(checkbox_checked ==true){
			checkbox_val=1;					 
			var background_col = jQuery(this).closest(".dragdrop_add_more_task_text").attr("checkbox-tick-color");	 					
			//jQuery(this).closest(".challageTaskItem").find(".dap_challenge_checkbox-custom-style .custom--checkbox").css("color", background_col);		  
		}			  
		var taskname = jQuery(this).closest(".challageTaskItem").find(".challageTaskItem_text div").text();	
		jQuery(this).closest(".challageTaskItem").find(".dap_challenge_checkbox-custom-style").addClass("dap_challenge_complete");
			 
		jQuery.post(ajaxurl, {
			action: "dap_lesson_status",
			actionname:"task_complete",
			course_id: '',
			module_id: '',
			lesson_id: '',
			mod_name: "",
			course_name: "fdfd23",
			lesson_name: "advfhssc",
			user_id: '',			
			product_structure: "module_lesson",
			taskid: taskid,
			sendcourseemail:"",
			sendmoduleemail: "",
			sendlessonemail: "",
			start_date: "2022-12-16 02:26:14",
			seconds: "seconds",
			next_btn: "no",
			current_url:  "",
			pageid:  "2454",
			related_courses:  "related_courses",
			taskname:  taskname,
			tasktype:  "default",
			checkbox_val: checkbox_val,
		}, function(response) {			 
			  	
		});  	        
	});
}

function dap_error_page_move(){
	var content_html = jQuery('.dap-error-page-content-in-body').html();
	jQuery('.dap-error-page-content-in-body').remove();
	jQuery('body').append(content_html);
}

function dapIsScrolledIntoView(elem)
{
    var docViewTop = jQuery(window).scrollTop();
    var docViewBottom = docViewTop + jQuery(window).height();

    var elemTop = jQuery(elem).offset().top;
    var elemBottom = elemTop + jQuery(elem).height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}