// ==========================================================
// AI Inventory Management Dashboard
// Part 1
// ==========================================================

$(document).ready(function () {

    console.log("AI Inventory Dashboard Loaded");

    // ======================================================
    // Inventory DataTable
    // ======================================================

    if ($("#inventoryTable").length) {

        if ($.fn.DataTable.isDataTable("#inventoryTable")) {
            $("#inventoryTable").DataTable().destroy();
        }

        $("#inventoryTable").DataTable({
            responsive: true,
            pageLength: 10,
            lengthMenu: [10, 25, 50, 100],
            order: [],
            autoWidth: false
        });

    }

    // ======================================================
    // Purchase DataTable
    // ======================================================

    if ($("#purchaseTable").length) {

        if ($.fn.DataTable.isDataTable("#purchaseTable")) {
            $("#purchaseTable").DataTable().destroy();
        }

        $("#purchaseTable").DataTable({
            responsive: true,
            pageLength: 10,
            lengthMenu: [10, 25, 50],
            order: [],
            autoWidth: false
        });

    }

    // ======================================================
    // Dark Mode
    // ======================================================

    $("#darkModeBtn").click(function () {

        $("body").toggleClass("dark-mode");

        localStorage.setItem(
            "darkMode",
            $("body").hasClass("dark-mode")
        );

    });

    if (localStorage.getItem("darkMode") === "true") {
        $("body").addClass("dark-mode");
    }

    // ======================================================
    // Live Clock
    // ======================================================

    function updateClock() {

        let now = new Date();

        let options = {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        };

        $("#clock").text(
            now.toLocaleString("en-IN", options)
        );

    }

    updateClock();

    setInterval(updateClock, 1000);

    // ======================================================
    // Dashboard Statistics
    // ======================================================

    function loadStats() {

        $.getJSON("/stats", function (data) {

            $("#total").text(data.total);

            $("#ok").text(data.ok);

            $("#purchase").text(data.purchase);

            $("#stockout").text(data.stockout);

            $("#deadstock").text(data.deadstock);

            $("#purchaseQty").text(data.purchase_qty);

            $("#inventoryHealth").text(
                data.inventory_health + "%"
            );

        });

    }

    loadStats();

    setInterval(loadStats, 10000);

    // ======================================================
    // Auto Refresh if Excel Changes
    // ======================================================

    function checkUpdate() {

        $.getJSON("/check_update", function (data) {

            if (data.updated) {

                console.log("Inventory Updated");

                location.reload();

            }

        });

    }

    setInterval(checkUpdate, 5000);

});
// ==========================================================
// AI Inventory Management Dashboard
// Part 2
// ==========================================================


// ==========================================================
// Load Alerts
// ==========================================================

function loadAlerts() {

    if (!$("#alertBox").length)
        return;

    $.getJSON("/alerts", function (alerts) {

        $("#alertBox").empty();

        if (alerts.length === 0) {

            $("#alertBox").html(
                '<div class="alert alert-success">No active alerts.</div>'
            );

            return;

        }

        alerts.forEach(function (item) {

            let color = "warning";

            if (item.status === "Stock Out")
                color = "danger";

            if (item.status === "Purchase Required")
                color = "warning";

            if (item.status === "Dead Stock")
                color = "secondary";

            $("#alertBox").append(

                '<div class="alert alert-' + color + '">' +

                '<strong>' + item.item + '</strong><br>' +

                item.status +

                '</div>'

            );

        });

    });

}


// ==========================================================
// AI Recommendations
// ==========================================================

function loadRecommendations() {

    if (!$("#recommendations").length)
        return;

    $.getJSON("/recommendations", function (list) {

        $("#recommendations").empty();

        if (list.length === 0) {

            $("#recommendations").html(

                '<div class="alert alert-success">Everything looks good.</div>'

            );

            return;

        }

        list.forEach(function (item) {

            let badge = "primary";

            if (item.priority === "High")
                badge = "danger";

            if (item.priority === "Medium")
                badge = "warning";

            if (item.priority === "Low")
                badge = "secondary";

            $("#recommendations").append(

                '<div class="card mb-2">' +

                '<div class="card-body">' +

                '<span class="badge bg-' + badge + '">' +

                item.priority +

                '</span><br><br>' +

                '<strong>' +

                item.item +

                '</strong><br>' +

                item.message +

                '</div></div>'

            );

        });

    });

}



// ==========================================================
// Monthly Sales Chart
// ==========================================================

let salesChart;

function loadMonthlyChart() {

    if (!$("#salesChart").length)
        return;

    $.getJSON("/monthly_sales", function (chart) {

        const ctx = document.getElementById("salesChart");

        if (salesChart)
            salesChart.destroy();

        salesChart = new Chart(ctx, {

            type: "line",

            data: {

                labels: chart.labels,

                datasets: [

                    {

                        label: "Monthly Sales",

                        data: chart.data,

                        tension: 0.4,

                        fill: true

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false

            }

        });

    });

}



// ==========================================================
// Top Selling Items Chart
// ==========================================================

let topChart;

function loadTopChart() {

    if (!$("#topChart").length)
        return;

    $.getJSON("/top_items", function (chart) {

        const ctx = document.getElementById("topChart");

        if (topChart)
            topChart.destroy();

        topChart = new Chart(ctx, {

            type: "bar",

            data: {

                labels: chart.labels,

                datasets: [

                    {

                        label: "Sales",

                        data: chart.data

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false

            }

        });

    });

}



// ==========================================================
// Voice Alert
// ==========================================================

function speak(text) {

    if (!("speechSynthesis" in window))
        return;

    let speech = new SpeechSynthesisUtterance(text);

    speech.rate = 1;

    speech.pitch = 1;

    speech.volume = 1;

    window.speechSynthesis.cancel();

    window.speechSynthesis.speak(speech);

}



// ==========================================================
// Check Alerts for Voice
// ==========================================================

function voiceAlert() {

    $.getJSON("/alerts", function (alerts) {

        if (alerts.length > 0) {

            speak(

                "Warning. " +

                alerts.length +

                " inventory alerts require your attention."

            );

        }

    });

}



// ==========================================================
// Initial Load
// ==========================================================

loadAlerts();

loadRecommendations();

loadMonthlyChart();

loadTopChart();



// ==========================================================
// Auto Refresh
// ==========================================================

setInterval(loadAlerts, 15000);

setInterval(loadRecommendations, 15000);

setInterval(loadMonthlyChart, 15000);

setInterval(loadTopChart, 15000);

setInterval(voiceAlert, 30000);
// ==========================================================
// AI Inventory Management Dashboard
// Part 3
// ==========================================================


// ==========================================================
// Export Excel
// ==========================================================

$("#exportExcel").click(function () {

    window.location.href = "/export";

});


// ==========================================================
// Print Dashboard
// ==========================================================

$("#printDashboard").click(function () {

    window.print();

});


// ==========================================================
// Toast Notification
// ==========================================================

function showToast(message, type = "success") {

    if (!$("#toastMessage").length)
        return;

    $("#toastMessage")
        .removeClass("bg-success bg-danger bg-warning bg-info")
        .addClass("bg-" + type)
        .text(message);

    const toast = new bootstrap.Toast(
        document.getElementById("liveToast")
    );

    toast.show();

}


// ==========================================================
// Dashboard Greeting
// ==========================================================

function dashboardGreeting() {

    let hour = new Date().getHours();

    let msg = "Welcome";

    if (hour < 12)
        msg = "Good Morning";

    else if (hour < 17)
        msg = "Good Afternoon";

    else
        msg = "Good Evening";

    $("#greeting").text(msg);

}

dashboardGreeting();


// ==========================================================
// Search Shortcut
// ==========================================================

$(document).keydown(function (e) {

    if (e.ctrlKey && e.key === "f") {

        e.preventDefault();

        $("#searchInput").focus();

    }

});


// ==========================================================
// Refresh Shortcut
// ==========================================================

$(document).keydown(function (e) {

    if (e.key === "F5") {

        e.preventDefault();

        location.reload();

    }

});


// ==========================================================
// Animate Progress Bars
// ==========================================================

$(".progress-bar").each(function () {

    let width = $(this).attr("aria-valuenow");

    $(this).css("width", width + "%");

});


// ==========================================================
// Card Hover Animation
// ==========================================================

$(".card").hover(

    function () {

        $(this).addClass("shadow-lg");

    },

    function () {

        $(this).removeClass("shadow-lg");

    }

);


// ==========================================================
// Refresh Dashboard Button
// ==========================================================

$("#refreshDashboard").click(function () {

    loadStats();

    loadAlerts();

    loadRecommendations();

    loadMonthlyChart();

    loadTopChart();

    showToast("Dashboard Updated", "success");

});


// ==========================================================
// Utility Function
// ==========================================================

function formatNumber(value) {

    return Number(value).toLocaleString();

}


// ==========================================================
// Highlight Low Stock
// ==========================================================

$("#inventoryTable tbody tr").each(function () {

    let status = $(this).find("td:last").text().trim();

    if (status === "Stock Out") {

        $(this).addClass("table-danger");

    }

    else if (status === "Purchase Required") {

        $(this).addClass("table-warning");

    }

    else if (status === "Dead Stock") {

        $(this).addClass("table-secondary");

    }

});


// ==========================================================
// Loading Overlay
// ==========================================================

$(window).on("load", function () {

    $("#loading").fadeOut(500);

});


// ==========================================================
// Internet Status
// ==========================================================

window.addEventListener("offline", function () {

    showToast("Internet Connection Lost", "danger");

});

window.addEventListener("online", function () {

    showToast("Internet Connected", "success");

});


// ==========================================================
// Footer Year
// ==========================================================

$("#currentYear").text(new Date().getFullYear());


// ==========================================================
// Final Initialization
// ==========================================================

console.log("AI Inventory Dashboard Ready");
