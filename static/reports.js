// https://stackoverflow.com/questions/5448545/how-to-retrieve-get-parameters-from-javascript

const REPORT_URL='/reports/json/';

function findGetParameter(parameterName) {
    var result = null,
        tmp = [];
    var items = location.search.substr(1).split("&");
    for (var index = 0; index < items.length; index++) {
        tmp = items[index].split("=");
        if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
    }
    return result;
}

function row(tag, cols){
  return "<tr>"+ cols.map(x => `<${tag}>${x}</${tag}>`).join('') + '</tr>\n';
}

function table(column_names, rows) {
    return "<table>\n" + row("th", column_names)
      + rows.map( r => row("td",r) ).join('')
      + "\n</table>\n";
}

$( document ).ready( function() {
    let num = findGetParameter("report");
    console.log("ready! report=",num);
    $.getJSON( REPORT_URL + num, function( data ) {
        console.log("data=",data);
        $('#report').html(`<h2> ${data.title} </h2>\n` + table(data.column_names,data.rows));
    })
});
