/*
	Initial text holds what should be set for the title of the song in the player.
*/
var initialText = [];

(function(){
	/*
		Configure the player views based on the config
		provided by the user.
	*/
	configurePlayerViews();

	/*
		Initialize Amplitude
	*/
	initializeAmplitude();

	/*
		Sets the initial text so we can truncate as needed.
	*/
	setInitialText();

	/*
		Add ellipses to the text box
	*/
	ellipsizeTextBox();

	/*
		Bind Song Downloads
	*/
	bindPlayerDownloads();

	/*
		Show all players on the page
	*/
	showPlayers();
})();

/*
	When the document is loaded, make sure the text box has ellipses where
	necessary.
*/
document.addEventListener("DOMContentLoaded", function(event) {
  	ellipsizeTextBox();
});

/*
	When the window is resized, make sure the text box has ellipses where
	necessary.
*/
window.onresize = function(){
	ellipsizeTextBox();
}

/*
	Sets the initial text variable
*/
function setInitialText(){
	/*
		Gets the audio item names from the players.
	*/
	var audioItemNames = document.getElementsByClassName('player-audio-item-name');

   	/*
		Set the initial text  variables
   	*/
    for( var i = 0; i < audioItemNames.length; i++ ){
    	 initialText[i] = audioItemNames[i].innerHTML;
    }
}

/*
	Truncates the string accordingly with ellipses if needed
*/
function ellipsizeTextBox() {
	/*
		Gets all of the player name fields
	*/
    var audioItemNames = document.getElementsByClassName('player-audio-item-name');

    /*
		Iterates over the player name fields and sets the inner html to
		a truncated string with ellipses
    */
    for( var i = 0; i < audioItemNames.length; i++ ){
    	/*
			Sets the inner HTML to the initial text.
    	*/
    	audioItemNames[i].innerHTML = initialText[i];

    	/*
			Splits the names by spaces
    	*/
    	var wordArray = audioItemNames[i].innerHTML.split(' ');

    	/*
			As long as the scroll height is greater than the offset height (+2 for firefox bug)
			we keep adding a word to the HTML
    	*/
    	while( audioItemNames[i].scrollHeight > audioItemNames[i].offsetHeight + 2 ) {
	        wordArray.pop();
	        audioItemNames[i].innerHTML = wordArray.join(' ') + '...';
	    }
    }
}

/*
	Initializes Amplitude.js
*/
function initializeAmplitude(){
	/*
		Builds the array of songs used by the player.
	*/
	var songs = buildSongsArray();

	/*
        Initialize AmplitudeJS and configure source media files
    */
    Amplitude.init({
        "songs": songs,
				"continue_next": false
    });
}

/*
	Builds an array of songs
*/
function buildSongsArray(){
	/*
		Initializes the songs array.
	*/
	var songsArray = [];

	/*
		Builds the songs array with the URLs provided
	*/
	for( var i = 0; i < players.length; i++ ){
		songsArray[i] = {
			'url': players[i].url
		}
	}

	/*
		Returns the songs array.
	*/
	return songsArray;
}

/*
	Configures the views for the player
*/
function configurePlayerViews(){
	for( var i = 0; i < players.length; i++ ){
		var playerElement = document.getElementById('player-'+ ( i + 1 ) );

		/*
			Gets the audio item names
		*/
		var audioItemNames = playerElement.getElementsByClassName('player-audio-item-name');

		/*
			Sets the line height to 24 px so we can do ellipses.
		*/
		for( var k = 0; k < audioItemNames.length; k++ ){
			audioItemNames[k].style.lineHeight = '24px';
		}

		/*
			Get the player speed icons and download icons
		*/
		var speedIcons = playerElement.getElementsByClassName('player-speed');
		var downloadIcons = playerElement.getElementsByClassName('player-download-link');

		/*
			Determine if the player should show the speed icon or not.
		*/
		if( !players[i].show_speed_icon ){
			for( var k = 0; k < speedIcons.length; k++ ){
				speedIcons[k].style.display = "none";
			}
		}

		/*
			Determine if the player should show the download icon or not
		*/
		if( !players[i].show_download_icon ){
			for( var k = 0; k < downloadIcons.length; k++ ){
				downloadIcons[k].style.display = "none";
			}
		}

		/*
			Determine if we should show the episode image or not.
		*/
		if( !players[i].show_episode_image ){
			playerElement.classList.add('hide-episode-image');
		}

		/*
			Apply the appropriate class to the player to show or hide the icons.
		*/
		if( players[i].show_speed_icon && players[i].show_download_icon ){
			playerElement.classList.add('show-all-icons');
		}else if( players[i].show_speed_icon && !players[i].show_download_icon ){
			playerElement.classList.add('show-speed-icons');
		}else if( !players[i].show_speed_icon && players[i].show_download_icon ){
			playerElement.classList.add('show-download-icons');
		}else{
			playerElement.classList.add('show-no-function-icons');
		}
	}
}

/*
	Bind the download links for each song
*/
function bindPlayerDownloads(){
	/*
		Gets all download links
	*/
	var playerDownloadLinks = document.getElementsByClassName('player-download-link');

	/*
		Set the download URL for each link.
	*/
	for( var i = 0; i < playerDownloadLinks.length; i++ ){
		var songIndex = playerDownloadLinks[i].getAttribute('amplitude-song-index');
		var song = Amplitude.getSongByIndex( songIndex );

		playerDownloadLinks[i].setAttribute( 'href', song.url );
	}
}

/*
	Show each player element.
*/
function showPlayers(){
	var playerElements = document.getElementsByClassName("player");

	for( var i = 0; i < players.length; i++ ){
		playerElements[i].style.display = "block";
	}
}
