
import os
import hmac
from datetime import timedelta
from functools import wraps

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

app = Flask(__name__)

# Required Render environment variable
app.secret_key = os.environ.get("SESSION_SECRET", "")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)


# --------------------------------------------------
# CUSTOM LOGIN PAGE
# --------------------------------------------------

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login | KICKMINER</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #0b0e11;
            color: #efeff1;
        }

        .login-card {
            width: 100%;
            max-width: 390px;
            padding: 34px;
            background: #191c21;
            border: 1px solid #2a2e35;
            border-radius: 16px;
            box-shadow: 0 20px 60px #0006;
        }

        h1 {
            margin: 0;
            text-align: center;
            font-size: 30px;
            letter-spacing: 1px;
        }

        .green { color: #53fc18; }

        .subtitle {
            margin: 12px 0 28px;
            text-align: center;
            color: #adadb8;
        }

        label {
            display: block;
            margin: 18px 0 8px;
            font-size: 14px;
        }

        input {
            width: 100%;
            padding: 13px;
            color: white;
            background: #0b0e11;
            border: 1px solid #383d45;
            border-radius: 8px;
            outline: none;
        }

        input:focus {
            border-color: #53fc18;
        }

        button {
            width: 100%;
            margin-top: 25px;
            padding: 14px;
            color: #101410;
            background: #53fc18;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover { background: #72ff42; }

        .error {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 8px;
            background: #3a1717;
            color: #ff8585;
            text-align: center;
            font-size: 14px;
        }

        .footer {
            margin-top: 24px;
            text-align: center;
            color: #777b85;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <main class="login-card">
        <h1><span class="green">KICK</span>MINER</h1>
        <p class="subtitle">Sign in to your dashboard</p>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <input type="hidden" name="csrf_token"
                   value="{{ csrf_token }}">

            <label for="username">Username</label>
            <input
                id="username"
                name="username"
                type="text"
                autocomplete="username"
                required
            >

            <label for="password">Password</label>
            <input
                id="password"
                name="password"
                type="password"
                autocomplete="current-password"
                required
            >

            <button type="submit">Sign In</button>
        </form>

        <div class="footer">KICKMINER • PRIVATE DASHBOARD</div>
    </main>
</body>
</html>
"""


# --------------------------------------------------
# AUTHENTICATION HELPERS
# --------------------------------------------------

def is_logged_in():
    return session.get("logged_in") is True


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401

            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def get_csrf_token():
    import secrets

    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token

    return token


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# --------------------------------------------------
# LOGIN AND LOGOUT
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if not app.secret_key:
        return "SESSION_SECRET is not configured", 503

    username = os.environ.get("DASHBOARD_USER", "")
    password = os.environ.get("DASHBOARD_PASSWORD", "")

    if not username or not password:
        return "Dashboard credentials are not configured", 503

    if is_logged_in():
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
                csrf_token=get_csrf_token(),
            ), 400

        submitted_user = request.form.get("username", "")
        submitted_password = request.form.get("password", "")

        username_ok = hmac.compare_digest(submitted_user, username)
        password_ok = hmac.compare_digest(
            submitted_password, password
        )

        if username_ok and password_ok:
            session.clear()
            session["logged_in"] = True
            session.permanent = True

            return redirect(url_for("dashboard"))

        return render_template_string(
            LOGIN_TEMPLATE,
            error="Invalid username or password",
            csrf_token=get_csrf_token(),
        ), 401

    return render_template_string(
        LOGIN_TEMPLATE,
        error=None,
        csrf_token=get_csrf_token(),
    )


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
# IMPORTANT:
# Replace this placeholder with your repository's
# original dashboard route and HTML template.
# Keep your existing miner integration and API logic.

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>KICKMINER Dashboard</title>
        <style>
            body {
                margin: 0;
                padding: 40px 20px;
                background: #0b0e11;
                color: #efeff1;
                font-family: Arial, sans-serif;
            }
            main { max-width: 850px; margin: auto; }
            h1 { color: #53fc18; }
            .card {
                padding: 24px;
                background: #191c21;
                border: 1px solid #2a2e35;
                border-radius: 12px;
            }
            a { color: #53fc18; }
        </style>
    </head>
    <body>
        <main>
            <h1>KICKMINER</h1>
            <div class="card">
                <h2>Dashboard login successful</h2>
                <p>Your session is authenticated.</p>
                <p>
                    Restore your original dashboard template here
                    to display live miner and points data.
                </p>
                <a href="/logout">Log out</a>
            </div>
        </main>
    </body>
    </html>
    """


# --------------------------------------------------
# PROTECT EXISTING API ROUTES
# --------------------------------------------------
# Add @login_required to each existing dashboard API
# route, for example:
#
# @app.route("/api/data")
# @login_required
# def get_data():
#     ... your existing implementation ...
#
# Do not replace your existing miner data functions
# with fabricated or empty responses.


# --------------------------------------------------
# SERVER STARTUP
# --------------------------------------------------

def start_server():
    port = int(os.environ.get("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    start_server()
