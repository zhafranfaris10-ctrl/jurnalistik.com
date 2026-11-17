import os
import sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "jurnalistik.db"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-secret-key-sebelum-online")
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
UPLOAD_DIR.mkdir(exist_ok=True)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Menunggu',
                score INTEGER,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        existing = conn.execute("SELECT id FROM admins WHERE username = ?", ("admin",)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                ("admin", generate_password_hash("jurnalistikmode"))
            )

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Silakan login sebagai admin terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    with db() as conn:
        articles = conn.execute(
            "SELECT * FROM submissions WHERE status='Diterbitkan' ORDER BY created_at DESC LIMIT 6"
        ).fetchall()
    return render_template("index.html", articles=articles)

@app.route("/karya")
def karya():
    with db() as conn:
        works = conn.execute(
            "SELECT * FROM submissions WHERE status='Diterbitkan' ORDER BY created_at DESC"
        ).fetchall()
    return render_template("karya.html", works=works)

@app.route("/pengumpulan", methods=["GET", "POST"])
def pengumpulan():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        class_name = request.form.get("class_name", "").strip()
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        file = request.files.get("file")

        if not all([name, class_name, title, category, file]) or not file.filename:
            flash("Lengkapi semua data dan pilih file karya.", "warning")
            return redirect(url_for("pengumpulan"))
        if not allowed_file(file.filename):
            flash("Format file harus PDF, DOC, DOCX, JPG, JPEG, atau PNG.", "danger")
            return redirect(url_for("pengumpulan"))

        safe_name = secure_filename(file.filename)
        stored_name = f"{os.urandom(8).hex()}_{safe_name}"
        file.save(UPLOAD_DIR / stored_name)
        with db() as conn:
            conn.execute("""
                INSERT INTO submissions (name, class_name, title, category, description, filename)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, class_name, title, category, description, stored_name))
        flash("Karya berhasil dikirim dan menunggu penilaian admin.", "success")
        return redirect(url_for("pengumpulan"))
    return render_template("pengumpulan.html")

@app.route("/saran", methods=["GET", "POST"])
def saran():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        if not message:
            flash("Pesan saran tidak boleh kosong.", "warning")
        else:
            with db() as conn:
                conn.execute("INSERT INTO suggestions (name, message) VALUES (?, ?)", (name, message))
            flash("Terima kasih! Saran kamu sudah dikirim.", "success")
            return redirect(url_for("saran"))
    return render_template("saran.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as conn:
            admin = conn.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin"))
        flash("Username atau password salah.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":
        submission_id = request.form.get("submission_id", type=int)
        status = request.form.get("status", "Menunggu")
        score = request.form.get("score", type=int)
        feedback = request.form.get("feedback", "").strip()
        if status not in {"Menunggu", "Ditolak", "Diterbitkan"}:
            abort(400)
        if score is not None and not 0 <= score <= 100:
            flash("Nilai harus antara 0 sampai 100.", "warning")
        else:
            with db() as conn:
                conn.execute(
                    "UPDATE submissions SET status=?, score=?, feedback=? WHERE id=?",
                    (status, score, feedback, submission_id)
                )
            flash("Penilaian berhasil disimpan.", "success")
        return redirect(url_for("admin"))
    with db() as conn:
        submissions = conn.execute("SELECT * FROM submissions ORDER BY created_at DESC").fetchall()
        suggestions = conn.execute("SELECT * FROM suggestions ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", submissions=submissions, suggestions=suggestions)

@app.route("/admin/file/<path:filename>")
@admin_required
def admin_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.route("/karya/file/<int:submission_id>")
def karya_file(submission_id):
    with db() as conn:
        item = conn.execute(
            "SELECT filename FROM submissions WHERE id=? AND status='Diterbitkan'",
            (submission_id,)
        ).fetchone()
    if not item:
        abort(404)
    return send_from_directory(UPLOAD_DIR, item["filename"], as_attachment=True)

@app.errorhandler(413)
def too_large(_error):
    flash("Ukuran file maksimal 10 MB.", "danger")
    return redirect(url_for("pengumpulan"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
