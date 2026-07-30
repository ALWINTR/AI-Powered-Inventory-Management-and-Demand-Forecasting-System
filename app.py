from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
    flash
)

import pandas as pd
import os
import subprocess
from functools import wraps
from datetime import datetime

# ======================================================
# FLASK CONFIGURATION
# ======================================================

app = Flask(__name__)

app.secret_key = "AIInventory@2026"

# ======================================================
# FILE PATHS
# ======================================================

MERGED_FILE = "merged_sales.xlsx"
PREDICTION_FILE = "predictions.xlsx"

# ======================================================
# LOGIN
# ======================================================

USERNAME = "admin"
PASSWORD = "admin123"

# ======================================================
# LOGIN REQUIRED
# ======================================================

def login_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        if "user" not in session:

            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated

# ======================================================
# LOAD INVENTORY
# ======================================================

def load_inventory():

    if os.path.exists(MERGED_FILE):

        df = pd.read_excel(MERGED_FILE)

        return df

    return pd.DataFrame()

# ======================================================
# LOAD PREDICTIONS
# ======================================================

def load_predictions():

    if os.path.exists(PREDICTION_FILE):

        df = pd.read_excel(PREDICTION_FILE)

        return df

    return pd.DataFrame()

# ======================================================
# DASHBOARD STATISTICS
# ======================================================

def dashboard_stats(inv_df, pred_df):

    stats = {}

    stats["total_items"] = len(inv_df)

    if inv_df.empty:

        stats["stock"] = 0

    else:

        stats["stock"] = int(inv_df["Balance"].sum())

    if pred_df.empty:

        stats["purchase_required"] = 0
        stats["dead_stock"] = 0
        stats["stock_out"] = 0
        stats["slow"] = 0
        stats["overstock"] = 0

    else:

        stats["purchase_required"] = len(
            pred_df[
                pred_df["Status"] == "Purchase Required"
            ]
        )

        stats["dead_stock"] = len(
            pred_df[
                pred_df["Status"] == "Dead Stock"
            ]
        )

        stats["stock_out"] = len(
            pred_df[
                pred_df["Status"] == "Stock Out"
            ]
        )

        stats["slow"] = len(
            pred_df[
                pred_df["Status"] == "Slow Moving"
            ]
        )

        stats["overstock"] = len(
            pred_df[
                pred_df["Status"] == "Overstock"
            ]
        )

    return stats

# ======================================================
# LOGIN PAGE
# ======================================================

@app.route("/", methods=["GET", "POST"])

def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        if username == USERNAME and password == PASSWORD:

            session["user"] = username

            return redirect(url_for("dashboard"))

        flash("Invalid Username or Password")

    return render_template("login.html")

# ======================================================
# LOGOUT
# ======================================================

@app.route("/logout")

def logout():

    session.clear()

    return redirect(url_for("login"))
    # ======================================================
# DASHBOARD
# ======================================================

@app.route("/dashboard")
@login_required
def dashboard():

    inventory = load_inventory()

    prediction = load_predictions()

    stats = dashboard_stats(
        inventory,
        prediction
    )

    # -----------------------------
    # Recent Alerts
    # -----------------------------

    if prediction.empty:

        alerts = []

    else:

        alerts = prediction[
            prediction["Status"] != "OK"
        ].head(10).to_dict("records")

    # -----------------------------
    # Purchase Required
    # -----------------------------

    if prediction.empty:

        purchase_items = []

    else:

        purchase_items = prediction[
            prediction["Status"] == "Purchase Required"
        ].head(10).to_dict("records")

    # -----------------------------
    # Dead Stock
    # -----------------------------

    if prediction.empty:

        dead_stock = []

    else:

        dead_stock = prediction[
            prediction["Status"] == "Dead Stock"
        ].head(10).to_dict("records")

    # -----------------------------
    # Inventory Table
    # -----------------------------

    inventory_table = inventory.to_dict(
        "records"
    )

    prediction_table = prediction.to_dict(
        "records"
    )

    # -----------------------------
    # Charts
    # -----------------------------

    chart_status = {}

    if not prediction.empty:

        chart_status = prediction[
            "Status"
        ].value_counts().to_dict()

    stock_chart = {}

    if not inventory.empty:

        stock_chart = (

            inventory

            .groupby("Month")["Sales"]

            .sum()

            .to_dict()

        )

    # -----------------------------
    # Dashboard
    # -----------------------------

    return render_template(

        "dashboard.html",

        stats=stats,

        inventory=inventory_table,

        predictions=prediction_table,

        alerts=alerts,

        purchase_items=purchase_items,

        dead_stock=dead_stock,

        chart_status=chart_status,

        stock_chart=stock_chart,

        current_time=datetime.now()

    )

# ======================================================
# INVENTORY PAGE
# ======================================================

@app.route("/inventory")
@login_required
def inventory():

    df = load_inventory()

    return render_template(

        "inventory.html",

        inventory=df.to_dict("records")

    )

# ======================================================
# PREDICTIONS PAGE
# ======================================================

@app.route("/predictions")
@login_required
def predictions():

    df = load_predictions()

    return render_template(

        "predictions.html",

        predictions=df.to_dict("records")

    )
    # ======================================================
# UPLOAD INVENTORY
# ======================================================

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if request.method == "POST":

        file = request.files.get("file")

        if file is None or file.filename == "":

            flash("Please select an Excel file.")

            return redirect(url_for("upload"))

        filename = "merged_sales.xlsx"

        file.save(filename)

        try:

            subprocess.run(

                ["python", "prediction.py"],

                check=True

            )

            flash("Inventory uploaded and predictions updated.")

        except Exception as e:

            flash(f"Prediction Error : {e}")

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# ======================================================
# RUN AI PREDICTION
# ======================================================

@app.route("/run_prediction")
@login_required
def run_prediction():

    try:

        subprocess.run(

            ["python", "prediction.py"],

            check=True

        )

        flash("Prediction completed successfully.")

    except Exception as e:

        flash(str(e))

    return redirect(url_for("dashboard"))


# ======================================================
# PURCHASE RECOMMENDATION
# ======================================================

@app.route("/purchase")
@login_required
def purchase():

    df = load_predictions()

    if not df.empty:

        df = df[
            df["Status"] == "Purchase Required"
        ]

        df = df.sort_values(

            "Purchase_Qty",

            ascending=False

        )

    return render_template(

        "purchase.html",

        items=df.to_dict("records")

    )


# ======================================================
# DEAD STOCK
# ======================================================

@app.route("/deadstock")
@login_required
def deadstock():

    df = load_predictions()

    if not df.empty:

        df = df[
            df["Dead_Stock"] == "YES"
        ]

    return render_template(

        "deadstock.html",

        items=df.to_dict("records")

    )


# ======================================================
# STOCK OUT
# ======================================================

@app.route("/stockout")
@login_required
def stockout():

    df = load_predictions()

    if not df.empty:

        df = df[
            df["Status"] == "Stock Out"
        ]

    return render_template(

        "stockout.html",

        items=df.to_dict("records")

    )


# ======================================================
# DOWNLOAD PREDICTIONS
# ======================================================

@app.route("/download_predictions")
@login_required
def download_predictions():

    if os.path.exists(PREDICTION_FILE):

        return send_file(

            PREDICTION_FILE,

            as_attachment=True

        )

    flash("Prediction file not found.")

    return redirect(url_for("dashboard"))


# ======================================================
# DOWNLOAD INVENTORY
# ======================================================

@app.route("/download_inventory")
@login_required
def download_inventory():

    if os.path.exists(MERGED_FILE):

        return send_file(

            MERGED_FILE,

            as_attachment=True

        )

    flash("Inventory file not found.")

    return redirect(url_for("dashboard"))
    # ======================================================
# API : DASHBOARD STATS
# ======================================================

@app.route("/api/stats")
@login_required
def api_stats():

    inventory = load_inventory()

    prediction = load_predictions()

    return jsonify(
        dashboard_stats(
            inventory,
            prediction
        )
    )


# ======================================================
# API : INVENTORY
# ======================================================

@app.route("/api/inventory")
@login_required
def api_inventory():

    df = load_inventory()

    return jsonify(
        df.to_dict("records")
    )


# ======================================================
# API : PREDICTIONS
# ======================================================

@app.route("/api/predictions")
@login_required
def api_predictions():

    df = load_predictions()

    return jsonify(
        df.to_dict("records")
    )


# ======================================================
# CHECK FOR UPDATED PREDICTION FILE
# ======================================================

@app.route("/check_update")
@login_required
def check_update():

    if os.path.exists(PREDICTION_FILE):

        modified = os.path.getmtime(
            PREDICTION_FILE
        )

        return jsonify({

            "updated": True,

            "last_modified": modified

        })

    return jsonify({

        "updated": False

    })


# ======================================================
# VOICE ALERTS
# ======================================================

@app.route("/alerts")
@login_required
def alerts():

    df = load_predictions()

    if df.empty:

        return jsonify([])

    alerts = df[
        df["Status"] != "OK"
    ][[
        "Itemcode",
        "Status",
        "Purchase_Qty"
    ]]

    return jsonify(
        alerts.to_dict("records")
    )


# ======================================================
# HEALTH CHECK
# ======================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "Running",

        "application": "AI Inventory Management",

        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    })


# ======================================================
# ERROR HANDLERS
# ======================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_error(error):

    return render_template(
        "500.html"
    ), 500


# ======================================================
# AUTO RUN PREDICTION
# ======================================================

def initialize_prediction():

    if not os.path.exists(PREDICTION_FILE):

        try:

            subprocess.run(

                ["python", "prediction.py"],

                check=True

            )

            print("Prediction file generated.")

        except Exception as e:

            print("Prediction Error:", e)


# ======================================================
# START APPLICATION
# ======================================================

if __name__ == "__main__":

    initialize_prediction()

    print("=" * 60)
    print("AI INVENTORY MANAGEMENT SYSTEM")
    print("=" * 60)
    print("Server Started Successfully")
    print("URL : http://127.0.0.1:5000")
    print("=" * 60)

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
