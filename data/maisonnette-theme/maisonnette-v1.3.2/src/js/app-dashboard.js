var App = (function () {
  'use strict';
  
  App.dashboard = function( ){

    // Develop Chart
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
        tooltip:{
          show: true,
          cssClass: "tooltip-chart",
          content: "<div class='content-chart'> <span> %s </span> <div class='label'> <div class='label-x'> %x.0 </div> - <div class='label-y'> %y.0 </div> </div></div>",
          defaultTheme: false
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

      widget_tooltipPosition('develop-chart', 65);
    }

    // Counter
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

    // Week Chart
    function widget_week_chart(){

      var color1 = App.color.primary;

      var plot_statistics = $.plot($("#week-chart"), [{
        data: [
          [1.0, 25],
          [1.5, 25],
          [1.8, 29],
          [2.0, 27],
          [3.0, 37],
          [3.3, 33],
          [3.6, 40],
          [3.8, 43],
          [4, 57],
          [4.7, 62],
          [5.2, 56],
          [5.6, 64],
          [6, 65],
          [6.3, 70],
          [6.5, 65],
          [6.7, 67],
          [7, 64],

        ],
        label: "Page Views"
      }
      ], {
        series: {
          lines: {
            show: true,
            lineWidth: 4, 
            fill: false
          },
          points: {
            show: false
          },
          shadowSize: 0
        },
        legend:{
          show: false
        },
        grid: {
          margin: {
            left: 30,
            right: 30,
            top: 20,
            botttom: 40
          },
          labelMargin: 0,
          axisMargin: 500,
          hoverable: true,
          clickable: true,
          tickColor: "rgba(0,0,0,0.15)",
          borderWidth: 0
        },
        tooltip:{
          show: true,
          cssClass: "tooltip-chart",
          content: "<div class='content-chart'> <span> %s </span> <div class='label'> <div class='label-x'> %x.0 </div> - <div class='label-y'> %y.0 </div> </div></div>",
          defaultTheme: false
        },
        colors: [color1],
        xaxis: {
          min: 1.0,
          max: 7.0,
          mode: "time",
          ticks: [ [1.0,"Sun"], [2.0,"Mon"], [3.0,"Tue"], [4.0,"Wed"], [5.0,"Thu"], [6.0,"Fri"], [7.0,"Sat"] ],
          timeformat: "%a"
        },
        yaxis: {
           tickFormatter: function(){
            return '';
          },
          min: 0,
          max: 80,
          ticks: 8
        }
      });

      widget_tooltipPosition('week-chart', 65);
    }

    // New Users
    function widget_users_chart(){
      var data = [
        { data: 45, label: "Facebook"},
        { data: 25, label: "Instagram"},
        { data: 20, label: "Twitter"},
        { data: 10, label: "Google"}
      ]; 

      var color1 = tinycolor( App.color.primary ).brighten( 9 ).toString();
      var color2 = tinycolor( App.color.primary ).lighten( 13 ).toString();
      var color3 = tinycolor( App.color.primary ).lighten( 20 ).toString();
      var color4 = tinycolor( App.color.primary ).lighten( 27 ).toString();

      $.plot('#users-chart', data, {
        series: {
          pie: {
            show: true,
            innerRadius: 0.7,
            shadow:{
              top: 5,
              left: 15,
              alpha:0.3
            },
            stroke:{
              width:0
            },
            label: {
                show: false,
                formatter: function (label, series) {
                    return '<div style="font-size:12px;text-align:center;padding:2px;color:#333;">' + label + '</div>';
                }
            },
            highlight:{
              opacity: 0.08
            }
          }
        },
        grid: {
          hoverable: true,
          clickable: true
        },
        tooltip:{
          show: true,
          cssClass: "tooltip-chart",
          content: "<div class='content-chart arrow-none'> <span> %s </span> <div class='label'> <div class='label-x'> %x.0% </div> </div></div>",
          defaultTheme: false
        },
        colors: [color1, color2, color3, color4],
        legend: {
          show: false
        }
      });
    }

    // Ads Chart
    function widget_ads_chart(){

      var color1 = tinycolor( App.color.primary ).lighten( 7 ).toString();
      var color2 = App.color.primary;

      var data = [
        [1, 60],
        [2, 90],
        [3, 35],
        [4, 70],
        [5, 40]
      ];

      var data2 = [
        [1, 0],
        [2, 30],
        [3, 80],
        [4, 30],
        [5, 65]
      ];

      var plot_statistics = $.plot("#ads-chart", 
        [
        {
          data: data,
          canvasRender: true,
          showLabels: true, label: "Google ads", labelPlacement: "below"
        },
        {
          data: data2,
          canvasRender: true,
          showLabels: true, label: "Facebook", labelPlacement: "below"
        }
        ], {
        series: {
          lines: {
            show: true,
            lineWidth: 0, 
            fill: true,
            fillColor: { colors: [{ opacity: 1 }, { opacity: 1}] }
          },
          fillColor: "rgba(0, 0, 0, 1)",
          shadowSize: 0,
          curvedLines: {
            apply: true,
            active: true,
            monotonicFit: true
          }
        },
        legend:{
          show: true,
          position: "nw",
          background: "green",
          container: $("#ads-chart-legend")
        },
        grid: {
          show:false,
          hoverable: true,
          clickable: true
        },
        tooltip:{
          show: true,
          cssClass: "tooltip-chart",
          content: "<div class='content-chart'> <span> %s </span> <div class='label'> <div class='label-x'> %x.0 </div> - <div class='label-y'> %y.0 </div> </div></div>",
          defaultTheme: false
        },
        colors: [color1, color2],
        xaxis: {
          autoscaleMargin: 0,
          ticks: 11,
          tickDecimals: 0
        },
        yaxis: {
          autoscaleMargin: 0.5,
          ticks: 5,
          tickDecimals: 0
        }
      });

      widget_tooltipPosition('ads-chart', 65);
    }

    // Earnings Chart
    function widget_earnings_chart(){

      var color1 = tinycolor( App.color.light ).darken( 15 ).toString();

      var data = [
        [1, 40],
        [2, 60],
        [3, 30],
        [4, 80],
        [5, 60]
      ];

      var plot_statistics = $.plot("#earnings-chart", 
        [
        {
          data: data,
          canvasRender: true,
          showLabels: false
        }
        ], {
        series: {
          lines: {
            show: true,
            fill: true,
            lineWidth: 4, 
            fillColor: { colors: [{ opacity: 0.4 }, { opacity: 0.4}] }
          },
          fillColor: "rgba(0, 0, 0, 1)",
          shadowSize: 0,
          curvedLines: {
            apply: true,
            active: true,
            monotonicFit: true
          }
        },
        legend:{
          show: false
        },
        grid: {
          show:false,
          hoverable: true
        },
        tooltip:{
          show: true,
          cssClass: "tooltip-chart",
          content: "<div class='content-chart'> <div class='label'> <div class='label-x'> %x.0 </div> - <div class='label-y'> %y.0 </div> </div></div>",
          defaultTheme: false
        },
        colors: [color1],
        xaxis: {
          autoscaleMargin: 0,
          ticks: 11
        },
        yaxis: {
          ticks: 9
        }
      });

      widget_tooltipPosition('earnings-chart', 45);
    }

    //Positioning tooltip
    function widget_tooltipPosition(id, top){
      $('#'+id).bind("plothover", function (event, pos, item) {
        var widthToolTip = $('.tooltip-chart').width();
        if(item){
          $(".tooltip-chart")
            .css({top: item.pageY - top, left: item.pageX - ((widthToolTip / 2)-2)})
            .fadeIn(200);
        }else{
          $(".tooltip-chart").hide();
        }
      });
    }

    widget_develop_chart();
    widget_countUp();
    widget_week_chart();
    widget_users_chart();
    widget_ads_chart();
    widget_earnings_chart();

  };

  return App;
})(App || {});