var App = (function () {
  'use strict';

  App.emailCompose = function( ){

    //Select2 Tags
    $(".tags").select2({tags: 0,width: '100%'});
    
  };

  return App;
})(App || {});