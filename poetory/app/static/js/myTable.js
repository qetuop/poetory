function populateTable(data, textStatus, xhr) {
    //console.log(textStatus)
    //console.log(xhr)
    var columns = [];
    visibleColumnNames = Object.assign(data.visible)

    for (var i in visibleColumnNames) {
        columns.push({
            data: visibleColumnNames[i],
            title: visibleColumnNames[i],
            visible: true,
            defaultContent: ""
        });
    }

    // reset table
    if (table !== null ) {
        $('#example').DataTable().destroy();
        table = null;
        // empty in case the columns change
        $('#example').empty();
    }

    var table = $('#example').DataTable({
        data: data.items,
        columns: columns
    });
}

function filterData() {
    $.ajax({
        url: "/filterdata",
        success: populateTable
    }); // ajax
} // filterData()

function getData() {
    $.ajax({
        url: "/getdata",
        success: filterData
    }); // ajax
} // getData()

$(document).ready( function () {
  //$("#reload").click(getData()); // click
  filterData();

    $('.mySelect2').select2();
  //$('#example-getting-started').multiselect();

  $('#example').DataTable( {
    data: [[
            ""
           ]]
  } );
} ); // documentReady


function submit() {
    var affixes = $('.mySelect2').select2('data');
    ids = []
    affixes.forEach(item => {
        console.log(item.id, item.text);
     });

    $.ajax({
        type: 'POST',
        url: "/filterdata",
        data: {
          'affixIds[]': $('.mySelect2').val()
        },
        success: populateTable
    }); // ajax

};

/*
        dataType: 'json',
data: function (params) {
                return {
                    q: params.id
                };
         },
*/
/*
$.ajax({
      type: 'POST',
      url: 'MyServerUrl',
      data: {
          'color[]': $('select.select2').val()
      },
      success: function (data, textStatus, jqXHR){

      },
      error: function (data, textStatus, jqXHR) {
      }
 });
 */


function getDataFile() {
    $.ajax({
        url: "/static/ajax/objects.txt",
        success: function(data) {
            var columns = [];

            data = JSON.parse(data)

            // THIS IS THE READ FROM FILE HANDLER YOU WANT THE ONE BELOW!!!

            visibleColumnNames = Object.assign(data.visible)
            console.log(visibleColumnNames)

            columnNames = Object.keys(data.data[0]);
            for (var i in columnNames) {
                columns.push({
                    data: columnNames[i],
                    title: columnNames[i],
                    visible: visibleColumnNames.includes(columnNames[i])
                });
            }
            table = $('#example').DataTable({
                data: data.data,
                columns: columns
            });
        }
    })
}


/*  This will update table on page load
ready() calls getData passing in a function that is called in ajax: success

function getData(cb_func) {
    $.ajax({
      url: "/ajax/objects.txt",
      success: cb_func
    });
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

$(document).ready(function() {
  getData(function( data ) {
    var columns = [];
    data = JSON.parse(data);
    columnNames = Object.keys(data.data[0]);
    for (var i in columnNames) {
      columns.push({data: columnNames[i], 
                    title: capitalizeFirstLetter(columnNames[i])});
    }
	$('#example').DataTable( {
		data: data.data,
		columns: columns
	} );
  });
  
} );
*/