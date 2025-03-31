var App = (function () {
  'use strict';
  
  App.profile = function( ){

    //Develop Chart
    function widget_develop_chart(){

      var color1 = App.color.primary;
      var color2 = tinycolor( App.color.primary ).brighten( 5 ).saturate(15);
      var color3 = tinycolor( App.color.primary ).brighten( 15 ).saturate(15);

      var data_com3 = [
        [1, 10],
        [2, 30],
        [3, 25],
        [4, 30],
        [5, 35],
        [6, 15],
        [7, 10],
        [8, 15]
      ];
      var data_com2 = [
        [1, 20],
        [2, 25],
        [3, 30],
        [4, 35],
        [5, 55],
        [6, 42],
        [7, 15],
        [8, 25]
      ];
      var data_com = [
        [1, 30],
        [2, 10],
        [3, 10],
        [4, 15],
        [5, 0],
        [6, 47],
        [7, 65],
        [8, 10]
      ];

      var plot_statistics = $.plot($("#develop-chart"), [{
        data: data_com, showLabels: true, label: "Purchases", labelPlacement: "below", canvasRender: true, cColor: "#FFFFFF" 
      },{
        data: data_com2, showLabels: true, label: "Plans", labelPlacement: "below", canvasRender: true, cColor: "#FFFFFF" 
      },{
        data: data_com3, showLabels: true, label: "Services", labelPlacement: "below", canvasRender: true, cColor: "#FFFFFF" 
      }],
      {
        series: {
          lines: {
            show: true,
            lineWidth: 0.5, 
            fill: true,
            fillColor: { colors: [{ opacity: 1 }, { opacity: 1}] },
          },
          fillColor: "rgba(0, 0, 0, 1)",
          points: {
            show: false,
            fill: true
          },
          shadowSize: 0
        },
        legend:{
          show: true,
          position: "nw",
          noColumns: 0,
          background: "green",
          container: $("#develop-chart-legend")
        },
        grid: {
          show: false,
          margin: {
            top: -20,
            bottom: 0,
            left: 0,
            right: 0,
          },
          labelMargin: 0,
          axisMargin: 0,
          hoverable: true,
          clickable: true,
          tickColor: "rgba(0,0,0,0)",
          borderWidth: 0,
          minBorderMargin: 0
        },
        colors: [color1, color2, color3],
        xaxis: {
          autoscaleMargin: 0,
          ticks: 11,
          tickDecimals: 0
        },
        yaxis: {
          autoscaleMargin: 0.2,
          ticks: 5,
          tickDecimals: 0
        }
      });
    }

    function widget_countDown(){

      var threeHours = new Date().getTime() + 100060000;

      $("#user-countdown").countdown(threeHours, function(event) {
        $(this).text(
          event.strftime('%H %M %S')
        );

        var $this = $(this).html(event.strftime(''
          + '<div class="time-component"><span class="time-counter">%H</span><span class="time-component-title"> Hours </span></div>'
          + '<div class="time-component"><span class="time-counter">%M</span><span class="time-component-title"> Minutes </span></div>'
          + '<div class="time-component"><span class="time-counter">%S</span><span class="time-component-title"> Seconds </span> </div>')
        );
      });
    }

    //Counter
    function widget_countUp(){

      $('[data-toggle="counter"]').each(function(i, e){
        var _el       = $(this);
        var prefix    = '';
        var suffix    = '';
        var start     = 0;
        var end       = 0;
        var decimals  = 0;
        var duration  = 2.5;

        if( _el.data('prefix') ){ prefix = _el.data('prefix'); }

        if( _el.data('suffix') ){ suffix = _el.data('suffix'); }

        if( _el.data('start') ){ start = _el.data('start'); }

        if( _el.data('end') ){ end = _el.data('end'); }

        if( _el.data('decimals') ){ decimals = _el.data('decimals'); }

        if( _el.data('duration') ){ duration = _el.data('duration'); }

        var count = new CountUp(_el.get(0), start, end, decimals, duration, { 
          suffix: suffix,
          prefix: prefix,
        });

        count.start();
      });
    }

    //Calendar Widget
    function calendar_widget(){
      var widget = $(".widget-calendar");
      var calNotes = $(".cal-notes", widget);
      var calNotesDay = $(".day", calNotes);
      var calNotesDate = $(".date", calNotes);

      //Calculate the weekday name
      var d = new Date();
      var weekday = new Array(7);
      weekday[0]=  "Sunday";
      weekday[1] = "Monday";
      weekday[2] = "Tuesday";
      weekday[3] = "Wednesday";
      weekday[4] = "Thursday";
      weekday[5] = "Friday";
      weekday[6] = "Saturday";

      var weekdayName = weekday[d.getDay()];

      calNotesDay.html( weekdayName );

      //Calculate the month name
      var month = new Array();
      month[0] = "January";
      month[1] = "February";
      month[2] = "March";
      month[3] = "April";
      month[4] = "May";
      month[5] = "June";
      month[6] = "July";
      month[7] = "August";
      month[8] = "September";
      month[9] = "October";
      month[10] = "November";
      month[11] = "December";

      var monthName = month[d.getMonth()];
      var monthDay = d.getDate();

      calNotesDate.html( monthName + " " + monthDay);

      if (typeof jQuery.ui != 'undefined') {
        $( ".ui-datepicker" ).datepicker({
          onSelect: function(s, o){
            var sd = new Date(s);
            var weekdayName = weekday[sd.getDay()];
            var monthName = month[sd.getMonth()];
            var monthDay = sd.getDate();

            calNotesDay.html( weekdayName );
            calNotesDate.html( monthName + " " + monthDay);
          }
        });
      }
    }

    widget_develop_chart();
    widget_countDown();
    widget_countUp();
    calendar_widget();

  };

  return App;
})(App || {});