/* =====================================================
   AI INVENTORY MANAGEMENT
===================================================== */

"use strict";

/* =====================================================
   DOCUMENT READY
===================================================== */

$(document).ready(function () {

    initializeTables();

    initializeDarkMode();

    initializeCharts();

    initializeVoiceAlerts();

    initializeAutoRefresh();

    initializeTooltips();

});


/* =====================================================
   DATATABLES
===================================================== */

function initializeTables() {

    if ($("#inventoryTable").length) {

        $("#inventoryTable").DataTable({

            responsive: true,

            pageLength: 10,

            order: [[0, "desc"]],

            language: {

                search: "Search Inventory:",

                lengthMenu: "Show _MENU_ Entries"

            }

        });

    }

    if ($("#predictionTable").length) {

        $("#predictionTable").DataTable({

            responsive: true,

            pageLength: 10,

            order: [[6, "asc"]],

            language: {

                search: "Search Prediction:",

                lengthMenu: "Show _MENU_ Entries"

            }

        });

    }

}


/* =====================================================
   DARK MODE
===================================================== */

function initializeDarkMode() {

    const button = document.getElementById("darkMode");

    if (!button)
        return;

    if (localStorage.getItem("darkMode") === "true") {

        document.body.classList.add("dark-mode");

    }

    button.addEventListener("click", function () {

        document.body.classList.toggle("dark-mode");

        localStorage.setItem(

            "darkMode",

            document.body.classList.contains("dark-mode")

        );

    });

}


/* =====================================================
   TOOLTIPS
===================================================== */

function initializeTooltips() {

    const tooltipTriggerList =
        [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));

    tooltipTriggerList.map(function (tooltipTriggerEl) {

        return new bootstrap.Tooltip(tooltipTriggerEl);

    });

}
/* =====================================================
   CHART.JS
===================================================== */

let statusChart = null;
let salesChart = null;

function initializeCharts() {

    if (typeof Chart === "undefined")
        return;

    createStatusChart();

    createSalesChart();

}


function createStatusChart() {

    const canvas = document.getElementById("statusChart");

    if (!canvas)
        return;

    if (typeof chart_status === "undefined")
        return;

    if (statusChart)
        statusChart.destroy();

    statusChart = new Chart(canvas, {

        type: "doughnut",

        data: {

            labels: Object.keys(chart_status),

            datasets: [{

                data: Object.values(chart_status),

                borderWidth: 1

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}



function createSalesChart() {

    const canvas = document.getElementById("salesChart");

    if (!canvas)
        return;

    if (typeof stock_chart === "undefined")
        return;

    if (salesChart)
        salesChart.destroy();

    salesChart = new Chart(canvas, {

        type: "bar",

        data: {

            labels: Object.keys(stock_chart),

            datasets: [{

                label: "Monthly Sales",

                data: Object.values(stock_chart)

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}


/* =====================================================
   AUTO REFRESH
===================================================== */

function initializeAutoRefresh() {

    setInterval(function () {

        checkPredictionUpdate();

        refreshDashboardStats();

    }, 30000);

}



function checkPredictionUpdate() {

    fetch("/check_update")

        .then(response => response.json())

        .then(data => {

            if (data.updated) {

                location.reload();

            }

        })

        .catch(error => {

            console.log(error);

        });

}


/* =====================================================
   LIVE DASHBOARD STATS
===================================================== */

function refreshDashboardStats() {

    fetch("/api/stats")

        .then(response => response.json())

        .then(data => {

            console.log("Dashboard Updated");

            console.log(data);

        })

        .catch(error => {

            console.log(error);

        });

}
/* =====================================================
   VOICE ALERTS
===================================================== */

function initializeVoiceAlerts() {

    const button = document.getElementById("playAlert");

    if (!button)
        return;

    button.addEventListener("click", playLatestAlerts);

}


function playLatestAlerts() {

    fetch("/alerts")

        .then(response => response.json())

        .then(data => {

            if (data.length === 0) {

                alert("No active alerts.");

                return;

            }

            let message = "";

            data.forEach(function(item){

                message +=
                    item.Itemcode +
                    " " +
                    item.Status +
                    ". ";

            });

            speak(message);

        })

        .catch(error => {

            console.log(error);

        });

}


function speak(text){

    if(!("speechSynthesis" in window))
        return;

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);

    speech.lang = "en-US";

    speech.rate = 1;

    speech.pitch = 1;

    speech.volume = 1;

    window.speechSynthesis.speak(speech);

}


/* =====================================================
   BROWSER NOTIFICATIONS
===================================================== */

function showNotification(title, body){

    if(!("Notification" in window))
        return;

    if(Notification.permission === "granted"){

        new Notification(title,{

            body:body,

            icon:"/static/images/logo.png"

        });

    }

    else if(Notification.permission !== "denied"){

        Notification.requestPermission()

        .then(function(permission){

            if(permission==="granted"){

                new Notification(title,{

                    body:body

                });

            }

        });

    }

}


/* =====================================================
   LOADING SPINNER
===================================================== */

function showLoader(){

    const loader=document.getElementById("loader");

    if(loader){

        loader.style.display="block";

    }

}


function hideLoader(){

    const loader=document.getElementById("loader");

    if(loader){

        loader.style.display="none";

    }

}


/* =====================================================
   SEARCH FILTER
===================================================== */

function filterTable(tableId,inputId){

    const input=document.getElementById(inputId);

    const table=document.getElementById(tableId);

    if(!input || !table)
        return;

    input.addEventListener("keyup",function(){

        const filter=input.value.toLowerCase();

        const rows=table.getElementsByTagName("tr");

        for(let i=1;i<rows.length;i++){

            const text=rows[i].innerText.toLowerCase();

            rows[i].style.display=

                text.indexOf(filter)>-1 ?

                "" :

                "none";

        }

    });

}


/* =====================================================
   CARD ANIMATION
===================================================== */

window.addEventListener("load",function(){

    document.querySelectorAll(".card").forEach(function(card){

        card.classList.add("fade-in");

    });

});


/* =====================================================
   LIVE CLOCK
===================================================== */

function updateClock(){

    const clock=document.getElementById("liveClock");

    if(!clock)
        return;

    const now=new Date();

    clock.innerHTML=now.toLocaleString();

}

setInterval(updateClock,1000);


/* =====================================================
   EXPORT TABLE TO CSV
===================================================== */

function exportTable(tableId,fileName){

    const table=document.getElementById(tableId);

    if(!table)
        return;

    let csv=[];

    const rows=table.querySelectorAll("tr");

    rows.forEach(function(row){

        const cols=row.querySelectorAll("td,th");

        const data=[];

        cols.forEach(function(col){

            data.push(

                '"' +

                col.innerText.replace(/"/g,'""') +

                '"'

            );

        });

        csv.push(data.join(","));

    });

    const csvFile=new Blob([csv.join("\n")],{

        type:"text/csv"

    });

    const link=document.createElement("a");

    link.download=fileName;

    link.href=URL.createObjectURL(csvFile);

    link.click();

}


/* =====================================================
   SMOOTH SCROLL
===================================================== */

document.querySelectorAll("a[href^='#']").forEach(anchor=>{

    anchor.addEventListener("click",function(e){

        e.preventDefault();

        document.querySelector(this.getAttribute("href"))

        ?.scrollIntoView({

            behavior:"smooth"

        });

    });

});


/* =====================================================
   END OF SCRIPT
===================================================== */

console.log("AI Inventory Management Loaded Successfully");
