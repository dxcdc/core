const slider = document.getElementById("product-price-range");
if (slider) {

    noUiSlider.create(slider, {
        start: [6000, 100000], // Handle start position
        step: 1, // Slider moves in increments of '10'
        margin: 0, // Handles must be more than '20' apart
        connect: true, // Display a colored bar between the handles
        behaviour: 'tap-drag', // Move a handle on tap, bar is draggable
        range: { // Slider can select '0' to '100'
            'min': 0,
            'max': 120000
        },
        format: wNumb({
            decimals: 0,
            prefix: '$ '
        })

    });

    const minCostInput = document.getElementById("minCost"),
        maxCostInput = document.getElementById("maxCost");

    // When the slider value changes, update the input and span
    slider.noUiSlider.on('update', function (values, handle) {
        if (handle) {
            maxCostInput.value = values[handle];
        } else {
            minCostInput.value = values[handle];
        }
    });

    minCostInput.addEventListener('change', function () {
        slider.noUiSlider.set([null, this.value]);
    });

    maxCostInput.addEventListener('change', function () {
        slider.noUiSlider.set([null, this.value]);
    });
}



//
// grid-chart
// 
var options = {
    chart: {
        height: 123,
        type: 'donut',
    },
    series: [80, 40, 30],
    legend: {
        show: false
    },
    stroke: {
        width: 0
    },
    plotOptions: {
        pie: {
            donut: {
                size: '70%',
                labels: {
                    show: false,
                    total: {
                        showAlways: true,
                        show: true
                    }
                }
            }
        }
    },
    labels: ["Vacant", "Occupied", "Unlisted"],
    colors: ["#027ef4", "#f0934e", "#47ad94"],
    dataLabels: {
        enabled: false
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: 200
            }
        }
    }]
}
var chart = new ApexCharts(
    document.querySelector("#grid-chart"),
    options
);
chart.render();




var colors = ['#ffffff'];
var options1 = {
    chart: {
        type: 'line',
        height: 115,
        sparkline: {
            enabled: true
        }
    },
    series: [{
        data: [25, 66, 41, 89, 63, 25, 44, 12, 36, 9, 54]
    }],
    stroke: {
        width: 2,
        curve: 'smooth'
    },
    markers: {
        size: 0
    },
    colors: colors,
    tooltip: {
        fixed: {
            enabled: false
        },
        x: {
            show: false
        },
        y: {
            title: {
                formatter: function (seriesName) {
                    return ''
                }
            }
        },
        marker: {
            show: false
        }
    }
}
new ApexCharts(document.querySelector("#seal_properties"), options1).render();