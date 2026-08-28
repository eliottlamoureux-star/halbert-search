function trackS3MV (action, playTime, videoId) {
	var data = {
		'action': action,
		'playTime': playTime,
		'videoId': videoId
	};

	jQuery.post(ajaxurl, data, function(response) {
		//alert('Got this from the server: ' + response);
	});
}


(function($) {

	
})(jQuery);