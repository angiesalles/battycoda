/*!
 * Maisonnette-admin v1.3.2
 * https://foxythemes.net
 *
 * Copyright (c) 2019 Foxy Themes
 */

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
