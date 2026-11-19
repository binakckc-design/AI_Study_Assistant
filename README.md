# AI Study Assistant 📚

A web-based AI-powered learning application that helps students understand and revise their study materials more effectively.

## 📌 About the Project

AI Study Assistant is a web-based application developed as a BCA 6th Semester academic project at Swastik College, affiliated with Tribhuvan University (TU), Nepal.

The application allows students to upload PDF study materials, read extracted content, generate AI-powered summaries, and create multiple-choice quizzes using Google's Gemini API.

The main goal of this project is to make studying easier, more interactive, and more efficient through Artificial Intelligence.

## ✨ Features

- **User Registration:** Students can create their own accounts.
- **User Login:** Secure login using password hashing and session management.
- **Student Dashboard:** View uploaded study materials and available actions.
- **PDF Upload:** Upload PDF study materials to the application.
- **PDF Reading:** Extract and display text from uploaded PDF files.
- **AI-Powered Summarization:** Generate summaries of uploaded study materials using Google Gemini.
- **AI Quiz Generation:** Generate multiple-choice questions based on uploaded PDF content.
- **Quiz Results:** View quiz results and feedback where supported by the application.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML | Webpage structure |
| CSS | Website styling |
| SQLite | Database management |
| Google Gemini API | AI-powered summarization and quiz generation |
| PyPDF | PDF text extraction |
| Visual Studio Code | Development environment |
| Git and GitHub | Version control and project hosting |

## 📂 Project Structure

```text
AI_Study_Assistant/
│
├── app.py
├── requirements.txt
├── test_gemini.py
├── .gitignore
│
├── static/
│   └── style.css
│
├── templates/
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── read_pdf.html
│   ├── summary.html
│   ├── quiz.html
│   └── quiz_result.html
│
├── uploads/
├── database.db
├── .env
└── venv/
```

*Note: The `.env`, `database.db`, `uploads/`, and `venv/` directories or files are local development resources and are excluded from GitHub.*

## ⚙️ Installation and Setup

Follow these steps to run the project on your local computer.

### 1. Clone the Repository

```bash
git clone https://github.com/binakckc-design/AI_Study_Assistant.git
```

### 2. Open the Project Folder

```bash
cd AI_Study_Assistant
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Required Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the Gemini API Key

Create a `.env` file in the project's root directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace `your_gemini_api_key` with your own API key.

Keep your API key private. Never upload the `.env` file to GitHub.

### 7. Run the Application

```bash
python app.py
```

### 8. Open the Application

Open your web browser and visit:

```text
http://127.0.0.1:5000/
```

You can now register an account and start using the application.

## 🔐 Security Notes

- Passwords are stored using password hashing.
- User sessions are used for authentication.
- Uploaded PDF files are validated by the application.
- API credentials are stored in environment variables.
- The `.env` file is excluded from version control.

## 🚀 Future Enhancements

The project can be improved further by introducing:

- Flashcard generation from uploaded study materials.
- Support for additional document formats.
- Student learning progress tracking.
- More quiz formats and difficulty levels.
- Improved AI-generated explanations.
- User profile management.

## 🎓 Academic Information

**Project Name:** AI Study Assistant  
**Program:** Bachelor of Computer Applications (BCA)  
**Semester:** Sixth Semester  
**College:** Swastik College  
**University:** Tribhuvan University (TU), Nepal  

## 👩‍💻 Author

**Bina Kc**

GitHub: [binakckc-design](https://github.com/binakckc-design)

---

*Developed as an academic project to explore the use of Artificial Intelligence in education and student learning.*
