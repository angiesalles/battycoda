/*!
 * Maisonnette-admin v1.3.2
 * https://foxythemes.net
 *
 * Copyright (c) 2019 Foxy Themes
 */

var App = (function () {
  'use strict';
  
  App.uiNotifications = function( ){  
    
    $('#not-basic').click(function(){
      $.gritter.add({
        title: 'MiguelMich new msg!',
        text: "You have a new Thomas message, let's checkout your inbox.",
        image: App.conf.assetsPath + '/' +  App.conf.imgPath + '/avatar.jpg',
        time: '',
        class_name: 'gritter-basic'
      });
      return false;
    });
    
    $('#not-theme').click(function(){
      $.gritter.add({
        title: 'Welcome home!',
        text: 'You can start your day checking the new messages.',
        image: App.conf.assetsPath + '/' +  App.conf.imgPath + '/avatar.jpg',
        class_name: 'gritter-theme',
        time: '',
      });
      return false;
    });
    
    $('#not-sticky').click(function(){
      $.gritter.add({
        title: 'Sticky Note',
        text: "Your daily goal is 130 new code lines, don't forget to update your work.",
        image: App.conf.assetsPath + '/' +  App.conf.imgPath + '/slack_logo.png',
        class_name: 'gritter-sticky',
        sticky: true, 
        time: ''
      });
      return false;
    });
    
    $('#not-text').click(function(){
      $.gritter.add({
        title: 'Just Text',
        text: 'This is a simple Gritter Notification. Etiam efficitur efficitur nisl eu dictum, nullam non orci elementum.',
        class_name: 'gritter-clean',
        time: ''
      });
      return false;
    });

    /*Positions*/
    $('#not-tr').click(function(){
      $.extend($.gritter.options, { position: 'top-right' });

      $.gritter.add({
        title: 'Top Right',
        text: 'This is a simple Gritter Notification. Etiam efficitur efficitur nisl eu dictum, nullam non orci elementum',
        class_name: 'gritter-clean'
      });

      return false;
    });
    
    $('#not-tl').click(function(){
      $.extend($.gritter.options, { position: 'top-left' });

      $.gritter.add({
        title: 'Top Left',
        text: 'This is a simple Gritter Notification. Etiam efficitur efficitur nisl eu dictum, nullam non orci elementum',
        class_name: 'gritter-clean'
      });

      return false;
    });
    
    $('#not-bl').click(function(){

      $.extend($.gritter.options, { position: 'bottom-left' });

      $.gritter.add({
        title: 'Bottom Left',
        text: 'This is a simple Gritter Notification. Etiam efficitur efficitur nisl eu dictum, nullam non orci elementum',
        class_name: 'gritter-clean'
      });

      return false;
    });
    
    $('#not-br').click(function(){

      $.extend($.gritter.options, { position: 'bottom-right' });
      
      $.gritter.add({
        title: 'Bottom Right',
        text: 'This is a simple Gritter Notification. Etiam efficitur efficitur nisl eu dictum, nullam non orci elementum',
        class_name: 'gritter-clean'
      });

      return false;
    });

    /*Social Gritters*/
    $('#not-facebook').click(function(){
      $.gritter.add({
        title: 'You have comments!',
        text: 'You can start your day checking the new messages.',
        icon: true,
        class_name: 'gritter-social facebook'
      });
      return false;
    });
    
    $('#not-twitter').click(function(){
      $.gritter.add({
        title: 'You have new followers!',
        text: 'You can start your day checking the new messages.',
        icon: true,
        class_name: 'gritter-social twitter'
      });
      return false;
    });
    
    $('#not-google-plus').click(function(){
      $.gritter.add({
        title: 'You have new +1!',
        text: 'You can start your day checking the new messages.',
        icon: true,
        class_name: 'gritter-social google-plus'
      });
      return false;
    });
    
    $('#not-dribbble').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social dribbble'
      });
      return false;
    });
    
    $('#not-flickr').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social flickr'
      });
      return false;
    });
    
    $('#not-linkedin').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social linkedin'
      });
      return false;
    });
    
    $('#not-youtube').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social youtube'
      });
      return false;
    });
    
    $('#not-pinterest').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social pinterest'
      });
      return false;
    });  
    
    $('#not-github').click(function(){
      $.gritter.add({
        title: 'You have new forks!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social github'
      });
      return false;
    });    
    
    $('#not-tumblr').click(function(){
      $.gritter.add({
        title: 'You have new comments!',
        text: 'You can start your day checking the new comments.',
        icon: true,
        class_name: 'gritter-social tumblr'
      });
      return false;
    });

    /*gritter states colors*/
    $('#not-primary').click(function(){
      $.gritter.add({
        title: 'Primary',
        text: 'This is a simple Gritter Notification.',
        class_name: 'gritter-color primary'
      });
    });
    
    $('#not-info').click(function(){
      $.gritter.add({
        title: 'Info',
        text: 'This is a simple Gritter Notification.',
        class_name: 'gritter-color info'
      });
    });
    
    $('#not-warning').click(function(){
      $.gritter.add({
        title: 'Warning',
        text: 'This is a simple Gritter Notification.',
        class_name: 'gritter-color warning'
      });
    });
    
    $('#not-danger').click(function(){
      $.gritter.add({
        title: 'Danger',
        text: 'This is a simple Gritter Notification.',
        class_name: 'gritter-color danger'
      });
    });

    /*Alt gritter-Colors*/
    
    $('#not-dark').click(function(){
      $.gritter.add({
        title: 'Dark Color',
        text: 'This is a simple Gritter Notification.',
        class_name: 'gritter-color dark'
      });
    });

  };

  return App;
})(App || {});
