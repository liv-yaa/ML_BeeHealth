$('#status').html('<i>Loading...</i>');

$.get('/long-ajax-call', function (response) {
  // do whatever you want to normally do with response

  $('#status').empty();  // remove "loading" message
});