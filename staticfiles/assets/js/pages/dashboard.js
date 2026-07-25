/* Dashboard Charts - Training Manager
   Initializes ApexCharts on the dashboard page using data
   injected via Django's json_script filter.
*/
(function () {
    "use strict";

    // Helper: safely read JSON from a <script type="application/json"> tag
    function getJsonData(scriptId) {
        var el = document.getElementById(scriptId);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent || el.innerText);
        } catch (e) {
            console.error("Failed to parse JSON for #" + scriptId, e);
            return null;
        }
    }

    // Only run on the dashboard page
    var chartProfileVisit = document.getElementById("chart-profile-visit");
    var chartActionsStatus = document.getElementById("chart-actions-status");
    var chartPaiements = document.getElementById("chart-paiements");
    var chartSessions = document.getElementById("chart-sessions");

    if (!chartProfileVisit && !chartActionsStatus && !chartPaiements && !chartSessions) {
        return;
    }

    // Ensure ApexCharts is available
    if (typeof ApexCharts === "undefined") {
        console.error("ApexCharts is not loaded. Make sure the CDN script is included.");
        return;
    }

    // Common tooltip / toolbar theme
    var apexTheme = {
        theme: {
            font: "'Nunito', sans-serif",
            foreground: "#344767",
            background: "#ffffff",
        },
        tooltip: {
            theme: "light",
            style: {
                fontSize: "0.8125rem",
                fontFamily: "'Nunito', sans-serif",
            },
        },
        toolbar: {
            show: false,
        },
        responsive: [
            {
                breakpoint: 480,
                options: {
                    chart: {
                        height: 250,
                    },
                    legend: {
                        position: "bottom",
                    },
                },
            },
        ],
    };

    // -------------------------------------------------------
    // 1. Aperçu activité – Bar chart (stagiaires vs actions)
    // -------------------------------------------------------
    if (chartProfileVisit) {
        var profileData = getJsonData("dashboard-chart-data");
        if (profileData) {
            var profileChart = new ApexCharts(chartProfileVisit, {
                chart: {
                    type: "bar",
                    height: 300,
                    toolbar: { show: false },
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        columnWidth: "40%",
                        distributed: true,
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                stroke: {
                    width: 0,
                },
                legend: {
                    position: "top",
                    horizontalAlign: "right",
                },
                colors: ["#435ebe", "#667eea"],
                series: profileData.series || [],
                xaxis: {
                    categories: profileData.categories || [],
                    axisBorder: {
                        show: false,
                    },
                    axisTicks: {
                        show: false,
                    },
                },
                title: {
                    text: profileData.title || "Aperçu activité",
                    style: {
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#1e293b",
                    },
                },
                ...apexTheme,
            });
            profileChart.render();
        }
    }

    // -------------------------------------------------------
    // 2. Statut des actions – Donut chart
    // -------------------------------------------------------
    if (chartActionsStatus) {
        var statusData = getJsonData("actions-status-chart-data");
        if (statusData) {
            var statusChart = new ApexCharts(chartActionsStatus, {
                chart: {
                    type: "donut",
                    height: 300,
                    toolbar: { show: false },
                },
                plotOptions: {
                    pie: {
                        donut: {
                            expandOnClick: true,
                        },
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                stroke: {
                    width: 2,
                },
                legend: {
                    position: "bottom",
                    horizontalAlign: "center",
                    fontSize: "0.8125rem",
                },
                colors: statusData.colors || ["#ffc107", "#0dcaf0", "#198754", "#dc3545"],
                series: statusData.series || [],
                labels: statusData.labels || [],
                title: {
                    text: statusData.title || "Statut des actions",
                    style: {
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#1e293b",
                    },
                },
                ...apexTheme,
            });
            statusChart.render();
        }
    }

    // -------------------------------------------------------
    // 3. Encaissements mensuels – Bar chart
    // -------------------------------------------------------
    if (chartPaiements) {
        var paiementsData = getJsonData("paiements-chart-data");
        if (paiementsData) {
            var paiementsChart = new ApexCharts(chartPaiements, {
                chart: {
                    type: "bar",
                    height: 300,
                    toolbar: { show: false },
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        columnWidth: "50%",
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                stroke: {
                    width: 0,
                },
                legend: {
                    position: "top",
                    horizontalAlign: "right",
                },
                colors: ["#10b981"],
                series: paiementsData.series || [],
                xaxis: {
                    categories: paiementsData.categories || [],
                    axisBorder: {
                        show: false,
                    },
                    axisTicks: {
                        show: false,
                    },
                },
                title: {
                    text: paiementsData.title || "Encaissements mensuels",
                    style: {
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#1e293b",
                    },
                },
                ...apexTheme,
            });
            paiementsChart.render();
        }
    }

    // -------------------------------------------------------
    // 4. Séances par semaine – Bar chart (prévues vs réalisées)
    // -------------------------------------------------------
    if (chartSessions) {
        var sessionsData = getJsonData("sessions-chart-data");
        if (sessionsData) {
            var sessionsChart = new ApexCharts(chartSessions, {
                chart: {
                    type: "bar",
                    height: 300,
                    toolbar: { show: false },
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        columnWidth: "50%",
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                stroke: {
                    width: 0,
                },
                legend: {
                    position: "top",
                    horizontalAlign: "right",
                },
                colors: ["#435ebe", "#10b981"],
                series: sessionsData.series || [],
                xaxis: {
                    categories: sessionsData.categories || [],
                    axisBorder: {
                        show: false,
                    },
                    axisTicks: {
                        show: false,
                    },
                },
                title: {
                    text: sessionsData.title || "Séances par semaine",
                    style: {
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#1e293b",
                    },
                },
                ...apexTheme,
            });
            sessionsChart.render();
        }
    }
})();
