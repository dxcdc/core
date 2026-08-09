// invoiced_customers

var options = {
    chart: {
        height: 294,
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
    colors: ["#604ae3", "#d3cbff", "#d3cbff", "#d3cbff"],
    dataLabels: {
        enabled: true
    },
    series: [{
        name: 'Inquiry',
        data: [4, 5, 6, 4, 9, 5, 4]
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
var chart = new ApexCharts(document.querySelector("#weekly-inquiry"), options);
chart.render();



//
// GRADIENT CIRCULAR CHART
//
var colors = ["#7f56da", "#4697ce"];
var options = {
  chart: {
    height: 343,
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
  series: [27],
  stroke: {
    lineCap: "round",
  },
  labels: ["Own"],
};
var chart = new ApexCharts(document.querySelector("#own-property"), options);
chart.render();
