var App = (function () {
  'use strict';

  App.formElements = function( ){ 

    // File input 
    $( '.inputfile' ).each( function(){
      var $input   = $( this ),
        $label   = $input.next( 'label' ),
        labelVal = $label.html();

      $input.on( 'change', function( e )
      {
        var fileName = '';

        if( this.files && this.files.length > 1 )
          fileName = ( this.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', this.files.length );
        else if( e.target.value )
          fileName = e.target.value.split( '\\' ).pop();

        if( fileName )
          $label.find( 'span' ).html( fileName );
        else
          $label.html( labelVal );
      });
    });

    //Select2
    $(".select2").select2({
      width: '100%'
    });
    
    //Select2 tags
    $(".tags").select2({tags: true, width: '100%'});

    //Bootstrap Slider
    $('.bslider').bootstrapSlider();

    //Date Picker
    $('#datepicker1').datepicker({
      autoclose: true
    });

    $('#datepicker2').datepicker({
      autoclose: true,
      todayHighlight: true,
    });

    $('#datepicker3').datepicker({
      startView: 1,
      autoclose: true
    });

    $('#datepicker4').datepicker({
      startView: 2,
      autoclose: true
    });

    $('#datepicker5').datepicker({
      startView: 3,
      autoclose: true
    });

    $('#datepicker6').datepicker({
      startView: 4,
      autoclose: true
    });

    $('#datepicker7').datepicker({
      todayBtn: "linked",
      autoclose: true
    });
  };

  return App;
})(App || {});
