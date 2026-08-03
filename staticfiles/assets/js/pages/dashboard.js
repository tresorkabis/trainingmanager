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

    // Helper: show a "no data" placeholder inside a chart container
    function showNoData(el) {
        if (!el) return;
        el.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;min-height:200px;color:#94a3b8;font-size:0.9rem;font-weight:600;"><i class="bi bi-inbox" style="font-size:1.5rem;margin-right:0.5rem;"></i> Aucune donnée à afficher</div>';
    }

    // Check if ApexCharts is available, show fallback if not
    if (typeof ApexCharts === "undefined") {
        console.error("ApexCharts is not loaded. Make sure the CDN script is included.");
        [chartProfileVisit, chartActionsStatus, chartPaiements, chartSessions].forEach(showNoData);
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

    // Helper: check if all series data is zero
    function isEmptyData(data) {
        if (!data) return true;
        if (!data.series || data.series.length === 0) return true;
        var hasNonZero = false;
        for (var i = 0; i < data.series.length; i++) {
            if (data.series[i].data) {
                for (var j = 0; j < data.series[i].data.length; j++) {
                    if (data.series[i].data[j] > 0) {
                        hasNonZero = true;
                        break;
                    }
                }
            }
            if (hasNonZero) break;
        }
        return !hasNonZero;
    }

    // -------------------------------------------------------
    // 1. Aperçu activité – Bar chart (stagiaires vs actions)
    // -------------------------------------------------------
    if (chartProfileVisit) {
        var profileData = getJsonData("dashboard-chart-data");
        if (profileData && !isEmptyData(profileData)) {
            var profileChart = new ApexCharts(chartProfileVisit, {
                chart: {
                    type: "bar",
                    height: 400,
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
                    show: true,
                    position: "bottom",
                    horizontalAlign: "center",
                    fontSize: "0.8rem",
                    fontFamily: "'Nunito', sans-serif",
                    fontWeight: 600,
                    markers: {
                        width: 10,
                        height: 10,
                        radius: 3,
                    },
                    itemMargin: {
                        horizontal: 10,
                    },
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
                // Titre supprimé car déjà présent dans le card-header du template
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
        if (statusData && !isEmptyData(statusData)) {
            var statusChart = new ApexCharts(chartActionsStatus, {
                chart: {
                    type: "donut",
                    height: 450,
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
                    enabled: true,
                    style: {
                        fontSize: "0.75rem",
                        fontWeight: 600,
                    },
                    dropShadow: {
                        enabled: false,
                    },
                },
                stroke: {
                    width: 2,
                },
                legend: {
                    show: true,
                    position: "bottom",
                    horizontalAlign: "center",
                    fontSize: "0.8rem",
                    fontFamily: "'Nunito', sans-serif",
                    fontWeight: 600,
                    markers: {
                        width: 10,
                        height: 10,
                        radius: 3,
                    },
                    itemMargin: {
                        horizontal: 10,
                    },
                },
                colors: statusData.colors || ["#ffc107", "#0dcaf0", "#198754", "#dc3545"],
                series: statusData.series || [],
                labels: statusData.labels || [],
                // Titre supprimé car déjà présent dans le card-header du template
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
        if (paiementsData && !isEmptyData(paiementsData)) {
            var paiementsChart = new ApexCharts(chartPaiements, {
                chart: {
                    type: "bar",
                    height: 400,
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
                    show: false,
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
                // Titre supprimé car déjà présent dans le card-header du template
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
        if (sessionsData && !isEmptyData(sessionsData)) {
            var sessionsChart = new ApexCharts(chartSessions, {
                chart: {
                    type: "bar",
                    height: 400,
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
                    show: true,
                    position: "bottom",
                    horizontalAlign: "center",
                    fontSize: "0.8rem",
                    fontFamily: "'Nunito', sans-serif",
                    fontWeight: 600,
                    markers: {
                        width: 10,
                        height: 10,
                        radius: 3,
                    },
                    itemMargin: {
                        horizontal: 10,
                    },
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
                // Titre supprimé car déjà présent dans le card-header du template
                ...apexTheme,
            });
            sessionsChart.render();
        }
    }
})();
