"use-strict";

$(document).ready(() => {
  $('#spinner').hide();
  $('#bee-success').toggle();
});


function submitForm() {
  $('#submit-form').on('submit', (evt) => {
    $('#spinner').toggle();
  });

  //   const formInputs = {
  //     'file': $('#file').val(),
  //     'health': $('#health').val(),
  //     'zipcode': $('#zipcode').val()
  //   };


  //   $.post('/upload-success', formInputs, (results) => {
  //     alert(results);
  //     $('#spinner').toggle();
  //   });
  // });
}

// submitForm();
