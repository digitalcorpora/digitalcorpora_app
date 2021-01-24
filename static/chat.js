// append a line but maintain the current selection
function appendLine(line) {
    var txt = document.getElementById("area1");
    txt.focus();
    var start=txt.selectionStart;
    var end=txt.selectionEnd;
    $("#area1").val( $("#area1").val() + line + "\n");
    txt.focus();
    txt.setSelectionRange(start,end);
}
// https://stackoverflow.com/questions/35072104/jquery-popup-window-scrolling
// for the pop-up, see http://jsfiddle.net/db5SX/6662/ and 
// Get all of the most recent status updates. In the future, we'll only ask for specific text fields.
function statusPoll() {
    $.get( "https://apps.simson.net/chat/poll", {t:$("#status1-text").attr('t')} , function(data, status){
	if (status=="success"){
	    for (work of JSON.parse(data)) {
		$("#"+work.channel+"-text").val(work.message);
		$("#"+work.channel+"-text").attr('t',work.t);
	    }
	} else {
	    console.log("ERROR from statusPoll: data=",data," status=",status);
	}
    });
}

// Called when a button is clicked; sends the button's contents to the webserver. The server returns time of the log message
// which is written into the text field
function statusSend() {
	var line = $("#status1-text").val();
	$.post( "https://apps.simson.net/chat/post", {channel:"status1", message:line}, function(data, status){
	    if (status=="success"){
		console.log("data:",data)
		work = JSON.parse(data);
		console.log("work:",work);
	    }
	});
	return false;
}

// add 
function makeDateText(date,text) {
    console.log("date=",date);
    var now = date.toISOString().slice(0, 19).replace("T"," ");
    return '<span class="tiny">'+now+'</span> ' + text;
}

function makeTimeText(msec,text) {
    var desc = '';
    if ( msec < 1000 ) {
	desc = msec.toString() + " msec";
    } else {
	var sec   = Math.floor(msec/1000);
	var days  = Math.floor(sec / (60*60*24) ); sec -= days*60*60*24;
	var hours = Math.floor(sec / (60*60)    ); sec -= hours*60*60;
	var mins  = Math.floor(sec / 60 );         sec -= mins*60;
			       
	if (days>0) {
	    desc += days.toString() + " d ";
	} else if (hours>0) {
	    desc += hours.toString() + " h ";
	} else if (mins>0) {
	    desc += mins.toString() + " m ";
	} else {
	    desc += sec.toString() + " s ";
	}
    }
    return '<span class="tiny">'+desc+'</span> ' + text;
}

function extractText(text) {
    return text.replace(/<span.*span>/,"");
}

function autoloadUpdate() {
    $('.autoload').each( function() {
	var timediff = new Date() - new Date($(this).attr('t'));
	$(this).html( makeTimeText( timediff, extractText( $(this).html()) ) );
    });
}

$(document).ready(function() {
    $('.edit-on-click').click(function() {
	var $text  = $(this);
	var $input = $('<input type="text" />')

	console.log("ctc=",$text.attr('ctc'));
	if ( $text.attr('ctc') != undefined && $text.attr('ctc') != ''){
	    $text.html("");	// click to clear
	}

	$text.hide().after($input);
	$input.val( extractText($text.html()) ).show().focus()
	    .keypress(function(e) {
		var key = e.which
		if (key == 13) { // enter key
		    $input.hide();
		    $text.html($input.val()).show();
		    console.log("input:",$input.val());
		    $text.attr('t', new Date()); // update the date
		    return false;
		}
	    })
	    .focusout(function() {
		$input.hide();
		$text.show();
	    })
    });

    // textfields use .val() to set
    // spans use .html() to set
    $('.autoload').each( function() {
	$(this).attr('t', new Date());
	var channel = $(this).attr('channel');
	var t = $(this).attr('t');
	console.log(" channel=",channel,"t=",t);
    });

    setInterval( autoloadUpdate, 1000);
});

