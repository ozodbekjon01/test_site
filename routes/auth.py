import sqlite3
from flask import *

bp = Blueprint('auth', __name__)




@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password)
            ).fetchone()

        if user:
            session.permanent = True
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")

        # ❗ XATO HOLAT
        flash("Login yoki parol noto‘g‘ri", "error")

    return render_template("auth/login.html")




@bp.route("/register", methods=["GET", "POST"])
def register_user():
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        if request.method == "POST":
            full_name = request.form["full_name"].strip()
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            class_number = request.form["class_number"]
            school_id = request.form["school_id"]

            role = "student"

            # 🔴 VALIDATSIYA
            if len(full_name) < 3:
                flash("Ism juda qisqa", "error")
                return redirect(url_for("auth.register_user"))

            if len(username) < 3:
                flash("Username kamida 3 ta belgidan iborat bo‘lishi kerak", "error")
                return redirect(url_for("auth.register_user"))

            if len(password) < 5:
                flash("Parol kamida 5 ta belgidan iborat bo‘lishi kerak", "error")
                return redirect(url_for("auth.register_user"))

            if not class_number.isdigit() or not (1 <= int(class_number) <= 11):
                flash("Sinf 1 dan 11 gacha bo‘lishi kerak", "error")
                return redirect(url_for("auth.register_user"))

            # 🔴 USERNAME TEKSHIRISH
            existing_user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing_user:
                flash("Bu username band!", "error")
                return redirect(url_for("auth.register_user"))

            # ✅ INSERT
            conn.execute("""
                INSERT INTO users (full_name, username, password, class_number, role, school_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, username, password, class_number, role, school_id))

            conn.commit()

            flash("Ro‘yxatdan muvaffaqiyatli o‘tdingiz!", "success")
            return redirect(url_for("auth.login"))

        schools = conn.execute("SELECT * FROM schools").fetchall()

    return render_template("auth/register.html", schools=schools)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")