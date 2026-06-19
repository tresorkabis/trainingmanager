// ============================================
// GRAPHIQUE 1: Répartition par filière
// ============================================
(function renderFiliereChart() {
    const element = document.querySelector("#chart-profile-visit");
    const dataEl = document.getElementById("dashboard-chart-data");
    if (!element || !dataEl) return;

    const data = JSON.parse(dataEl.textContent);
    const categories = data.categories;
    const hasData = data.series.some(s => s.data.some(v => v > 0));
    const chartHeight = Math.max(320, (categories.length * 52) + 90);

    const options = {
        series: data.series.map(s => ({ name: s.name, type: "bar", data: s.data })),
        chart: {
            height: chartHeight,
            type: "bar",
            stacked: false,
            toolbar: { show: false },
            fontFamily: "Nunito, sans-serif",
            animations: {
                enabled: true, easing: "easeinout", speed: 700,
                animateGradually: { enabled: true, delay: 120 },
                dynamicAnimation: { enabled: true, speed: 300 },
            },
            events: {
                dataPointSelection: function (event, chartContext, config) {
                    const filiere = categories[config.dataPointIndex];
                    if (filiere && filiere !== "Autres") {
                        window.location.href = "/training/filieres";
                    }
                },
            },
        },
        colors: ["#5a8dee", "#5ddab4"],
        plotOptions: {
            bar: { horizontal: true, barHeight: "58%", borderRadius: 8, borderRadiusApplication: "end", hideZeroBarsWhenGrouped: true },
        },
        dataLabels: {
            enabled: true, offsetX: 4,
            style: { fontSize: "12px", fontFamily: "Nunito, sans-serif", fontWeight: 700, colors: ["#112033"] },
        },
        stroke: { width: 1, colors: ["#ffffff"] },
        xaxis: {
            categories: categories,
            labels: { style: { colors: "#62748a", fontSize: "12px", fontFamily: "Nunito, sans-serif" } },
            axisBorder: { show: false }, axisTicks: { show: false },
            title: { text: "Nombre", style: { color: "#62748a", fontFamily: "Nunito, sans-serif", fontWeight: 600 } },
        },
        yaxis: {
            labels: { style: { colors: "#112033", fontSize: "12px", fontFamily: "Nunito, sans-serif" } },
        },
        grid: { borderColor: "rgba(15, 23, 42, 0.08)", strokeDashArray: 4, xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } },
        legend: { position: "top", horizontalAlign: "left", fontSize: "13px", labels: { colors: "#112033" }, markers: { radius: 12 } },
        tooltip: {
            theme: "light", shared: true, intersect: false,
            y: {
                formatter: function (value, { seriesIndex, dataPointIndex }) {
                    if (value === undefined || value === null) return "";
                    const filiere = categories[dataPointIndex] || "Inconnue";
                    const totalStagiaires = data.series[0]?.data[dataPointIndex] || 0;
                    const totalActions = data.series[1]?.data[dataPointIndex] || 0;
                    const totalFiliere = totalStagiaires + totalActions;
                    const label = seriesIndex === 0 ? "Stagiaires" : "Actions";
                    return `<strong>${filiere}</strong><br>${label}: ${value}<br>Total filière: ${totalFiliere}`;
                },
            },
        },
        noData: { text: "Aucune donnée exploitable pour le moment.", align: "center", verticalAlign: "middle", style: { color: "#62748a", fontSize: "14px", fontFamily: "Nunito, sans-serif" } },
    };

    if (!hasData) options.series = [];
    new ApexCharts(element, options).render();
})();

// ============================================
// GRAPHIQUE 2: Encaissements mensuels
// ============================================
(function renderPaiementsChart() {
    const element = document.querySelector("#chart-paiements");
    const dataEl = document.getElementById("paiements-chart-data");
    if (!element || !dataEl) return;

    const data = JSON.parse(dataEl.textContent);
    const hasData = data.series[0]?.data?.some(v => v > 0);

    const options = {
        series: data.series,
        chart: { height: 300, type: "bar", toolbar: { show: false }, fontFamily: "Nunito, sans-serif" },
        colors: ["#28a745"],
        plotOptions: { bar: { borderRadius: 6, columnWidth: "60%", dataLabels: { position: "top" } } },
        dataLabels: {
            enabled: true,
            offsetY: -20,
            style: { fontSize: "11px", fontFamily: "Nunito, sans-serif", fontWeight: 600, colors: ["#112033"] },
            formatter: function (val) { return val > 0 ? val.toLocaleString() : ""; },
        },
        xaxis: {
            categories: data.categories,
            labels: { style: { colors: "#62748a", fontSize: "11px", fontFamily: "Nunito, sans-serif" } },
        },
        yaxis: {
            labels: {
                style: { colors: "#62748a", fontSize: "11px", fontFamily: "Nunito, sans-serif" },
                formatter: function (val) { return val.toLocaleString(); },
            },
        },
        grid: { borderColor: "rgba(15, 23, 42, 0.08)", strokeDashArray: 4 },
        tooltip: {
            theme: "light",
            y: { formatter: function (val) { return `${val.toLocaleString()} USD`; } },
        },
        noData: { text: "Aucun encaissement enregistré.", align: "center", verticalAlign: "middle", style: { color: "#62748a", fontSize: "14px", fontFamily: "Nunito, sans-serif" } },
    };

    if (!hasData) options.series = [];
    new ApexCharts(element, options).render();
})();

// ============================================
// GRAPHIQUE 3: Statut des actions (Donut)
// ============================================
(function renderActionsStatusChart() {
    const element = document.querySelector("#chart-actions-status");
    const dataEl = document.getElementById("actions-status-chart-data");
    if (!element || !dataEl) return;

    const data = JSON.parse(dataEl.textContent);
    const hasData = Array.isArray(data.series) && data.series.some(v => v > 0);

    const options = {
        series: hasData ? data.series : [],
        chart: { type: "donut", height: 300, fontFamily: "Nunito, sans-serif" },
        labels: ["Planifiée", "En cours", "Terminée", "Annulée"],
        colors: ["#ffc107", "#0dcaf0", "#198754", "#dc3545"],
        legend: { position: "bottom", fontSize: "12px", labels: { colors: "#112033" } },
        plotOptions: {
            pie: {
                donut: {
                    size: "55%",
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: "Total",
                            fontSize: "14px",
                            fontFamily: "Nunito, sans-serif",
                            formatter: function (w) {
                                return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                            },
                        },
                    },
                },
            },
        },
        dataLabels: {
            enabled: true,
            formatter: function (val) {
                if (!val || val === 0) return "";
                return val.toFixed(1) + "%";
            },
        },
        tooltip: {
            theme: "light",
            y: {
                formatter: function (val) {
                    return `${val} action(s)`;
                },
            },
        },
        noData: { text: "Aucune action.", align: "center", verticalAlign: "middle", style: { color: "#62748a", fontSize: "14px", fontFamily: "Nunito, sans-serif" } },
    };

    new ApexCharts(element, options).render();
})();

// ============================================
// GRAPHIQUE 4: Séances par semaine
// ============================================
(function renderSessionsChart() {
    const element = document.querySelector("#chart-sessions");
    const dataEl = document.getElementById("sessions-chart-data");
    if (!element || !dataEl) return;

    const data = JSON.parse(dataEl.textContent);
    const hasData = data.series?.length > 0 && data.categories?.length > 0;

    const options = {
        series: data.series,
        chart: { height: 300, type: "bar", toolbar: { show: false }, fontFamily: "Nunito, sans-serif" },
        colors: ["#5a8dee", "#5ddab4"],
        plotOptions: { bar: { borderRadius: 4, columnWidth: "65%", horizontal: false, dataLabels: { position: "top" } } },
        dataLabels: {
            enabled: true,
            offsetY: -15,
            style: { fontSize: "11px", fontFamily: "Nunito, sans-serif", fontWeight: 600, colors: ["#112033"] },
            formatter: function (val) { return val > 0 ? val : ""; },
        },
        xaxis: {
            categories: data.categories,
            labels: { style: { colors: "#62748a", fontSize: "11px", fontFamily: "Nunito, sans-serif" } },
        },
        yaxis: {
            labels: { style: { colors: "#62748a", fontSize: "11px", fontFamily: "Nunito, sans-serif" } },
            min: 0,
            forceNiceScale: true,
        },
        grid: { borderColor: "rgba(15, 23, 42, 0.08)", strokeDashArray: 4 },
        legend: { position: "top", horizontalAlign: "left", fontSize: "12px", labels: { colors: "#112033" }, markers: { radius: 12 } },
        tooltip: { theme: "light" },
        noData: { text: "Aucune séance planifiée.", align: "center", verticalAlign: "middle", style: { color: "#62748a", fontSize: "14px", fontFamily: "Nunito, sans-serif" } },
    };

    if (!hasData) options.series = [];
    new ApexCharts(element, options).render();
})();

