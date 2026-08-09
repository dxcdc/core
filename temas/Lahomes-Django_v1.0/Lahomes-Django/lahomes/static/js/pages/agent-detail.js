class VectorMap {
    initWorldMapMarker() {
      const map = new jsVectorMap({
        map: "world",
        selector: "#agent-location",
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



  
  var t = new Date
  e = {
      series: [80],
      chart: {
          width: 90,
          height: 90,
          type: 'radialBar',
          sparkline: {
              enabled: true
          }
      },
      plotOptions: {
          radialBar: {
              hollow: {
                  margin: 0,
                  size: '50%',
              },
              track: {
                  margin: 0,
                  background: "#02bc9c",

              },
              dataLabels: {
                  show: false
              }
          }
      },
      grid: {
          padding: {
              top: -15,
              bottom: -15
          }
      },
      stroke: {
          lineCap: 'round'
      },
      labels: ['Cricket'],
      colors: ["#47ad94"],

  };

  new ApexCharts(document.querySelector("#property_sale"), e).render()

  
  var t = new Date
  e = {
      series: [40],
      chart: {
          width: 90,
          height: 90,
          type: 'radialBar',
          sparkline: {
              enabled: true
          }
      },
      plotOptions: {
          radialBar: {
              hollow: {
                  margin: 0,
                  size: '50%',
              },
              track: {
                  margin: 0,
                  background: "#e1360d",

              },
              dataLabels: {
                  show: false
              }
          }
      },
      grid: {
          padding: {
              top: -15,
              bottom: -15
          }
      },
      stroke: {
          lineCap: 'round'
      },
      labels: ['Cricket'],
      colors: ["#e1360d"],

  };

  new ApexCharts(document.querySelector("#property_sale2"), e).render()


  var t = new Date
  e = {
      series: [56],
      chart: {
          width: 90,
          height: 90,
          type: 'radialBar',
          sparkline: {
              enabled: true
          }
      },
      plotOptions: {
          radialBar: {
              hollow: {
                  margin: 0,
                  size: '50%',
              },
              track: {
                  margin: 0,
                  background: "#e1360d",

              },
              dataLabels: {
                  show: false
              }
          }
      },
      grid: {
          padding: {
              top: -15,
              bottom: -15
          }
      },
      stroke: {
          lineCap: 'round'
      },
      labels: ['Cricket'],
      colors: ["#027ef4"],

  };

  new ApexCharts(document.querySelector("#property_sale3"), e).render()