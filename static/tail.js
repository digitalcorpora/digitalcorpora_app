// append a line but maintain the current selection
function append(buf, next) {
    // This seems to require the actual element, not the jquery object
    // It preserves the selection after there is an append
    var txt = document.getElementById("area1");
    var start=txt.selectionStart;
    var end=txt.selectionEnd;

    // Append text using the JQuery object
    var $t2 = $("#area1");
    $t2.focus();
    $t2.val( $("#area1").val() + buf);

    // Restore the selection
    txt.setSelectionRange(start,end);

    // Scroll to the bottom
    if ($t2.length){
	$t2.scrollTop($t2[0].scrollHeight - $t2.height());
    }
    // Finally, store what's next
    $t2.attr('next',next);
}

function tailPoll() {
    var next = $("#area1").attr('next');
    console.log("next=",next)
    $.post( "https://apps.simson.net/tail/api", {loc:next}, function(resp, status){
	if (status=="success"){
	    data = JSON.parse(resp);
	    if (next != data.next){
		append(data.buf, data.next)
	    }
	}
    });
}

$(document).ready(function() {
    $.post( "https://apps.simson.net/tail/api", {}, function(resp, status){
	if (status=="success"){
	    data = JSON.parse(resp);
	    append(data.buf, data.next)
	}
    });
    setInterval( tailPoll, 1000);
});

