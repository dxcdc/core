/**
 * Theme: Lahomes - Real Estate Admin Dashboard Template
 * Author: Techzaa
 * Module/App: Dashboard
 */

//
// sales_funnel
//
var options = {
  chart: {
    type: "area",
    height: 165,
    sparkline: {
      enabled: true,
    },
  },
  series: [
    {
      data: [25, 66, 41, 89, 63, 25, 44, 12, 36, 9, 54],
    },
  ],
  stroke: {
    width: 2,
    curve: "smooth",
  },
  fill: {
    type: "gradient",
    gradient: {
      shade: "light",
      type: "vertical",
      opacityFrom: 0.4,
      opacityTo: 0,
      stops: [0, 100],
    },
  },

  markers: {
    size: 0,
  },
  colors: ["#604ae3"],
  tooltip: {
    fixed: {
      enabled: false,
    },
    x: {
      show: false,
    },
    y: {
      title: {
        formatter: function (seriesName) {
          return "";
        },
      },
    },
    marker: {
      show: false,
    },
  },
};
var chart = new ApexCharts(document.querySelector("#sales_funnel"), options);
chart.render();

//
// Bar with Markers
//
var colors = ["#604ae3", "#f8ac59"];
var options = {
  series: [
   
    {
      name: "Property Sales",
      type: "bar",
      data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57,],
    },
    {
      name: "Profit Ratio",
      type: "line",
      data: [35, 35, 25, 25, 45, 45, 75, 75, 45, 45, 54, 54],
    },
  ],
  chart: {
    height: 330,
    type: "line",
    toolbar: {
      show: false,
    },
  },
  stroke: {
    curve: "straight",
    dashArray: [ 0, 8],
    width: [ 0, 2],
  },
  fill: {
    opacity: [ 4, 1],
  },
  markers: {
    size: [ 0, 0],
    strokeWidth: 2,
    hover: {
      size: 4,
    },
  },
  xaxis: {
    categories: [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ],
    axisTicks: {
      show: false,
    },
    axisBorder: {
      show: false,
    },
  },
  grid: {
    show: true,
    xaxis: {
      lines: {
        show: true,
      },
    },
    yaxis: {
      lines: {
        show: false,
      },
    },
    padding: {
      top: 0,
      right: -2,
      bottom: 15,
      left: 10,
    },
  },
  legend: {
    show: false,
  },
  plotOptions: {
    bar: {
      columnWidth: "30%",
      barHeight: "100%",
      borderRadius: 8,
    },
  },
  colors: colors,
  tooltip: {
    shared: true,
    y: [
      {
        formatter: function (y) {
          if (typeof y !== "undefined") {
            return y.toFixed(0);
          }
          return y;
        },
      },
      {
        formatter: function (y) {
          if (typeof y !== "undefined") {
            return "$" + y.toFixed(2) + "k";
          }
          return y;
        },
      },
      {
        formatter: function (y) {
          if (typeof y !== "undefined") {
            return y.toFixed(0) + " Sales";
          }
          return y;
        },
      },
    ],
  },
};

var chart = new ApexCharts(document.querySelector("#markers"), options);
chart.render();




//
// agent_goals
// 
var colors = ["#604ae3"];
var options = {
  chart: {
    height: 300,
    type: "radialBar",
  },
  plotOptions: {
    radialBar: {
      startAngle: -135,
      endAngle: 135,
      dataLabels: {
        name: {
          fontSize: "16px",
          color: undefined,
          offsetY: 120,
        },
        value: {
          offsetY: 76,
          fontSize: "22px",
          color: undefined,
          formatter: function (val) {
            return val + "%";
          },
        },
      },
      track: {
        background: "rgba(170,184,197, 0.4)",
        margin: 0,
      },
    },
  },
  fill: {
    gradient: {
      enabled: true,
      shade: "dark",
      shadeIntensity: 0.2,
      inverseColors: false,
      opacityFrom: 1,
      opacityTo: 1,
      stops: [0, 50, 65, 91],
    },
  },
  stroke: {
    dashArray: 4,
  },
  colors: colors,
  series: [75],
  labels: ["Achieved"],
  responsive: [
    {
      breakpoint: 380,
      options: {
        chart: {
          height: 280,
        },
      },
    },
  ],
};
var chart = new ApexCharts(
  document.querySelector("#agent_goals"),
  options
);
chart.render();



// VectorMap

class VectorMap {
  initWorldMapMarker() {
    const map = new jsVectorMap({
      map: "world",
      selector: "#world-map-markers",
      zoomOnScroll: true,
      zoomButtons: false,
      markersSelectable: true,
      markers: [
        { name: "Canada", coords: [56.1304, -106.3468] },
        { name: "Brazil", coords: [-14.235, -51.9253] },
        { name: "Russia", coords: [61, 105] },
        { name: "China", coords: [35.8617, 104.1954] },
        { name: "United States", coords: [37.0902, -95.7129] },
      ],
      markerStyle: {
        initial: { fill: "#7f56da" },
        selected: { fill: "#1bb394" },
      },
      labels: {
        markers: {
          render: (marker) => marker.name,
        },
      },
      regionStyle: {
        initial: {
          fill: "rgba(169,183,197, 0.3)",
          fillOpacity: 1,
        },
      },
    });
  }

  init() {
    this.initWorldMapMarker();
  }
}

document.addEventListener("DOMContentLoaded", function (e) {
  new VectorMap().init();
});
