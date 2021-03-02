$(document).ready(function() {
    //$('.mySelect2').select2();
    $(".mySelect2").select2({
        theme: "classic"
    });
});

function submit2() {
    var data = $('.mySelect2').select2('data');
    data.forEach(item => {
        console.log(item.id, item.text);
     });
};

/*
// https://stackoverflow.com/questions/16626735/how-to-loop-through-an-array-containing-objects-and-access-their-properties
  yourArray.forEach(arrayItem => {
      var x = arrayItem.prop1 + 2;
      console.log(x);
  });*/

/*
$(".ajax").select2({
  ajax: {
    url: "/filter",
    dataType: 'json',
    delay: 250,
    data: function (params) {
      return {
        q: params.term, // search term
        page: params.page
      };
    },
    processResults: function (data, params) {
      // parse the results into the format expected by Select2
      // since we are using custom formatting functions we do not need to
      // alter the remote JSON data, except to indicate that infinite
      // scrolling can be used
      params.page = params.page || 1;

      return {
        results: data.items,
        pagination: {
          more: (params.page * 30) < data.total_count
        }
      };
    },
    cache: true
  },
  placeholder: 'Search for a repository',
  minimumInputLength: 1
});
*/