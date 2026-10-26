
import os
import sqlite3
import uuid
import json
import re

from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai

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


# Load environment variables from the .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Connect to Gemini only if an API key is available
gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


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


# Find a student's own study material
def get_student_material(material_id):
    connection = get_db_connection()

    material = connection.execute(
        """
        SELECT id, original_filename, stored_filename
        FROM study_materials
        WHERE id = ? AND user_id = ?
        """,
        (material_id, session["user_id"])
    ).fetchone()

    connection.close()
    return material


# Extract readable text from a PDF
def extract_pdf_text(file_path, max_characters=30000):
    reader = PdfReader(file_path)

    text = "\n\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    return text[:max_characters]


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

    connection = None

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

    except Exception:
        if connection is not None:
            connection.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        flash("The file could not be uploaded. Please try again.")
        return redirect(url_for("dashboard"))

    finally:
        if connection is not None:
            connection.close()

    flash("PDF uploaded successfully!")
    return redirect(url_for("dashboard"))


# Read text from an uploaded PDF
@app.route("/read-pdf/<int:material_id>")
def read_pdf(material_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    material = get_student_material(material_id)

    if material is None:
        return "Study material not found.", 404

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        material["stored_filename"]
    )

    try:
        extracted_text = extract_pdf_text(file_path)

        if not extracted_text.strip():
            extracted_text = (
                "No readable text was found. "
                "This PDF may contain scanned images."
            )

    except Exception:
        app.logger.exception("PDF reading failed.")
        return "Could not read this PDF file.", 400

    return render_template(
        "read_pdf.html",
        filename=material["original_filename"],
        extracted_text=extracted_text
    )


# Generate an AI summary of an uploaded PDF
@app.route("/summarize-pdf/<int:material_id>")
def summarize_pdf(material_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if gemini_client is None:
        return "Gemini API key is missing. Please check your .env file.", 500

    material = get_student_material(material_id)

    if material is None:
        return "Study material not found.", 404

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        material["stored_filename"]
    )

    try:
        pdf_text = extract_pdf_text(file_path)

        if not pdf_text.strip():
            return (
                "No readable text was found in this PDF. "
                "Scanned PDFs may require OCR."
            ), 400

        prompt = f"""
        You are a helpful AI study assistant.

        Summarize the following study material in simple language.

        Include:
        1. The main topic
        2. Important points
        3. Key definitions
        4. Important facts students should remember
        5. A short conclusion

        Use clear headings and bullet points.
        Do not invent information that is not in the material.

        Study material:
        {pdf_text}
        """

        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        summary = response.text

        if not summary:
            return "The AI did not return a summary. Please try again.", 502

    except Exception:
        app.logger.exception("PDF summarization failed.")
        return (
            "Sorry, the PDF could not be summarized right now. "
            "Please try again later."
        ), 502

    return render_template(
        "summary.html",
        filename=material["original_filename"],
        summary=summary
    )


# Generate a multiple-choice quiz from an uploaded PDF
@app.route("/generate-quiz/<int:material_id>")
def generate_quiz(material_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if gemini_client is None:
        return "Gemini API key is missing. Please check your .env file.", 500

    material = get_student_material(material_id)

    if material is None:
        return "Study material not found.", 404

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        material["stored_filename"]
    )

    try:
        pdf_text = extract_pdf_text(file_path)

        if not pdf_text.strip():
            return (
                "No readable text was found in this PDF. "
                "Scanned PDFs may require OCR."
            ), 400

        prompt = f"""
        Create exactly 5 multiple-choice quiz questions based only
        on the study material below.

        Return ONLY valid JSON, without Markdown code fences, using
        this exact structure:

        {{
          "questions": [
            {{
              "question": "Question text",
              "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
              ],
              "answer": 0,
              "explanation": "Brief explanation"
            }}
          ]
        }}

        Rules:
        - Each question must have exactly four options.
        - The answer must be an integer from 0 to 3.
        - The answer is the zero-based index of the correct option.
        - Questions must test understanding of the supplied material.
        - Explanations must be short and accurate.
        - Do not include answers in the question text.
        - Do not invent facts outside the material.

        Study material:
        {pdf_text}
        """

        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        response_text = response.text

        if not response_text:
            raise ValueError("Gemini returned an empty quiz response.")

        # Remove optional Markdown code fences
        response_text = response_text.strip()
        response_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        quiz_data = json.loads(response_text)
        questions = quiz_data.get("questions", [])

        if len(questions) != 5:
            raise ValueError("The generated quiz did not contain 5 questions.")

        # Validate the generated questions before showing them
        for question in questions:
            if not isinstance(question.get("question"), str):
                raise ValueError("A quiz question is invalid.")

            options = question.get("options")
            answer = question.get("answer")

            if not isinstance(options, list) or len(options) != 4:
                raise ValueError("A quiz question must have 4 options.")

            if (
                not isinstance(answer, int)
                or isinstance(answer, bool)
                or answer not in range(4)
            ):
                raise ValueError("A quiz answer is invalid.")

            if not all(isinstance(option, str) for option in options):
                raise ValueError("A quiz option is invalid.")

            if not isinstance(question.get("explanation"), str):
                question["explanation"] = ""

        # Keep correct answers on the server, not in the quiz form
        session["active_quiz"] = {
            "material_id": material_id,
            "questions": questions
        }

    except Exception:
        app.logger.exception("Quiz generation failed.")
        return (
            "Sorry, the quiz could not be generated right now. "
            "Please try again."
        ), 502

    # Remove answers from the data sent to the browser
    public_questions = []

    for question in questions:
        public_questions.append({
            "question": question["question"],
            "options": question["options"]
        })

    return render_template(
        "quiz.html",
        filename=material["original_filename"],
        questions=public_questions,
        material_id=material_id
    )


# Check quiz answers and calculate the score
@app.route("/submit-quiz/<int:material_id>", methods=["POST"])
def submit_quiz(material_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    active_quiz = session.get("active_quiz")

    if (
        not active_quiz
        or active_quiz.get("material_id") != material_id
    ):
        flash("Please generate a new quiz before submitting answers.")
        return redirect(
            url_for("generate_quiz", material_id=material_id)
        )

    questions = active_quiz["questions"]
    results = []
    score = 0

    for index, question in enumerate(questions):
        submitted_answer = request.form.get(f"question_{index}")

        try:
            selected_index = int(submitted_answer)
        except (TypeError, ValueError):
            selected_index = -1

        if selected_index not in range(4):
            selected_index = -1

        correct_index = question["answer"]
        is_correct = selected_index == correct_index

        if is_correct:
            score += 1

        results.append({
            "question": question["question"],
            "options": question["options"],
            "selected": selected_index,
            "correct": correct_index,
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })

    # Remove the active quiz after submission
    session.pop("active_quiz", None)

    return render_template(
        "quiz_result.html",
        filename=get_material_filename(material_id),
        results=results,
        score=score,
        total=len(questions)
    )


# Get the filename only for the logged-in student's own PDF
def get_material_filename(material_id):
    material = get_student_material(material_id)

    if material is None:
        return "Study Material"

    return material["original_filename"]


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# Run the application
if __name__ == "__main__":
    create_database()
    app.run(debug=True)
