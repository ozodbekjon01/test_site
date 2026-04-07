from flask import *
import sqlite3
import io

bp = Blueprint('admin', __name__)


@bp.route("/")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        user_count = conn.execute("SELECT COUNT(*) as total FROM users").fetchone()["total"]
        tests= conn.execute(""" select * from tests """).fetchall()
        
    return render_template("admin/dashboard.html", user_count=user_count, tests=tests)

@bp.route("/add_test", methods=["GET", "POST"])
def add_test():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        duration = request.form.get("duration")
        test_class = request.form.get("test_class")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        # 🔒 VALIDATSIYA
        if not title or not description:
            flash("Barcha maydonlarni to‘ldiring!", "error")
            return redirect(url_for("admin.add_test"))

        try:
            duration = int(duration)
            test_class = int(test_class)
        except:
            flash("Sonli maydonlar noto‘g‘ri!", "error")
            return redirect(url_for("admin.add_test"))

        # vaqt tekshirish
        if start_time >= end_time:
            flash("Boshlanish vaqti tugashdan oldin bo‘lishi kerak!", "error")
            return redirect(url_for("admin.add_test"))

        # DB ga yozish
        with sqlite3.connect("database.db") as conn:
            conn.execute("""
                INSERT INTO tests (title, description, duration, test_class, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, duration, test_class, start_time, end_time))
            conn.commit()

        flash("Test muvaffaqiyatli qo‘shildi!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_test.html")

@bp.route("/edit_test/<int:test_id>", methods=["GET", "POST"])
def edit_test(test_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        test = conn.execute(
            "SELECT * FROM tests WHERE id=?",
            (test_id,)
        ).fetchone()

        if not test:
            flash("Test topilmadi!", "error")
            return redirect(url_for("admin.dashboard"))

        if request.method == "POST":
            title = request.form.get("title")
            description = request.form.get("description")
            duration = request.form.get("duration")
            test_class = request.form.get("test_class")
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")

            # VALIDATSIYA
            if not title or not description:
                flash("Barcha maydonlarni to‘ldiring!", "error")
                return redirect(url_for("admin.edit_test", test_id=test_id))

            try:
                duration = int(duration)
                test_class = int(test_class)
            except:
                flash("Sonli maydonlar noto‘g‘ri!", "error")
                return redirect(url_for("admin.edit_test", test_id=test_id))

            if start_time >= end_time:
                flash("Vaqt noto‘g‘ri!", "error")
                return redirect(url_for("admin.edit_test", test_id=test_id))

            # UPDATE
            conn.execute("""
                UPDATE tests
                SET title=?, description=?, duration=?, test_class=?, start_time=?, end_time=?
                WHERE id=?
            """, (title, description, duration, test_class, start_time, end_time, test_id))

            conn.commit()
            flash("Test yangilandi!", "success")
            return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin/edit_test.html", test=test)


@bp.route("/questions/<int:test_id>")
def questions(test_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        test = conn.execute(
            "SELECT * FROM tests WHERE id=?",
            (test_id,)
        ).fetchone()

        questions = conn.execute("""
            SELECT * FROM questions
            WHERE test_id=?
        """, (test_id,)).fetchall()

    return render_template("admin/questions.html", test=test, questions=questions)


@bp.route("/add_question/<int:test_id>", methods=["GET", "POST"])
def add_question(test_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        test = conn.execute(
            "SELECT * FROM tests WHERE id=?",
            (test_id,)
        ).fetchone()

        if not test:
            flash("Test topilmadi!", "error")
            return redirect(url_for("admin.dashboard"))

        if request.method == "POST":
            title = request.form.get("title")

            answers = [
                request.form.get("answer1"),
                request.form.get("answer2"),
                request.form.get("answer3"),
                request.form.get("answer4"),
            ]

            correct = request.form.get("correct")  # 1,2,3,4

            # VALIDATSIYA
            if not title:
                flash("Savol yozilmadi!", "error")
                return redirect(request.url)

            if "" in answers:
                flash("Barcha javoblarni to‘ldiring!", "error")
                return redirect(request.url)

            if correct not in ["1", "2", "3", "4"]:
                flash("To‘g‘ri javobni tanlang!", "error")
                return redirect(request.url)

            # SAVOL qo‘shish
            cursor = conn.execute("""
                INSERT INTO questions (title, description, test_id)
                VALUES (?, ?, ?)
            """, (title, "", test_id))

            question_id = cursor.lastrowid

            # JAVOBLAR qo‘shish
            for i, ans in enumerate(answers, start=1):
                is_correct = 1 if str(i) == correct else 0

                conn.execute("""
                    INSERT INTO answers (title, description, question_id, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (ans, "", question_id, is_correct))

            conn.commit()

            flash("Savol va javoblar qo‘shildi!", "success")
            return redirect(url_for("admin.questions", test_id=test_id))

    return render_template("admin/add_question.html", test=test)




@bp.route("/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        question = conn.execute(
            "SELECT * FROM questions WHERE id=?",
            (question_id,)
        ).fetchone()

        if not question:
            flash("Savol topilmadi", "error")
            return redirect("/admin")

        if request.method == "POST":
            title = request.form["title"]

            conn.execute("""
                UPDATE questions
                SET title=?
                WHERE id=?
            """, (title, question_id))
            conn.commit()

            flash("Savol yangilandi", "success")
            return redirect(url_for("admin.questions", test_id=question["test_id"]))

    return render_template("admin/edit_question.html", question=question)


@bp.route("/delete_question/<int:question_id>")
def delete_question(question_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        question = conn.execute(
            "SELECT * FROM questions WHERE id=?",
            (question_id,)
        ).fetchone()

        if question:
            conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
            conn.commit()
            flash("Savol o‘chirildi", "success")

            return redirect(url_for("admin.questions", test_id=question["test_id"]))

    return redirect("/admin")



@bp.route("/upload_questions/<int:test_id>", methods=["POST"])
def upload_questions(test_id):

    file = request.files.get("file")

    if not file:
        flash("Fayl tanlanmadi!", "error")
        return redirect(request.referrer)

    if not file.filename.endswith(".txt"):
        flash("Faqat .txt fayl yuklash mumkin!", "error")
        return redirect(request.referrer)

    content = file.read().decode("utf-8")

    # PARSING
    questions_data = content.split("++++")

    with sqlite3.connect("database.db") as conn:
        for block in questions_data:
            block = block.strip()
            if not block:
                continue

            parts = block.split("====")

            if len(parts) < 5:
                continue  # noto‘g‘ri format skip

            question_text = parts[0].strip()

            answers = []
            correct_index = None

            for i, ans in enumerate(parts[1:5]):
                ans = ans.strip()

                if ans.startswith("#"):
                    correct_index = i
                    ans = ans[1:].strip()

                answers.append(ans)

            # VALIDATSIYA
            if not question_text or len(answers) != 4 or correct_index is None:
                continue

            # SAVOL qo‘shish
            cursor = conn.execute("""
                INSERT INTO questions (title, description, test_id)
                VALUES (?, ?, ?)
            """, (question_text, "", test_id))

            question_id = cursor.lastrowid

            # JAVOBLAR
            for i, ans in enumerate(answers):
                is_correct = 1 if i == correct_index else 0

                conn.execute("""
                    INSERT INTO answers (title, description, question_id, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (ans, "", question_id, is_correct))

        conn.commit()

    flash("Savollar muvaffaqiyatli yuklandi!", "success")
    return redirect(request.referrer)


@bp.route("/download_sample")
def download_sample():
    from flask import send_file
    import io

    sample_content = """++++
Savol 1 matni
====
# To'g'ri javob
====
Noto'g'ri javob 1
====
Noto'g'ri javob 2
====
Noto'g'ri javob 3
++++
Savol 2 matni
====
# To'g'ri javob
====
Noto'g'ri javob 1
====
Noto'g'ri javob 2
====
Noto'g'ri javob 3
"""

    return send_file(
        io.BytesIO(sample_content.encode('utf-8')),
        download_name="sample_questions.txt",
        as_attachment=True,
        mimetype="text/plain"
    )
    
    
@bp.route("/download_test/<int:test_id>")
def download_test(test_id):
    if session.get("role") != "admin":
        flash("Siz admin emassiz!", "error")
        return redirect("/auth/login")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        test = conn.execute("SELECT * FROM tests WHERE id=?", (test_id,)).fetchone()
        if not test:
            flash("Test topilmadi!", "error")
            return redirect("/admin")

        questions = conn.execute(
            "SELECT * FROM questions WHERE test_id=? ORDER BY id", (test_id,)
        ).fetchall()

        if not questions:
            flash("Testda savol mavjud emas!", "error")
            return redirect("/admin")

        content = ""
        for q in questions:
            content += "++++\n"
            content += f"{q['title']}\n"  # Savol matni
            answers = conn.execute(
                "SELECT * FROM answers WHERE question_id=? ORDER BY id", (q['id'],)
            ).fetchall()
            for a in answers:
                prefix = "# " if a['is_correct'] else ""
                content += f"====\n{prefix}{a['title']}\n"
        content += "++++\n"

        return send_file(
            io.BytesIO(content.encode("utf-8")),
            as_attachment=True,
            download_name=f"{test['title']}.txt",
            mimetype="text/plain"
        )
        
        
@bp.route("/test_ranking/<int:test_id>")
def test_ranking(test_id):
    if session.get("role") != "admin":
        flash("Siz admin emassiz!", "error")
        return redirect("/auth/login")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row

        # Testni olish
        test = conn.execute("SELECT * FROM tests WHERE id=?", (test_id,)).fetchone()
        if not test:
            flash("Test topilmadi!", "error")
            return redirect("/admin")

        # Test natijalarini olish va reyting tartibida saralash
        rankings = conn.execute("""
            SELECT u.full_name, tr.score, 
                   strftime('%s', tr.end_time) - strftime('%s', tr.start_time) as duration_seconds
            FROM test_results tr
            JOIN users u ON tr.user_id = u.id
            WHERE tr.test_id=? AND tr.completed=1
            ORDER BY tr.score DESC, duration_seconds ASC
            LIMIT 10
        """, (test_id,)).fetchall()

    return render_template("admin/test_ranking.html", test=test, rankings=rankings)



# routes/admin.py
@bp.route("/schools")
def schools_list():
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        schools = conn.execute("SELECT * FROM schools").fetchall()
    return render_template("admin/schools.html", schools=schools)

@bp.route("/add_school", methods=["GET", "POST"])
def add_school():
    if request.method == "POST":
        name = request.form["name"]
        with sqlite3.connect("database.db") as conn:
            conn.execute("INSERT INTO schools (name) VALUES (?)", (name,))
            conn.commit()
        flash("Maktab qo‘shildi!", "success")
        return redirect(url_for("admin.schools_list"))
    return render_template("admin/add_school.html")

@bp.route("/edit_school/<int:school_id>", methods=["GET", "POST"])
def edit_school(school_id):
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        school = conn.execute("SELECT * FROM schools WHERE id=?", (school_id,)).fetchone()
        if request.method == "POST":
            name = request.form["name"]
            conn.execute("UPDATE schools SET name=? WHERE id=?", (name, school_id))
            conn.commit()
            flash("Maktab yangilandi!", "success")
            return redirect(url_for("admin.schools_list"))
    return render_template("admin/edit_school.html", school=school)

@bp.route("/delete_school/<int:school_id>")
def delete_school(school_id):
    with sqlite3.connect("database.db") as conn:
        conn.execute("DELETE FROM schools WHERE id=?", (school_id,))
        conn.commit()
    flash("Maktab o‘chirildi!", "success")
    return redirect(url_for("admin.schools_list"))