const dashboardChartElement = document.querySelector("#chart-profile-visit");
const dashboardChartDataElement = document.getElementById("dashboard-chart-data");

if (dashboardChartElement && dashboardChartDataElement) {
    const dashboardChartData = JSON.parse(dashboardChartDataElement.textContent);
    const hasData = dashboardChartData.series.some((serie) =>
        serie.data.some((value) => value > 0)
    );

    const optionsProfileVisit = {
        series: [
            {
                name: "Stagiaires",
                type: "column",
                data: dashboardChartData.series[0].data,
            },
            {
                name: "Actions planifiées",
                type: "line",
                data: dashboardChartData.series[1].data,
            },
        ],
        chart: {
            height: 350,
            type: "line",
            stacked: false,
            toolbar: {
                show: false,
            },
            fontFamily: "Nunito, sans-serif",
            animations: { // Added animations for a premium feel
                enabled: true,
                easing: 'easeinout',
                speed: 800,
                animateGradually: {
                    enabled: true,
                    delay: 150
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 350
                }
            }
        },
        colors: ["#5a8dee", "#5ddab4"], // Refined colors
        dataLabels: {
            enabled: false,
        },
        stroke: {
            width: [0, 4],
            curve: "smooth",
            dashArray: [0, 0], // Solid line for the line chart
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "55%",
                endingShape: "rounded",
                borderRadius: 6,
                colors: { // Gradient for column bars
                    ranges: [{
                        from: 0,
                        to: 100000, // Max value, adjust if needed
                        color: '#5a8dee'
                    }],
                    backgroundBarColors: [],
                    backgroundBarOpacity: 1,
                    backgroundBarRadius: 0,
                }
            },
        },
        fill: { // Apply gradient to column series
            type: 'gradient',
            gradient: {
                shade: 'light',
                type: 'vertical',
                shadeIntensity: 0.25,
                gradientToColors: ['#8dbeff'], // Lighter shade for gradient end
                inverseColors: true,
                opacityFrom: 1,
                opacityTo: 0.8,
                stops: [0, 100]
            }
        },
        xaxis: {
            categories: dashboardChartData.categories,
            labels: {
                rotate: -45,
                style: {
                    colors: "#62748a",
                    fontSize: "12px",
                    fontFamily: "Nunito, sans-serif",
                },
            },
            axisBorder: {
                show: false,
            },
            axisTicks: {
                show: false,
            },
        },
        yaxis: [
            {
                axisTicks: {
                    show: true,
                },
                axisBorder: {
                    show: true,
                    color: "#5a8dee", // Color for the first Y-axis
                },
                labels: {
                    style: {
                        colors: "#5a8dee",
                        fontSize: "12px",
                        fontFamily: "Nunito, sans-serif",
                    },
                },
                title: {
                    text: "Nombre de Stagiaires",
                    style: {
                        color: "#5a8dee",
                        fontFamily: "Nunito, sans-serif",
                        fontWeight: 700,
                    },
                },
                tooltip: {
                    enabled: true,
                },
            },
            {
                seriesName: "Actions planifiées",
                opposite: true,
                axisTicks: {
                    show: true,
                },
                axisBorder: {
                    show: true,
                    color: "#5ddab4", // Color for the second Y-axis
                },
                labels: {
                    style: {
                        colors: "#5ddab4",
                        fontSize: "12px",
                        fontFamily: "Nunito, sans-serif",
                    },
                },
                title: {
                    text: "Nombre d'Actions",
                    style: {
                        color: "#5ddab4",
                        fontFamily: "Nunito, sans-serif",
                        fontWeight: 700,
                    },
                },
            },
        ],
        grid: {
            borderColor: "rgba(15, 23, 42, 0.08)",
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: false,
                },
            },
            yaxis: {
                lines: {
                    show: true,
                },
            },
        },
        legend: {
            position: "bottom",
            horizontalAlign: "center",
            fontSize: "13px",
            labels: {
                colors: "#112033",
            },
            markers: {
                radius: 12,
            },
        },
        tooltip: {
            theme: "light",
            y: [
                {
                    title: {
                        formatter: function (val) {
                            return val + " (Stagiaires)";
                        },
                    },
                },
                {
                    title: {
                        formatter: function (val) {
                            return val + " (Actions)";
                        },
                    },
                },
            ],
        },
        noData: {
            text: "Aucune donnée exploitable pour le moment.",
            align: "center",
            verticalAlign: "middle",
            style: {
                color: "#62748a",
                fontSize: "14px",
                fontFamily: "Nunito, sans-serif",
            },
        },
    };

    if (!hasData) {
        optionsProfileVisit.series = [];
    }

    const chartProfileVisit = new ApexCharts(dashboardChartElement, optionsProfileVisit);
    chartProfileVisit.render();
}