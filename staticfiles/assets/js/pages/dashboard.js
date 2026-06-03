const dashboardChartElement = document.querySelector("#chart-profile-visit");
const dashboardChartDataElement = document.getElementById("dashboard-chart-data");

if (dashboardChartElement && dashboardChartDataElement) {
    const dashboardChartData = JSON.parse(dashboardChartDataElement.textContent);
    const hasData = dashboardChartData.series.some((serie) =>
        serie.data.some((value) => value > 0)
    );

    const chartHeight = Math.max(320, (dashboardChartData.categories.length * 52) + 90);

    const optionsProfileVisit = {
        series: dashboardChartData.series.map((serie) => ({
            name: serie.name,
            type: "bar",
            data: serie.data,
        })),
        chart: {
            height: chartHeight,
            type: "bar",
            stacked: false,
            toolbar: {
                show: false,
            },
            fontFamily: "Nunito, sans-serif",
            animations: {
                enabled: true,
                easing: "easeinout",
                speed: 700,
                animateGradually: {
                    enabled: true,
                    delay: 120,
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 300,
                },
            },
        },
        colors: ["#5a8dee", "#5ddab4"],
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: "58%",
                borderRadius: 8,
                borderRadiusApplication: "end",
                hideZeroBarsWhenGrouped: true,
            },
        },
        dataLabels: {
            enabled: true,
            offsetX: 4,
            style: {
                fontSize: "12px",
                fontFamily: "Nunito, sans-serif",
                fontWeight: 700,
                colors: ["#112033"],
            },
        },
        stroke: {
            width: 1,
            colors: ["#ffffff"],
        },
        xaxis: {
            categories: dashboardChartData.categories,
            labels: {
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
            title: {
                text: "Nombre",
                style: {
                    color: "#62748a",
                    fontFamily: "Nunito, sans-serif",
                    fontWeight: 600,
                },
            },
        },
        yaxis: {
            labels: {
                style: {
                    colors: "#112033",
                    fontSize: "12px",
                    fontFamily: "Nunito, sans-serif",
                },
            },
        },
        grid: {
            borderColor: "rgba(15, 23, 42, 0.08)",
            strokeDashArray: 4,
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
        },
        legend: {
            position: "top",
            horizontalAlign: "left",
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
            y: {
                formatter: function (value) {
                    return `${value} élément(s)`;
                },
            },
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
