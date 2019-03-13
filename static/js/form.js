"use-strict";

$(document).ready(function() {
  $('#spinner').hide();
  $('#bee-success').hide();

});




function submitForm() {
  $('#submit-form').on('submit', (evt) => {
    evt.preventDefault();

    $('#status').html('<i>Loading...</i>');
    $("#load").attr("src", "/static/images/load.gif");


    const formInputs = {
      'file': $('#file').val(),
      'health': $('#health').val(),
      'zipcode': $('#zipcode').val()

    };


  $.post('/upload-success', formInputs, (results) => {
      alert(results);

      // We know it is finished
      $('#status').html('');  // remove "loading" message

      $('#load').attr("src", "");

    });
  });
}




submitForm();
