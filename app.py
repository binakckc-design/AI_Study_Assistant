
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Development secret for Flask sessions.
# We will move this to an environment variable later.
app.secret_key = "change-this-development-secret-key"


# Connect to the SQLite database
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Create the users table
def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Register page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            return "Please fill in all fields."

        # Hash the password before saving it
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "This email is already registered."

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user is None:
            connection.close()
            return "Invalid email or password."

        stored_password = user["password"]

        # Check a securely hashed password.
        # The fallback supports accounts created by our old version.
        try:
            password_is_valid = check_password_hash(
                stored_password, password
            )
        except (ValueError, TypeError):
            password_is_valid = False

        if not password_is_valid and stored_password == password:
            # Upgrade an old plain-text password after successful login.
            new_hash = generate_password_hash(password)

            connection.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_hash, user["id"])
            )
            connection.commit()
            password_is_valid = True

        connection.close()

        if not password_is_valid:
            return "Invalid email or password."

        # Remember the logged-in user
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# Student dashboard (only logged-in users can access it)
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# Run the application
if __name__ == "__main__":
    create_database()
    app.run(debug=True)