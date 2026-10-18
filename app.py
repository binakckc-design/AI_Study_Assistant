
import os
import sqlite3
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

# Development secret for local testing
app.secret_key = "change-this-development-secret-key"

# Folder where uploaded PDF files will be saved
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Only PDF files are allowed
ALLOWED_EXTENSIONS = {"pdf"}


# Connect to the SQLite database
def get_db_connection():
    connection = sqlite3.connect(
        os.path.join(app.root_path, "database.db")
    )
    connection.row_factory = sqlite3.Row
    return connection


# Check whether a filename has the PDF extension
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Create the database tables
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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()

    # Ensure the uploads folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            return "Please fill in all fields."

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


# Login
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

        try:
            password_is_valid = check_password_hash(
                stored_password, password
            )
        except (ValueError, TypeError):
            password_is_valid = False

        # Support older accounts created before password hashing
        if not password_is_valid and stored_password == password:
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

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# Student dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    materials = connection.execute(
        """
        SELECT id, original_filename, upload_date
        FROM study_materials
        WHERE user_id = ?
        ORDER BY upload_date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        materials=materials
    )


# Upload study material
@app.route("/upload", methods=["POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if "file" not in request.files:
        flash("Please select a PDF file.")
        return redirect(url_for("dashboard"))

    file = request.files["file"]

    if file.filename == "":
        flash("No file was selected.")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Only PDF files are allowed.")
        return redirect(url_for("dashboard"))

    original_filename = secure_filename(file.filename)

    if not original_filename:
        flash("Invalid filename.")
        return redirect(url_for("dashboard"))

    # Generate a unique name to prevent files overwriting each other
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, stored_filename)

    try:
        file.save(file_path)

        connection = get_db_connection()
        connection.execute(
            """
            INSERT INTO study_materials
                (user_id, original_filename, stored_filename)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                original_filename,
                stored_filename
            )
        )
        connection.commit()
        connection.close()

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)

        flash("The file could not be uploaded. Please try again.")
        return redirect(url_for("dashboard"))

    flash("PDF uploaded successfully!")
    return redirect(url_for("dashboard"))


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# Run the application
if __name__ == "__main__":
    create_database()
    app.run(debug=True)
