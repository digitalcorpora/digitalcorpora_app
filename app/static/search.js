// search.js for trsearch
// (C) Simson L. Garfinkel, 2022

const version='1.1.0';
const SEARCH_URL='/' + site + '/search';
const SEARCH_API_URL='/' + site + '/api/search';
const FIELDS=['title', 'author', 'body', 'metadata','start_date','end_date'];
const USE_SEARCH_API = false;

function fill_params(usp) {
    // Take a URLSearchParams object and put the fields into the form
    FIELDS.forEach(
        function(tag) {
            $('#'+tag).val( usp.get( tag ));
        });
}

function get_params() {
    // Read the form and return a URLSearchParams object
    let usp = new URLSearchParams();
    FIELDS.forEach(
        function(tag) {
            const val = $('#'+tag).val();
            if (val) {
                usp.set(tag, val);
            }
        });
    return usp;
}

const R2 = /[^a-z]/i;
function key_id(key) {
    return key.replace(R2, '_');
}

// Need to empty the table if it already has data.
// Or destory and remake it. See:
// https://stackoverflow.com/questions/12934144/how-to-reload-refresh-jquery-datatable
// https://datatables.net/reference/api/ajax.reload()
// https://github.com/abpframework/abp/issues/10054

const COLUMNS = ['datePublished','title','author','snipit','url'];
function data_columns() {
    ret = [];
    for(var j=0;j<COLUMNS.length;j++){
        ret[j] = {'title':COLUMNS[j]};
    }
    return ret
}

function fix_url(url) {
    if (url.startsWith('http')){
        return `<a href='${url}'>${url}</a>`;
    }
    return url;
}

function fill_form_from_loc() {
    const usp = new URLSearchParams(window.location.search);
    fill_params( usp );      // the URLSearchParams after the '?' in the broser URL
}

function do_search() {
    console.log('do_search');
    // Read the URL, set the form, and do the search

    // Send the encoded browser search stirng to the API on the back end
    let url = SEARCH_API_URL+'?'+usp.toString();
    $.ajax({ url: url } )
        .then(function(text) {
            const rows = JSON.parse(text);
            data = [];
            for(var i=0;i<rows.length;i++){
                row = [];
                for(var j=0;j<COLUMNS.length;j++){
                    row[j] = rows[i][COLUMNS[j]];
                    row[j] = fix_url(row[j]);
                }
                data[i] = row;
                console.log('data[i]=',i,data[i]);
            }
            // https://stackoverflow.com/questions/27778389/how-to-manually-update-datatables-table-with-new-json-data
            var datatable = $( '#report' ).DataTable();
            datatable.clear();
            datatable.rows.add( data );
            datatable.draw();
        });
    return false;
}

// dynamically add columns:
// https://stackoverflow.com/questions/37352001/dynamically-change-column-data-datatables


// If we were using the JavaScript search button,
// we would need to manually manage the URL, and we would be using the JavaScript below.
// change this to use pushstate -
// https://stackoverflow.com/questions/824349/how-do-i-modify-the-url-without-reloading-the-page
function search_button_clicked(e) {
    const url = SEARCH_URL+'?'+get_params().toString();
    //this just jumps to it and then the ready function gets called and do_search does the search
    //window.location=url;

    //This changes the string and then the search happens
    window.history.pushState(url, '', url);
    do_search();

    return false;
}

function metadata_button_clicked(e) {
    // Get a list of the selected checkboxes
    chosen_metadata = {}
    $('input.metacheck').each(
        function(i, obj) {
            if ($(this).is(':checked')) {
                const name = $(this).attr('name');
                chosen_metadata[name] = 1;
            }
        }
    );

    $('td.metadata').each(
        function(i, obj) {
            const articleId = $(this).attr('id').replace('metadata-','');
            const md = metadata[ articleId ];
            var html = '';
            for (const key of Object.keys( md ) ){
                if (chosen_metadata[key] && md[key]){
                    html += `<tr><td>${key}</td><td>${md[key]}</td>\n`;
                }
            }
            if (html != '') {
                html = '<table class="metadata">' + html + "</table>";
            }
            $(this).html( html);
        }
    );

    return true;                // without this, the box doesn't get clicked!
}

$(document).ready( function() {
    fill_form_from_loc();

    // wire up the #all and #none buttons
    $('#all').on('click', function() {
        $('.metadata').prop('checked', true);
        metadata_button_clicked();
    });

    $('#none').on('click', function() {
        $('.metadata').prop('checked', false);
        metadata_button_clicked();
    });

    // call this function if any checkbox is clicked
    $('input.metadata').on('click', metadata_button_clicked );

    // add the matched keyword to all of the divs that contain checkboxes that arrived checked
    $('input.metacheck').each(
        function(i, obj) {
            if ($(this).is(':checked')) {
                const id=$(this).attr('id');
                const label = $(`label[for='${id}']`);
                label.addClass('matched');
            }
        }
    );

    // Run the function, because some were set when the page loaded
    metadata_button_clicked();

    // Create the data table with no data and a dummy column
    if (USE_SEARCH_API){
        $('#report').DataTable({
            data: [],
            columns: data_columns(),
            pageLength:100,
            "sDom":"Rlfrtip",
            lengthMenu: [ [10, 100, 1000, -1], [10, 25, 100, 1000, "All"] ],
            oLanguage: {
                sSearch: "Filter Results: "
            }
        });
        $('select[name=report_length').val('100');

        $('#trsearchbutton').on('click', search_button_clicked );

        // If there is a search URL, then execute the search
        if (window.location.search.length > 0){
            do_search();
        }
    }
});

console.log('search.js',version);
