var App = (function () {

  var config = {//Basic Config
    animate: false,
    popover: true,
    assetsPath: 'assets',
    imgPath: 'img',
    jsPath: 'js',
    libsPath: 'lib',
    SlideSpeed: 200,
    megaMenuClass: 'mai-mega-menu-container',
    megaMenuColumnClass: 'mai-mega-menu-column',
    megaMenuSectionClass: 'mai-mega-menu-section',
    navTabsClass: 'mai-nav-tabs',
    subNavClass: 'mai-sub-nav'
  };

  var megaMenu, navTabs, colors = {};
  var scrollers = {};
  var iconsNav, notificationsDiv, messagesDiv, asideDiv;

  var ps_top_messages_scroll,
      ps_notifications_scroll,
      ps_aside_scroll;

  // Refresh scroller
  function updateScroller(ps_object){
    ps_object.update();
  }

  // Destroy scroller
  function destroyScroller(ps_object){
    ps_object.destroy();
  }

  // Initialize scroller
  function initScroller(domObject) {
    return new PerfectScrollbar(domObject[0], {
      wheelPropagation: false
    });
  }

  // No childs check
  function noChildsCheck(tab) {
    // Check if the tab is open
    if( tab.hasClass('open') ) {
      var subNav = $('.' + config.subNavClass, tab);
      var subHeader = tab.parents('.mai-sub-header');

      // If subNav has children
      if(subNav.length) {
        subHeader.removeClass('mai-sub-header--no-child')
      } else {
        subHeader.addClass('mai-sub-header--no-child')
      }
    } else {
      return false;
    }
  }

  // Main tabs active state sync
  function tabSync() {
    var tabs = $( '.navbar-nav > .nav-item', navTabs );
    var openTabs = tabs.filter( '.open' );

    if( !openTabs.length ) { // Si no hay tabs abiertas
      tabs.filter( ':first-child' ).addClass( 'open' );
    }

    noChildsCheck(tabs.filter('.open'));
  }

  // Sub navigation interaction
  function subNav() {
    $('.nav-link, .dropdown-item', navTabs).on('click',function( e ){
      var _this = $( this );
      var parent = _this.parent();
      var openElements = parent.siblings( '.open' );
      var subNav = _this.next( '.' + config.subNavClass );
      var slideSpeed = config.SlideSpeed;

      function closeSubMenu( subMenu ){
        var _parent = $( subMenu ).parent();
        var openChildren = $( '.nav-item.open, .' + config.megaMenuSectionClass + '.open', _parent );

        subMenu.slideUp({ duration: slideSpeed, complete: function(){
          _parent.removeClass( 'open' );
          openChildren.removeClass( 'open' );
          $( this ).removeAttr( 'style' );
        }});
      }

      function openSubMenu( subMenu ){
        var _parent = subMenu.parent();
        var openSubMenus = false;

        // Get the open sub menus
        openSubMenus = _parent.siblings( '.open' );

        if( _parent.hasClass( config.megaMenuSectionClass ) ) {
          megaColumn = _parent.parent();
          openSubMenus = openSubMenus.add( megaColumn.siblings().find( '.' + config.megaMenuSectionClass + '.open' ) );
        }
        // If there are open sub menus close them
        if( openSubMenus ) {
          closeSubMenu( $( '> .' + config.subNavClass, openSubMenus ) );
        }

        subMenu.slideDown({ duration: slideSpeed, complete: function(){
          _parent.addClass( 'open' );
          $( this ).removeAttr( 'style' );
        }});
      }

      // Check if the event is fired from mobile
      if( $.isSm() ) {
        if( subNav.length ) {
          if( parent.hasClass( 'open' ) ) {
            closeSubMenu( subNav );
          } else {
            openSubMenu( subNav );
          }
          e.preventDefault();
        }

        // Stop default bootstrap dropdown interaction
        e.stopPropagation();
      } else if ( parent.parent().hasClass('navbar-nav') ) {
        if ( subNav.length ) {
          var subHeader = parent.parents('.mai-sub-header');
          openElements.removeClass( 'open' );
          parent.addClass( 'open' );
          if (subHeader.hasClass('mai-sub-header--no-child')) {
            subHeader.removeClass('mai-sub-header--no-child')
          }
          e.preventDefault();
        }
      }
    });

    // Sync tabs when resize between mobile and desktop resolutions
    $(window).resize(function() {
      waitForFinalEvent(function() {
        if( !$.isSm() ) {
          tabSync();
        }
      }, 100, "sync_tabs");
    });
  }

  // Get the template css colors into js vars
  function getColor( c ){
    var tmp = $("<div>", { class: c }).appendTo("body");
    var color = tmp.css("background-color");
    tmp.remove();

    return color;
  }

  // Wait for final event on window resize
  var waitForFinalEvent = (function () {
    var timers = {};
    return function (callback, ms, uniqueId) {
      if (!uniqueId) {
        uniqueId = "x1x2x3x4";
      }
      if (timers[uniqueId]) {
        clearTimeout (timers[uniqueId]);
      }
      timers[uniqueId] = setTimeout(callback, ms);
    };
  })();

  // Scroll plugin init
  function scrollerInit(){
    if (notificationsDiv.length) {
      ps_notifications_scroll = initScroller(notificationsDiv);
    }

    if (messagesDiv.length) {
      ps_top_messages_scroll = initScroller(messagesDiv);
    }
  }

  function initAsidePS() {
    var pas = asideDiv;
    if( !$.isSm() ) {
      ps_aside_scroll = initScroller(asideDiv);
    }
    $(window).resize(function () {
      if( $.isSm() ) {
        if (typeof ps_aside_scroll !== "undefined") {
          destroyScroller(ps_aside_scroll);
        }
      } else {
        if( pas.hasClass('ps') ) {
          updateScroller(ps_aside_scroll);
        } else {
          if (typeof ps_aside_scroll === "undefined" || !ps_aside_scroll || !ps_aside_scroll.nodeName) {
            ps_aside_scroll = initScroller(asideDiv);
          }
        }
      }
    });
  }

  return {
    conf: config,
    color: colors,
    scroller: scrollers,

    init: function (options) {

      iconsNav = $('.mai-icons-nav');
      notificationsDiv = $('.mai-scroller-notifications');
      messagesDiv = $('.mai-scroller-messages');
      asideDiv = $('.mai-scroller-aside');

      megaMenu = document.getElementsByClassName( config.megaMenuClass );
      navTabs = document.getElementsByClassName( config.navTabsClass );

      // Extends basic config with options
      $.extend( config, options );

      // Page Aside
      if( asideDiv.length ) {
        initAsidePS();
      }

      // Scroller Plugin
      if( iconsNav.length ) {
        scrollerInit();
      }

      // Get colors
      colors.primary = getColor('clr-primary');
      colors.success = getColor('clr-success');
      colors.info    = getColor('clr-info');
      colors.warning = getColor('clr-warning');
      colors.danger  = getColor('clr-danger');
      colors.grey    = getColor('clr-grey');
      colors.dark    = getColor('clr-dark');
      colors.light   = getColor('clr-light');
      colors.black   = getColor('clr-black');

      // Get scrollers
      scrollers.notifications_scroll = ps_notifications_scroll;
      scrollers.top_messages_scroll = ps_top_messages_scroll;
      scrollers.aside_scroll = ps_aside_scroll;
      scrollers.updateScroller = updateScroller;
      scrollers.destroyScroller = destroyScroller;
      scrollers.initScroller = initScroller;

      // Navigation tabs
      tabSync();
      subNav();

      // Core public function
      // Prevent settings dropdown closes on click
      $(".mai-settings .dropdown-menu").on("click",function( e ){
        e.stopPropagation();
      });

      $('.mai-icons-nav .dropdown').on('shown.bs.dropdown', function () {
        if (notificationsDiv.length) {
          updateScroller(ps_notifications_scroll);
        }

        if (messagesDiv.length) {
          updateScroller(ps_top_messages_scroll);
        }
      });

      // Tooltips
      $('[data-toggle="tooltip"]').tooltip();

      // Popover
      $('[data-toggle="popover"]').popover();
    }
  };

})();
