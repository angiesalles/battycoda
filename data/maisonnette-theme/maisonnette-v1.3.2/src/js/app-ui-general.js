var App = (function () {
  'use strict';
  
  App.uiGeneral = function( ){   
    
    /* Prevents dynamic positioning */
    $('.card-body [data-toggle="dropdown"]').on('click', function(e){
      e.stopPropagation();
    });
    
  };

  return App;
})(App || {});
