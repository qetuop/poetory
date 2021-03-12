function populateTable(data) {

}

function filterData() {
    $.ajax({
        url: "/filterdata",
        success: function(data) {
            var columns = [];

            visibleColumnNames = Object.assign(data.visible)
            //console.log(visibleColumnNames)

            //columnNames = Object.keys(data.items[0]);
            //console.log(columnNames)

             /*
             for (var i in columnNames) {
                //console.log(columnNames[i])
                columns.push({
                    data: columnNames[i],
                    title: columnNames[i],
                    visible: visibleColumnNames.includes(columnNames[i])
                });
            }
            */

            for (var i in visibleColumnNames) {
                //console.log(columnNames[i])
                columns.push({
                    data: visibleColumnNames[i],
                    title: visibleColumnNames[i],
                    visible: true,
                    defaultContent: ""
                });
            }

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

        } // success
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


function submit2() {
    var data = $('.mySelect2').select2('data');
    data.forEach(item => {
        console.log(item.id, item.text);
     });

};


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