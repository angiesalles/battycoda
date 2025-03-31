/*!
 * Maisonnette-admin v1.3.2
 * https://foxythemes.net
 *
 * Copyright (c) 2019 Foxy Themes
 */

var App = (function () {
	'use strict';

	App.ChartJs = function( ){

    var randomScalingFactor = function() {
      return Math.round(Math.random() * 100);
    };

		function lineChart(){
			//Set the chart colors
      var color1 = tinycolor( App.color.primary );
			var color2 = tinycolor( App.color.primary ).lighten( 22 );

      //Get the canvas element
			var ctx = document.getElementById("line-chart");
			
			var lineChartData = {
	      labels: ["January", "February", "March", "April", "May", "June", "July"],
	      datasets: [{
	        label: "My First dataset",
	        borderColor: color1.toString(),
	        backgroundColor: color1.setAlpha(.8).toString(),
	        data: [randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor()]
	      }, {
	        label: "My Second dataset",
	        borderColor: color2.toString(),
	        backgroundColor: color2.setAlpha(.5).toString(),
	        data: [randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor()]
	      }]
	    };

	    var line = new Chart(ctx, {
        type: 'line',
        data: lineChartData
      });
		}

		function barChart(){
			//Set the chart colors
      var color1 = tinycolor( App.color.primary );
			var color2 = tinycolor( App.color.primary ).lighten( 22 );

      //Get the canvas element
			var ctx = document.getElementById("bar-chart");
			
			var data = {
	      labels: ["January", "February", "March", "April", "May", "June", "July"],
	      datasets: [{
	        label: "Credit",
	        borderColor: color1.toString(),
	        backgroundColor: color1.setAlpha(.8).toString(),
	        data: [randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor()]
	      }, {
	        label: "Debit",
	        borderColor: color2.toString(),
	        backgroundColor: color2.setAlpha(.5).toString(),
	        data: [randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor(), randomScalingFactor()]
	      }]
	    };

	    var bar = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
          elements: {
            rectangle: {
              borderWidth: 2,
              borderColor: 'rgb(0, 255, 0)',
              borderSkipped: 'bottom'
            }
          },
        }
      });
		}

		function radarChart(){
			//Set the chart colors
			var color1 = tinycolor( App.color.primary ).lighten( 30 );
      var color2 = tinycolor( App.color.primary );

      //Get the canvas element
			var ctx = document.getElementById("radar-chart");
			
			var data = {
			  labels: ["Eating", "Drinking", "Sleeping", "Designing", "Coding", "Cycling", "Running"],
			  datasets: [
			    {
			      label: "First Year",
			      backgroundColor: color1.setAlpha(.3).toString(),
			      borderColor: color1.toString(),
			      pointBackgroundColor: color1.toString(),
			      pointBorderColor: "#fff",
			      pointHoverBackgroundColor: "#fff",
			      pointHoverBorderColor: color1.toString(),
			      data: [65, 59, 90, 81, 56, 55, 40]
			    },
			    {
			      label: "Second Year",
			      backgroundColor: color2.setAlpha(.4).toString(),
			      borderColor: color2.toString(),
			      pointBackgroundColor: color2.toString(),
			      pointBorderColor: "#fff",
			      pointHoverBackgroundColor: "#fff",
			      pointHoverBorderColor: color2.toString(),
			      data: [28, 48, 40, 19, 96, 27, 100]
			    }
			  ]
			};

	    var radar = new Chart(ctx, {
        type: 'radar',
        data: data
      });
		}

		function polarChart(){
			//Set the chart colors
			var color1 = App.color.primary;
			var color2 = tinycolor( App.color.primary ).lighten( 10 ).toString();
			var color3 = tinycolor( App.color.primary ).lighten( 20 ).toString();
			var color4 = tinycolor( App.color.primary ).lighten( 30 ).toString();
      var color5 = tinycolor( App.color.primary ).lighten( 40 ).toString();

      //Get the canvas element
			var ctx = document.getElementById("polar-chart");
			
			var data = {
		    datasets: [{
	        data: [11,16,14,7,14],
	        backgroundColor: [
            color1,
            color2,
            color3,
            color4,
            color5
	        ],
	        label: 'My dataset'
		    }],
		    labels: [
	        "January",
	        "February",
	        "March",
	        "April",
	        "May"
		    ]
			};

	    var polar = new Chart(ctx, {
        type: 'polarArea',
        data: data
      });
		}

		function pieChart(){
			//Set the chart colors
			var color1 = App.color.primary;
			var color2 = tinycolor( App.color.primary ).lighten( 12 ).toString();
			var color3 = tinycolor( App.color.primary ).lighten( 22 ).toString();

      //Get the canvas element
			var ctx = document.getElementById("pie-chart");
			
			var data = {
			  labels: [
			    "Red",
			    "Blue",
			    "Yellow"
			  ],
			  datasets: [
			    {
			      data: [300, 50, 100],
			      backgroundColor: [
			        color1,
			        color2,
			        color3
			      ],
			      hoverBackgroundColor: [
			        color1,
			        color2,
			        color3
			      ]
			  	}]
			};

	    var pie = new Chart(ctx, {
        type: 'pie',
        data: data
      });
		}

		function donutChart(){
			//Set the chart colors
			var color1 = App.color.primary;
			var color2 = tinycolor( App.color.primary ).lighten( 12 ).toString();
			var color3 = tinycolor( App.color.primary ).lighten( 22 ).toString();

      //Get the canvas element
			var ctx = document.getElementById("donut-chart");
			
			var data = {
			  labels: [
			    "Red",
			    "Blue",
			    "Yellow"
			  ],
			  datasets: [
			    {
			      data: [300, 50, 100],
			      backgroundColor: [
			        color1,
			        color2,
			        color3
			      ],
			      hoverBackgroundColor: [
			        color1,
			        color2,
			        color3
			      ]
			  	}]
			};

	    var pie = new Chart(ctx, {
        type: 'doughnut',
        data: data
      });
		}

		lineChart();
		barChart();
		radarChart();
		polarChart();
		pieChart();
		donutChart();
	};

	return App;
})(App || {});