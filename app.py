# app.py  -  the Flask backend (the "waiter"), now with a login desk
import json
import math
import os
import secrets
from functools import wraps

import joblib
import pandas as pd
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, session, url_for)

import auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_secret_key():
    """The secret used to sign the login 'wristbands'. Created once and reused."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    path = os.path.join(BASE_DIR, "secret_key.txt")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__)
app.config["SECRET_KEY"] = load_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True     # JavaScript cannot read the cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"    # not sent along with other sites' forms

auth.init_db()                                   # make sure the guest book exists

MODEL_PATH = "model/best_model.joblib"
METRICS_PATH = "model/metrics.json"

# ---------- Load the saved model and its report card once, at start-up ----------
try:
    model = joblib.load(MODEL_PATH)
    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    print("Model loaded:", metrics["best_model"])
except FileNotFoundError:
    model = None
    metrics = {}
    print("WARNING: model files not found. Run  python train_model.py  first.")

# ---------- The rules each input must follow ----------
DEPARTMENTS = ["CSE", "IT", "ECE", "Mechanical", "Civil"]
GENDERS = ["Male", "Female"]
NUMBER_RULES = {
    # field name: (smallest allowed, largest allowed, label for messages)
    "Attendance_Pct": (0, 100, "Attendance (%)"),
    "Study_Hours": (0, 16, "Study hours per day"),
    "Previous_Score": (0, 100, "Previous score"),
    "Assignments_Completed": (0, 10, "Assignments completed"),
}


# ---------- The rope at the door: who is allowed in? ----------
def login_required(view):
    """For web pages: visitors without a wristband are sent to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def api_login_required(view):
    """For the JSON route: visitors without a wristband get a 401 message."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Please log in first."}), 401
        return view(*args, **kwargs)
    return wrapper


def validate(data):
    """Check the form data. Returns (clean_values, errors)."""
    clean, errors = {}, {}

    if data.get("Gender") not in GENDERS:
        errors["Gender"] = "Please choose Male or Female."
    else:
        clean["Gender"] = data["Gender"]

    if data.get("Department") not in DEPARTMENTS:
        errors["Department"] = "Please choose a department from the list."
    else:
        clean["Department"] = data["Department"]

    for field, (low, high, label) in NUMBER_RULES.items():
        raw = data.get(field)
        if raw is None or str(raw).strip() == "":
            errors[field] = f"{label} is required."
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors[field] = f"{label} must be a number."
            continue
        if math.isnan(value) or math.isinf(value):
            errors[field] = f"{label} must be a real number."
        elif not (low <= value <= high):
            errors[field] = f"{label} must be between {low} and {high}."
        else:
            clean[field] = value

    return clean, errors


def get_category(grade):
    if grade >= 16:
        return "Excellent"
    if grade >= 13:
        return "Good"
    if grade >= 10:
        return "Average"
    return "Needs Improvement"


def get_suggestions(values, grade):
    tips = []
    if values["Study_Hours"] < 3:
        tips.append("Try to study at least 3 to 4 hours a day, in short focused sessions with breaks.")
    if values["Attendance_Pct"] < 75:
        tips.append("Raise your attendance above 75%. Missing classes means missing explanations.")
    if values["Assignments_Completed"] < 7:
        tips.append("Complete more of your assignments. They are the best regular practice you get.")
    if values["Previous_Score"] < 50:
        tips.append("Revise the basics from last term and ask your teacher about the topics you find hard.")
    if grade < 10:
        tips.append("Make a weekly study timetable and ask a teacher or friend for help early.")
    if not tips and grade >= 13:
        tips.append("You are on a strong track. Keep your routine and try helping classmates, which deepens your own learning.")
    elif not tips:
        tips.append("Your habits look reasonable. To move up a level, add one extra revision session a week and practise past questions.")
    return tips[:4]


# ---------- Login routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("register.html", errors={}, form={})

    form = {
        "name": request.form.get("name", ""),
        "email": request.form.get("email", ""),
    }
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    errors = auth.validate_registration(form["name"], form["email"], password, confirm)
    if not errors:
        created, problem = auth.create_user(form["name"], form["email"], password)
        if not created:
            errors["email"] = problem
    if errors:
        return render_template("register.html", errors=errors, form=form), 400

    flash("Account created! Please log in.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("login.html", error=None, email="")

    email = request.form.get("email", "")
    password = request.form.get("password", "")

    user = auth.check_login(email, password)
    if user is None:
        # Same message whether the email or the password was wrong (do not help guessers)
        return render_template("login.html", error="Incorrect email or password.",
                               email=email), 401

    session.clear()                          # start a fresh wristband
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("home"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Predictor routes ----------
@app.route("/")
@login_required
def home():
    return render_template("index.html", departments=DEPARTMENTS, genders=GENDERS,
                           user_name=session.get("user_name", ""))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": model is not None})


@app.route("/api/metrics")
@api_login_required
def get_metrics():
    if model is None:
        return jsonify({"error": "Model not found. Run train_model.py first."}), 503
    return jsonify(metrics)


@app.route("/predict", methods=["POST"])
@api_login_required
def predict():
    if model is None:
        return jsonify({"error": "Model not found. Run train_model.py first."}), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Please send the form data as JSON."}), 400

    values, errors = validate(data)
    if errors:
        return jsonify({"error": "Please fix the highlighted fields.", "fields": errors}), 400

    row = pd.DataFrame([values])
    grade = float(model.predict(row)[0])
    grade = round(min(max(grade, 0), 20), 1)      # keep it between 0 and 20

    return jsonify({
        "predicted_grade": grade,
        "out_of": 20,
        "category": get_category(grade),
        "suggestions": get_suggestions(values, grade),
        "model_name": metrics.get("best_model"),
        "metrics": metrics.get("results", {}),
    })


# ---------- Friendly error pages (JSON instead of ugly crashes) ----------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page not found."}), 404


@app.errorhandler(405)
def wrong_method(error):
    return jsonify({"error": "Wrong request method for this address."}), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Something went wrong on the server."}), 500


if __name__ == "__main__":
    app.run(debug=True)