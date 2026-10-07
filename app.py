from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


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


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Register page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        try:
            connection.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "This email is already registered."

        connection.close()

        return redirect(url_for("home"))

    return render_template("register.html")


# Run the application
if __name__ == "__main__":
    create_database()
    app.run(debug=True)