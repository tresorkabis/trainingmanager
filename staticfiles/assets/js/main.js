/* Main JS - Training Manager
   Global UI interactions: sidebar toggle, perfect scrollbar,
   active menu highlighting, and responsive behaviour.
*/
(function () {
    "use strict";

    // -------------------------------------------------------
    // Sidebar toggle (mobile)
    // -------------------------------------------------------
    var sidebar = document.getElementById("sidebar");
    var burgerBtn = document.querySelector(".burger-btn");
    var sidebarToggler = document.querySelector(".sidebar-toggler");
    var sidebarHide = document.querySelector(".sidebar-hide");

    function toggleSidebar() {
        if (sidebar) {
            sidebar.classList.toggle("show");
        }
    }

    if (burgerBtn) {
        burgerBtn.addEventListener("click", function (e) {
            e.preventDefault();
            toggleSidebar();
        });
    }

    if (sidebarToggler) {
        sidebarToggler.addEventListener("click", function (e) {
            e.preventDefault();
            toggleSidebar();
        });
    }

    if (sidebarHide) {
        sidebarHide.addEventListener("click", function (e) {
            e.preventDefault();
            toggleSidebar();
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", function (e) {
        if (
            sidebar &&
            sidebar.classList.contains("show") &&
            !sidebar.contains(e.target) &&
            burgerBtn &&
            !burgerBtn.contains(e.target)
        ) {
            sidebar.classList.remove("show");
        }
    });

    // -------------------------------------------------------
    // Perfect Scrollbar (if available)
    // -------------------------------------------------------
    if (typeof PerfectScrollbar !== "undefined") {
        var sidebarWrapper = document.querySelector(".sidebar-wrapper");
        if (sidebarWrapper) {
            new PerfectScrollbar(sidebarWrapper, {
                wheelSpeed: 2,
                wheelPropagation: false,
            });
        }
    }

    // -------------------------------------------------------
    // Active menu highlighting
    // -------------------------------------------------------
    var currentPath = window.location.pathname;
    var sidebarLinks = document.querySelectorAll(".sidebar-link");

    sidebarLinks.forEach(function (link) {
        var href = link.getAttribute("href");
        if (href && currentPath === href) {
            link.closest(".sidebar-item").classList.add("active");
        }
    });

    // -------------------------------------------------------
    // Bootstrap tooltip & popover init (if Bootstrap is available)
    // -------------------------------------------------------
    if (typeof bootstrap !== "undefined") {
        var tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        var popoverTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="popover"]')
        );
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // -------------------------------------------------------
    // Auto-dismiss alerts after 5 seconds
    // -------------------------------------------------------
    var alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (typeof bootstrap !== "undefined" && bootstrap.Alert) {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } else {
                alert.style.display = "none";
            }
        }, 5000);
    });
})();
