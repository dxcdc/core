// customer_invest
var options = {
    chart: {
        height: 182,
        parentHeightOffset: 0,
        type: "bar",
        toolbar: {
            show: !1,
        },
    },
    plotOptions: {
        bar: {
            barHeight: "100%",
            columnWidth: "30%",
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
            right: 0,
        },
    },
    colors: ["#efecfc", "#604ae3", "#604ae3", "#efecfc"],
    dataLabels: {
        enabled: !1,
    },
    series: [
        {
            name: "Invest",
            data: [40, 50, 65, 45, 40, 70, 40, 50, 45, 20, 10, 29],
        },
    ],
    legend: {
        show: !1,
    },
    xaxis: {
        categories: [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "July",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        axisBorder: {
            show: !1,
        },
        axisTicks: {
            show: !1,
        },
    },
    yaxis: {
        labels: {
            show: !1,
        },
    },
    tooltip: {
        y: [
            {
                formatter: function (y) {
                    if (typeof y !== "undefined") {
                        return "$" + y.toFixed(2) + "k";
                    }
                    return y;
                },
            },
        ],
    },
    responsive: [
        {
            breakpoint: 1025,
            options: {
                chart: {
                    height: 199,
                },
            },
        },
    ],
};

var chart = new ApexCharts(document.querySelector("#customer_invest"), options);
chart.render();

class VectorMap {
    initWorldMapMarker() {
        const map = new jsVectorMap({
            map: "world",
            selector: "#world-map-markers",
            zoomOnScroll: false,
            zoomButtons: !1,
            markersSelectable: !1,
            markers: [
                { name: "Greenland", coords: [72, -42] },
                { name: "Canada", coords: [56.1304, -106.3468] },
                { name: "Brazil", coords: [-14.235, -51.9253] },
                { name: "Egypt", coords: [26.8206, 30.8025] },
                { name: "Russia", coords: [61, 105] },
                { name: "China", coords: [35.8617, 104.1954] },
                { name: "United States", coords: [37.0902, -95.7129] },
                { name: "Norway", coords: [60.472024, 8.468946] },
                { name: "Ukraine", coords: [48.379433, 31.16558] },
            ],
            markerStyle: {
                initial: { fill: "#5B8DEC" },
                selected: { fill: "#ed5565" },
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

//
// COLUMN CHART WITH DATALABELS
//
var options = {
    chart: {
        height: 300,
        type: "bar",
        toolbar: {
            show: false,
        },
    },
    plotOptions: {
        bar: {
            borderRadius: 10,
            columnWidth: "30%",
            dataLabels: {
                position: "top", // top, center, bottom
            },
        },
    },
    dataLabels: {
        enabled: true,
        formatter: function (val) {
            return val + "%";
        },
        offsetY: -25,
        style: {
            fontSize: "12px",
            colors: ["#304758"],
        },
    },
    colors: ["#604ae3"],
    legend: {
        show: true,
        horizontalAlign: "center",
        offsetX: 0,
        offsetY: -5,
    },
    series: [
        {
            name: "Invest Percentage",
            data: [12.3, 3.1, 4.0, 10.1, 6.0, 2.3, 19.4],
        },
    ],
    xaxis: {
        categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "July"],
        position: "bottom",
        labels: {
            offsetY: 0,
        },
        axisBorder: {
            show: true,
        },
        axisTicks: {
            show: true,
        },

        tooltip: {
            enabled: true,
            offsetY: -10,
        },
    },

    yaxis: {
        axisBorder: {
            show: true,
        },
        axisTicks: {
            show: true,
        },
        labels: {
            show: true,
            formatter: function (val) {
                return val + "%";
            },
        },
    },
    grid: {
        row: {
            colors: ["transparent", "transparent"], // takes an array which will be repeated on columns
            opacity: 0.2,
        },
        borderColor: "#f1f3fa",
    },
};

var chart = new ApexCharts(
    document.querySelector("#datalabels-column2"),
    options
);

chart.render();

//
//
// sales_funnel
//
var options = {
    chart: {
        type: "area",
        height: 150,
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
var chart = new ApexCharts(
    document.querySelector("#customer_devices"),
    options
);
chart.render();
