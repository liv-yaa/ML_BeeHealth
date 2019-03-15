"use-strict";

$(document).ready(function() {
  $('#spinner').hide();
  $('#bee-success').toggle();

});




function submitForm() {
  $('#submit-form').on('submit', (evt) => {
    evt.preventDefault();

    // $('#status').html('<i>Loading...</i>');
    // $("#load").attr("src", "/static/images/load.gif");

    $('#spinner').toggle();
    const formInputs = {
      'file': $('#file').val(),
      'health': $('#health').val(),
      'zipcode': $('#zipcode').val()

    };


  $.post('/upload-success', formInputs, (results) => {
      alert(results);
      $('#spinner').toggle();
      // We know it is finished
      // $('#status').html('');  // remove "loading" message

      // $('#load').attr("src", "");

    });
  });
}




submitForm();
