"""
DevOps Learning Hub - Full-stack Flask application
Topics, video notes, quizzes, and certification recommendations covering DevOps end-to-end.

Run:
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000
"""
import json
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, g, flash, session

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "devops.db"

app = Flask(__name__)
app.secret_key = "change-this-in-production"


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_slug TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_slug TEXT UNIQUE NOT NULL,
            completed INTEGER DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()


# ---------- Content (loaded from JSON) ----------
def load_json(name):
    with open(BASE_DIR / "data" / name, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- Routes ----------
@app.route("/")
def home():
    topics = load_json("topics.json")
    return render_template("index.html", topics=topics)


@app.route("/topics")
def topics_list():
    topics = load_json("topics.json")
    db = get_db()
    progress = {row["topic_slug"]: row["completed"] for row in db.execute("SELECT * FROM progress")}
    return render_template("topics.html", topics=topics, progress=progress)


@app.route("/topic/<slug>")
def topic_detail(slug):
    topics = load_json("topics.json")
    topic = next((t for t in topics if t["slug"] == slug), None)
    if not topic:
        return "Topic not found", 404
    db = get_db()
    notes = db.execute(
        "SELECT * FROM notes WHERE topic_slug=? ORDER BY created_at DESC", (slug,)
    ).fetchall()
    return render_template("topic.html", topic=topic, notes=notes)


@app.route("/topic/<slug>/note", methods=["POST"])
def add_note(slug):
    content = request.form.get("content", "").strip()
    if content:
        db = get_db()
        db.execute("INSERT INTO notes (topic_slug, content) VALUES (?, ?)", (slug, content))
        db.commit()
        flash("Note saved!", "success")
    return redirect(url_for("topic_detail", slug=slug))


@app.route("/note/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    db = get_db()
    row = db.execute("SELECT topic_slug FROM notes WHERE id=?", (note_id,)).fetchone()
    db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    db.commit()
    return redirect(url_for("topic_detail", slug=row["topic_slug"]) if row else url_for("topics_list"))


@app.route("/topic/<slug>/complete", methods=["POST"])
def toggle_complete(slug):
    db = get_db()
    row = db.execute("SELECT completed FROM progress WHERE topic_slug=?", (slug,)).fetchone()
    if row:
        db.execute("UPDATE progress SET completed=? WHERE topic_slug=?", (0 if row["completed"] else 1, slug))
    else:
        db.execute("INSERT INTO progress (topic_slug, completed) VALUES (?, 1)", (slug,))
    db.commit()
    return redirect(url_for("topic_detail", slug=slug))


@app.route("/certifications")
def certifications():
    certs = load_json("certifications.json")
    return render_template("certifications.html", certs=certs)


@app.route("/quiz")
def quiz():
    questions = load_json("quiz.json")
    return render_template("quiz.html", questions=questions)


@app.route("/api/quiz/score", methods=["POST"])
def score_quiz():
    data = request.get_json() or {}
    questions = load_json("quiz.json")
    correct = 0
    for q in questions:
        if str(data.get(str(q["id"]))) == str(q["answer"]):
            correct += 1
    total = len(questions)
    pct = round(correct * 100 / total) if total else 0
    if pct >= 80:
        recommendation = "AWS DevOps Engineer Professional or CKA"
    elif pct >= 50:
        recommendation = "Docker DCA or Terraform Associate"
    else:
        recommendation = "Start with AWS Cloud Practitioner & Linux Foundation LFS101"
    return jsonify({"score": correct, "total": total, "percent": pct, "recommendation": recommendation})


@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
