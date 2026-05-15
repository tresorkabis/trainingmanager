const dashboardChartElement = document.querySelector("#chart-profile-visit");
const dashboardChartDataElement = document.getElementById("dashboard-chart-data");

if (dashboardChartElement && dashboardChartDataElement) {
    const dashboardChartData = JSON.parse(dashboardChartDataElement.textContent);
    const hasData = dashboardChartData.series.some((serie) =>
        serie.data.some((value) => value > 0)
    );

    const optionsProfileVisit = {
        series: dashboardChartData.series,
        chart: {
            type: "bar",
            height: 320,
            toolbar: {
                show: false,
            },
        },
        colors: ["#0f766e", "#b45309"],
        dataLabels: {
            enabled: false,
        },
        stroke: {
            show: true,
            width: [0, 3],
            colors: ["transparent", "#b45309"],
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "44%",
                borderRadius: 6,
            },
        },
        xaxis: {
            categories: dashboardChartData.categories,
            labels: {
                rotate: -20,
                style: {
                    colors: "#62748a",
                    fontSize: "12px",
                    fontFamily: "Nunito, sans-serif",
                },
            },
        },
        yaxis: {
            min: 0,
            forceNiceScale: true,
            labels: {
                style: {
                    colors: "#62748a",
                    fontSize: "12px",
                    fontFamily: "Nunito, sans-serif",
                },
            },
            title: {
                text: "Volume",
                style: {
                    color: "#112033",
                    fontFamily: "Nunito, sans-serif",
                    fontWeight: 700,
                },
            },
        },
        grid: {
            borderColor: "rgba(15, 23, 42, 0.08)",
            strokeDashArray: 4,
        },
        legend: {
            position: "top",
            horizontalAlign: "right",
            labels: {
                colors: "#112033",
            },
        },
        tooltip: {
            y: {
                formatter: function (value) {
                    return `${value}`;
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
