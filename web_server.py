import threading
import json
import os
import hmac
import secrets

from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask,
    render_template_string,
    jsonify,
    request,
    redirect,
    url_for,
    session,
)
from loguru import logger

app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_SECRET", "")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)


LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KICKMINER Login</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; min-height: 100vh; display: grid;
    place-items: center; padding: 20px;
    background: #0b0e11; color: #efeff1;
    font-family: Arial, sans-serif;
}
.card {
    width: 100%; max-width: 390px; padding: 32px;
    background: #191c21; border: 1px solid #2a2e35;
    border-radius: 16px;
}
h1 { text-align: center; }
.green { color: #53fc18; }
p { text-align: center; color: #adadb8; }
label { display: block; margin: 18px 0 8px; }
input {
    width: 100%; padding: 12px; border-radius: 8px;
    border: 1px solid #383d45; background: #0b0e11;
    color: white;
}
button {
    width: 100%; padding: 13px; margin-top: 24px;
    border: 0; border-radius: 8px;
    background: #53fc18; font-weight: bold; cursor: pointer;
}
.error { color: #ff7777; text-align: center; }
</style>
</head>
<body>
<div class="card">
    <h1><span class="green">KICK</span>MINER</h1>
    <p>Sign in to your dashboard</p>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="POST" action="/login">
        <input type="hidden" name="csrf_token" value="{{ csrf }}">
        <label for="username">Username</label>
        <input id="username" name="username"
               autocomplete="username" required>
        <label for="password">Password</label>
        <input id="password" name="password" type="password"
               autocomplete="current-password" required>
        <button type="submit">Sign In</button>
    </form>
</div>
</body>
</html>
"""


@app.before_request
def check_dashboard_login():
    # Health checks must work without a login.
    if request.endpoint in ("health", "login"):
        return None

    if not session.get("logged_in"):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required"}), 401
        return redirect(url_for("login"))


@app.route("/health")
def health():
    return "OK", 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if not app.secret_key:
        return "SESSION_SECRET is missing in Render", 503

    username = os.environ.get("DASHBOARD_USER", "")
    password = os.environ.get("DASHBOARD_PASSWORD", "")

    if not username or not password:
        return "Dashboard credentials are not configured", 503

    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        submitted_csrf = request.form.get("csrf_token", "")
        expected_csrf = session.get("csrf_token", "")

        if not expected_csrf or not hmac.compare_digest(
            submitted_csrf, expected_csrf
        ):
            return render_template_string(
                LOGIN_TEMPLATE,
                error="Session expired. Please try again.",
                csrf=secrets.token_urlsafe(32),
            ), 400

        user_ok = hmac.compare_digest(
            request.form.get("username", ""), username
        )
        pass_ok = hmac.compare_digest(
            request.form.get("password", ""), password
        )

        if user_ok and pass_ok:
            session.clear()
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("dashboard"))

        return render_template_string(
            LOGIN_TEMPLATE,
            error="Invalid username or password",
            csrf=secrets.token_urlsafe(32),
        ), 401

    csrf = secrets.token_urlsafe(32)
    session["csrf_token"] = csrf
    return render_template_string(
        LOGIN_TEMPLATE, error=None, csrf=csrf
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))
    
@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)


def start_server(streamers_data, port=5000):
    global _account_manager

    # Prefer Render's assigned port when available.
    port = int(os.environ.get("PORT", port))

    if hasattr(streamers_data, "get_all_status"):
        _account_manager = streamers_data
        with data_lock:
            names = _account_manager.get_all_streamers_flat()
            shared_context["streamers"] = {s: "" for s in names}
            shared_context["points"] = {s: 0 for s in names}
            shared_context["last_update"] = {s: "N/A" for s in names}
            shared_context["stream_status"] = {
                s: "offline" for s in names
            }
            shared_context["status"] = "Active"

    elif isinstance(streamers_data, list):
        with data_lock:
            shared_context["streamers"] = {
                s: "" for s in streamers_data
            }
            shared_context["points"] = {
                s: 0 for s in streamers_data
            }
            shared_context["last_update"] = {
                s: "N/A" for s in streamers_data
            }
            shared_context["stream_status"] = {
                s: "offline" for s in streamers_data
            }
            shared_context["status"] = "Active"

    elif isinstance(streamers_data, dict):
        with data_lock:
            shared_context["streamers"] = streamers_data
            shared_context["status"] = "Active"

    def run():
        import logging
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        logger.info(
            f"Dashboard starting on 0.0.0.0:{port}"
        )
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
        )

    threading.Thread(target=run, daemon=True).start()
