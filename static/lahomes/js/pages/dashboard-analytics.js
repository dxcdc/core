/**
 * Theme: Lahomes - Real Estate Admin Dashboard Template
 * Author: Techzaa
 * Module/App: Dashboard
 */

// total_customers

var options = {
    chart: {
        height: 95,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "40%",
            startingShape: "rounded",
            endingShape: "rounded",
            borderRadius: 4,
            distributed: !0,
        },
    },
    grid: {
        show: !1,
        padding: {
            top: -20,
            bottom: -10,
            left: 0,
            right: 0
        },
    },
    colors: ["#eef2f7", "#eef2f7", "#604ae3", "#eef2f7"],
    dataLabels: {
        enabled: !1
    },
    series: [{
        name: 'Property Listing',
        data: [40, 50, 65, 40, 40, 65, 40]
    }],
    legend: {
        show: !1
    },
    xaxis: {
        categories: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
        axisBorder: {
            show: !1
        },
        axisTicks: {
            show: !1
        },
    },
    yaxis: {
        labels: {
            show: !1
        }
    },
    tooltip: {
        enabled: !0
    },
    responsive: [{
        breakpoint: 1025,
        options: {
            chart: {
                height: 199
            }
        }
    }],
};

var chart = new ApexCharts(document.querySelector("#total_customers"), options);
chart.render();

// invoiced_customers

var options = {
    chart: {
        height: 95,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "40%",
            startingShape: "rounded",
            endingShape: "rounded",
            borderRadius: 4,
            distributed: !0,
        },
    },
    grid: {
        show: !1,
        padding: {
            top: -20,
            bottom: -10,
            left: 0,
            right: 0
        },
    },
    colors: ["#eef2f7", "#eef2f7", "#604ae3", "#eef2f7"],
    dataLabels: {
        enabled: !1
    },
    series: [{
        name: 'New Agents',
        data: [40, 50, 65, 40, 40, 65, 40]
    }],
    legend: {
        show: !1
    },
    xaxis: {
        categories: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
        axisBorder: {
            show: !1
        },
        axisTicks: {
            show: !1
        },
    },
    yaxis: {
        labels: {
            show: !1
        }
    },
    tooltip: {
        enabled: !0
    },
    responsive: [{
        breakpoint: 1025,
        options: {
            chart: {
                height: 199
            }
        }
    }],
};
var chart = new ApexCharts(document.querySelector("#invoiced_customers"), options);
chart.render();

// new_sale

var options = {
    chart: {
        height: 95,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "40%",
            startingShape: "rounded",
            endingShape: "rounded",
            borderRadius: 4,
            distributed: !0,
        },
    },
    grid: {
        show: !1,
        padding: {
            top: -20,
            bottom: -10,
            left: 0,
            right: 0
        },
    },
    colors: ["#eef2f7", "#eef2f7", "#604ae3", "#eef2f7"],
    dataLabels: {
        enabled: !1
    },
    series: [{
        name: 'New Customers',
        data: [40, 50, 65, 40, 40, 65, 40]
    }],
    legend: {
        show: !1
    },
    xaxis: {
        categories: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
        axisBorder: {
            show: !1
        },
        axisTicks: {
            show: !1
        },
    },
    yaxis: {
        labels: {
            show: !1
        }
    },
    tooltip: {
        enabled: !0
    },
    responsive: [{
        breakpoint: 1025,
        options: {
            chart: {
                height: 199
            }
        }
    }],
};
var chart = new ApexCharts(document.querySelector("#new_sale"), options);
chart.render();

// invoiced_sales

var options = {
    chart: {
        height: 95,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "40%",
            startingShape: "rounded",
            endingShape: "rounded",
            borderRadius: 4,
            distributed: !0,
        },
    },
    grid: {
        show: !1,
        padding: {
            top: -20,
            bottom: -10,
            left: 0,
            right: 0
        },
    },
    colors: ["#eef2f7", "#eef2f7", "#604ae3", "#eef2f7"],
    dataLabels: {
        enabled: !1
    },
    series: [{
        name: 'Revenue',
        data: [40, 50, 65, 40, 40, 65, 40]
    }],
    legend: {
        show: !1
    },
    xaxis: {
        categories: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
        axisBorder: {
            show: !1
        },
        axisTicks: {
            show: !1
        },
    },
    yaxis: {
        labels: {
            show: !1
        }
    },
    tooltip: {
        y: {
          formatter: function (val) {
            return "$" + val + " thousands"
          }
        }
    },
    responsive: [{
        breakpoint: 1025,
        options: {
            chart: {
                height: 199
            }
        }
    }],
};
var chart = new ApexCharts(document.querySelector("#invoiced_sales"), options);
chart.render();



// sales_analytic

var options = {
    chart: {
        height: 341,
        type: "area",

        dropShadow: {
            enabled: true,
            opacity: 0.2,
            blur: 10,
            left: -7,
            top: 22,
        },
        toolbar: {
            show: false,
        },
    },
    colors: ["#47ad94", "#604ae3"],
    dataLabels: {
        enabled: false,
    },

    stroke: {
        show: true,
        curve: "smooth",
        width: 2,
        lineCap: "square",
    },
    series: [{
            name: "Expenses",
            data: [
                16800, 16800, 15500, 17000, 14800, 15500, 19000, 16000, 15000, 17000,
                14000, 17000,
            ],
        },
        {
            name: "Income",
            data: [
                16500, 17500, 16200, 21500, 17300, 16000, 16000, 17000, 16000, 19000,
                18000, 19000,
            ],
        },
    ],
    labels: [
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
    xaxis: {
        axisBorder: {
            show: false,
        },
        axisTicks: {
            show: false,
        },
        crosshairs: {
            show: true,
        },
        labels: {
            offsetX: 0,
            offsetY: 5,
            style: {
                fontSize: "12px",
                cssClass: "apexcharts-xaxis-title",
            },
        },
    },
    yaxis: {
        labels: {
            formatter: function (value, index) {
                return value / 1000 + "K";
            },
            offsetX: -15,
            offsetY: 0,
            style: {
                fontSize: "12px",
                cssClass: "apexcharts-yaxis-title",
            },
        },
    },
    grid: {
        borderColor: "#191e3a",
        strokeDashArray: 5,
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
            top: -50,
            right: 0,
            bottom: 0,
            left: 5,
        },
    },
    legend: {
        show: false,
    },

    fill: {
        type: "gradient",
        gradient: {
            type: "vertical",
            shadeIntensity: 1,
            inverseColors: !1,
            opacityFrom: 0.12,
            opacityTo: 0.1,
            stops: [100, 100],
        },
    },
    responsive: [{
        breakpoint: 575,
        options: {
            legend: {
                offsetY: -50,
            },
        },
    }, ],
};
var chart = new ApexCharts(document.querySelector("#sales_analytic"), options);
chart.render();

// sales_funnel
var options = {
    chart: {
        height: 120,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "40%",
            startingShape: "rounded",
            endingShape: "rounded",
            borderRadius: 4,
            distributed: !0,
        },
    },
    grid: {
        show: true,
        padding: {
            top: -20,
            bottom: -10,
            left: 0,
            right: 0
        },
    },
    colors: ["#604ae3", "#604ae3", "#604ae3", "#604ae3"],
    dataLabels: {
        enabled: !1
    },
    series: [{
        name: 'Property Sales',
        data: [40, 50, 65, 45, 40, 70, 40]
    }],
    legend: {
        show: !1
    },
    xaxis: {
        categories: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
        axisBorder: {
            show: !1
        },
        axisTicks: {
            show: !1
        },
    },
    yaxis: {
        labels: {
            show: true
        }
    },
    tooltip: {
        enabled: !0
    },
    responsive: [{
        breakpoint: 1025,
        options: {
            chart: {
                height: 199
            }
        }
    }],
};

var chart = new ApexCharts(document.querySelector("#sales_funnel"), options);
chart.render();


  
//
// GRADIENT CIRCULAR CHART
//
var colors = ["#7f56da", "#4697ce"];
var options = {
  chart: {
    height: 349,
    type: "radialBar",
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    radialBar: {
      startAngle: -135,
      endAngle: 225,
      hollow: {
        margin: 0,
        size: "70%",
        background: "transparent",
        image: undefined,
        imageOffsetX: 0,
        imageOffsetY: 0,
        position: "front",
        dropShadow: {
          enabled: true,
          top: 3,
          left: 0,
          blur: 4,
          opacity: 0.24,
        },
      },
      track: {
        background: "rgba(170,184,197, 0.4)",
        strokeWidth: "67%",
        margin: 0,
      },

      dataLabels: {
        showOn: "always",
        name: {
          offsetY: -10,
          show: true,
          color: "#888",
          fontSize: "17px",
        },
        value: {
          formatter: function (val) {
            return parseInt(val);
          },
          color: "#111",
          fontSize: "36px",
          show: true,
        },
      },
    },
  },
  fill: {
    type: "gradient",
    gradient: {
      shade: "dark",
      type: "horizontal",
      shadeIntensity: 0.5,
      gradientToColors: colors,
      inverseColors: true,
      opacityFrom: 1,
      opacityTo: 1,
      stops: [0, 100],
    },
  },
  series: [70],
  stroke: {
    lineCap: "round",
  },
  labels: ["Total Buyer"],
};
var chart = new ApexCharts(document.querySelector("#own-property"), options);
chart.render();



// most-sales-location

class VectorMap {
    initWorldMapMarker() {
        const map = new jsVectorMap({
            map: "world",
            selector: "#most-sales-location",
            zoomOnScroll: true,
            zoomButtons: false,
            markersSelectable: true,
            markers: [{
                    name: "Canada",
                    coords: [56.1304, -106.3468]
                },
                {
                    name: "Brazil",
                    coords: [-14.235, -51.9253]
                },
                {
                    name: "Russia",
                    coords: [61, 105]
                },
                {
                    name: "China",
                    coords: [35.8617, 104.1954]
                },
                {
                    name: "United States",
                    coords: [37.0902, -95.7129]
                },
            ],
            markerStyle: {
                initial: {
                    fill: "#7f56da"
                },
                selected: {
                    fill: "#1bb394"
                },
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
