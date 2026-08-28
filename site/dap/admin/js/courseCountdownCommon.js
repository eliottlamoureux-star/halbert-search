var start = true;
var days = "00";
var hours = "00";
var minutes = "00";
var seconds = "00";
var vars = {};
var lesson_id_hidden = '';
var course_id_hidden = '';
var random_id_timer = '';
jQuery(document).ready(function(){

  jQuery('#countDownMain .dap_timer_days .dap_timer_value').html('00');
  jQuery('#countDownMain .dap_timer_hours .dap_timer_value').html('00');
  jQuery('#countDownMain .dap_timer_minutes .dap_timer_value').html('00');
  jQuery('#countDownMain .dap_timer_seconds .dap_timer_value').html('00');
  jQuery('.dap-timer-wrapper').show();
	//DAPcountDownTimer();
  var multiple_counter = 0;
  

  jQuery('.dap-timer-wrapper').each(function(index, el) {
    var get_time_from_db = jQuery(this).attr('data-seconds');
    var get_time_type_from_db = jQuery(this).attr('data-type');
    
    multiple_counter++;
   



  lesson_id_hidden = jQuery('#lesson_id_hidden').val();
  course_id_hidden = jQuery('#course_id_hidden').val();
  random_id_timer = 'mycoursepage_'+course_id_hidden+'_'+lesson_id_hidden;
  vars[random_id_timer] = 'true';

    if(get_time_type_from_db == 'countdown-timer'){
       vars['days_' + multiple_counter] =  '';
       vars['hours_' + multiple_counter] = '';
       vars['minutes_' + multiple_counter] = '';
       vars['seconds_' + multiple_counter] = '';

      DAPcountDownTimer(this, get_time_from_db, multiple_counter);
    }else{
       get_time_from_db = Number(get_time_from_db);
        vars['days_' + multiple_counter] =  Math.floor(get_time_from_db / (3600*24));
        vars['hours_' + multiple_counter] = Math.floor(get_time_from_db % (3600*24) / 3600);
        vars['minutes_' + multiple_counter] = Math.floor(get_time_from_db % 3600 / 60);
        vars['seconds_' + multiple_counter] = Math.floor(get_time_from_db % 60);

        if(vars['days_' + multiple_counter] < 10){
            vars['days_' + multiple_counter] = '0'+vars['days_' + multiple_counter];
        }
        if(vars['hours_' + multiple_counter] < 10){
            vars['hours_' + multiple_counter] = '0'+vars['hours_' + multiple_counter];
        }
        if(vars['minutes_' + multiple_counter] < 10){
            vars['minutes_' + multiple_counter] = '0'+vars['minutes_' + multiple_counter];
        }
        if(vars['seconds_' + multiple_counter] < 10){
            vars['seconds_' + multiple_counter] = '0'+vars['seconds_' + multiple_counter];
        }
      DAPcountStopWatch(this, get_time_from_db, multiple_counter);
    }
  });
	
	
});	

function DAPcountDownTimer(thisvar, time = '', multiple_counter) {

  var days = vars['days_' +multiple_counter];
  var hours = vars['hours_' +multiple_counter];
  var minutes = vars['minutes_' +multiple_counter];
  var seconds = vars['seconds_' +multiple_counter];

	if(time == ''){
		var time = 40000;
	}
  //var elem = jQuery('#countDownMain');
 
 //jQuery( "p" ).add( "div" ).addClass( "widget" );
 // var futureTime = new Date(date).getTime();
  var currentDate = new Date();
  var futureTime = new Date(currentDate.getTime() + time*1000);

  setInterval(function() { 
    // Time left between future and current time in Seconds
    var timeLeft = Math.floor( (futureTime - new Date().getTime()) / 1000 );
   if(timeLeft >= 0){
    
    // Days left = time left / Seconds per Day 
    var days =  Math.floor(timeLeft / 86400);
    // console.log(days);
    
    // 86400 seconds per Day
    timeLeft -= days * 86400;
    // console.log(timeLeft);
    
    // Hours left = time left / Seconds per Hour
    var hours = Math.floor(timeLeft / 3600) % 24;
    // console.log(hours);

    // 3600 seconds per Hour
    timeLeft -= hours * 3600;
    // console.log(timeLeft);
    
    // Minutes left = time left / Minutes per Hour
    var min = Math.floor(timeLeft / 60) % 60;
    // console.log(min);
    
    // 60 seconds per minute
    timeLeft -= min * 60;
    // console.log(timeLeft);
    
    // Seconds Left
    var sec = timeLeft % 60;
    }else{
    	var days = 0;
    	var hours = 0;
    	var min = 0;
    	var sec = 0;
    }

    if(parseInt(sec)< 10){
      sec = "0" + sec;
    };

    if(parseInt(min) < 10){
      min = '0'+min;
    };
    if(parseInt(hours) < 10){
      hours = '0'+hours;
    };
    if(parseInt(days) < 10){
      days = '0'+days;
    };
    jQuery(thisvar).find('.dap_timer_days .dap_timer_value').html(days);
    jQuery(thisvar).find('.dap_timer_hours .dap_timer_value').html(hours);
    jQuery(thisvar).find('.dap_timer_minutes .dap_timer_value').html(min);
    jQuery(thisvar).find('.dap_timer_seconds .dap_timer_value').html(sec);
    
  }, 1000);
}


function DAPcountStopWatch(thisvar, get_time_from_db, multiple_counter){

var currentTime = '';

  /*var days = vars['days_' +multiple_counter];
  var hours = vars['hours_' +multiple_counter];
  var minutes = vars['minutes_' +multiple_counter];
  var seconds = vars['seconds_' +multiple_counter];*/ 
  //DAPsecondsToDhms(multiple_counter, get_time_from_db);

setInterval(function() { 

      lesson_id_hidden = jQuery('#lesson_id_hidden').val();
      course_id_hidden = jQuery('#course_id_hidden').val();
      random_id_timer = 'mycoursepage_'+course_id_hidden+'_'+lesson_id_hidden;
    	if (vars[random_id_timer]){
          jQuery(thisvar).find('.dap_timer_days .dap_timer_value').html(vars['days_' +multiple_counter]);
			    jQuery(thisvar).find('.dap_timer_hours .dap_timer_value').html(vars['hours_' +multiple_counter]);
			    jQuery(thisvar).find('.dap_timer_minutes .dap_timer_value').html(vars['minutes_' +multiple_counter]);
			    jQuery(thisvar).find('.dap_timer_seconds .dap_timer_value').html(vars['seconds_' +multiple_counter]);
          vars['seconds_' +multiple_counter] ++;
          if(parseInt(vars['seconds_' +multiple_counter])< 10){
              vars['seconds_' +multiple_counter] = "0" + vars['seconds_' +multiple_counter];
          };
          if (vars['seconds_' +multiple_counter] == 60){
              vars['seconds_' +multiple_counter] ="00";
              vars['minutes_' +multiple_counter]++;
              if(vars['minutes_' +multiple_counter] < 10){
                  vars['minutes_' +multiple_counter] = '0'+vars['minutes_' +multiple_counter];
              };
          };
          if (vars['minutes_' +multiple_counter] == 60){
              vars['seconds_' +multiple_counter] ="00";
              vars['minutes_' +multiple_counter] = "00";
              vars['hours_' +multiple_counter] ++;
              if(vars['hours_' +multiple_counter] < 10){
                  vars['hours_' +multiple_counter] = '0'+vars['hours_' +multiple_counter];
              };
          };
          if (vars['hours_' +multiple_counter] == 60){
              vars['seconds_' +multiple_counter] ="00";
              vars['minutes_' +multiple_counter] = "00";
              vars['hours_' +multiple_counter] = "00";
              vars['days_' +multiple_counter] ++;
              if(vars['days_' +multiple_counter] < 10){
                  vars['days_' +multiple_counter] = '0'+vars['days_' +multiple_counter];
              };
          };
    	}
    }, 1000);

//stopTimer();

}

function DAPcountStopTimer(random_id){
   // start = random_id+'_false';

    vars[random_id] = false;
}

function DAPcountStartTimer(random_id){
   // start = random_id+'_true';

    vars[random_id] = true;
}

function DAPsecondsToDhms(thisvar, totalSeconds) {

	
}