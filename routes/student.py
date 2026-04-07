from flask import *
import sqlite3
from datetime import datetime
dt_str = "2026-04-09T01:00"
dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
print(dt_obj)  # datetime.datetime(2026, 4, 9, 1, 0)

bp = Blueprint('student', __name__)

def login_required(f):
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "student":
            return redirect("/login")
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@bp.route("/")
def student_dashboard():
    user_id = session.get("user_id")  # foydalanuvchi ID

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        tests = conn.execute("SELECT * FROM tests").fetchall()
        results = conn.execute(
            """
            SELECT id, test_id, completed, start_time, end_time
            FROM test_results
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()

    tests_list = []
    for test in tests:
        test_dict = dict(test)

        # SQL dan olingan stringlarni datetime ga aylantirish
        test_dict["start_time_dt"] = datetime.strptime(test_dict["start_time"], "%Y-%m-%dT%H:%M")
        test_dict["end_time_dt"] = datetime.strptime(test_dict["end_time"], "%Y-%m-%dT%H:%M")
        # O'quvchi natijasi
        res_completed = next(
            (r for r in results if r["test_id"] == test_dict["id"] and r["completed"] == 1),
            None
        )

        res_started = next(
            (r for r in results if r["test_id"] == test_dict["id"]),
            None
        )

        res = res_completed if res_completed else res_started
        test_dict["started"] = True if res and res["start_time"] else False
        test_dict["completed"] = bool(res["completed"]) if res else False
        test_dict["result_id"] = res["id"] if res and "id" in res.keys() else None
        def parse_dt(dt):
            return datetime.fromisoformat(dt) if dt else None

        test_dict["result_start"] = parse_dt(res["start_time"]) if res else None
        test_dict["result_end"] = parse_dt(res["end_time"]) if res else None
        tests_list.append(test_dict)

    current_time = datetime.now()
    return render_template(
        "student/dashboard.html",
        tests=tests_list,
        current_time=current_time
    )
    





def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@bp.route('/start_test/<int:test_id>')
def start_test(test_id):
    if 'user_id' not in session:
        flash("Avval tizimga kiring", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Testni tekshirish
    c.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    test = c.fetchone()
    if not test:
        flash("Test topilmadi", "error")
        return redirect(url_for('student.student_dashboard'))

    now = datetime.now()
    start_time = datetime.strptime(test['start_time'], "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(test['end_time'], "%Y-%m-%dT%H:%M")

    if now < start_time:
        flash("Test boshlanish vaqti hali kelmagan", "error")
        return redirect(url_for('student.student_dashboard'))
    elif now > end_time:
        flash("Test muddati tugagan", "error")
        return redirect(url_for('student.student_dashboard'))

    # Foydalanuvchi allaqachon topshirganligini tekshirish
    c.execute("""
        SELECT * FROM test_results 
        WHERE user_id=? AND test_id=? AND completed=1
    """, (user_id, test_id))
    res = c.fetchone()
    if res:
        flash("Siz bu testni allaqachon topshirdingiz", "success")
        return redirect(url_for('student.student_dashboard'))

    # Yangi test natijasini yaratish (topshirish boshlanadi)
    c.execute("""
        INSERT INTO test_results (user_id, test_id, start_time, completed)
        VALUES (?, ?, ?, 0)
    """, (user_id, test_id, now))
    conn.commit()
    result_id = c.lastrowid

    # Endi foydalanuvchi test sahifasiga yo‘naltiriladi
    return redirect(url_for('student.take_test', result_id=result_id))



import random
from datetime import datetime

import random
from datetime import datetime

@bp.route('/take_test/<int:result_id>', methods=['GET', 'POST'])
def take_test(result_id):
    if 'user_id' not in session:
        flash("Avval tizimga kiring", "error")
        return redirect(url_for('auth.login'))

    conn = get_db()
    c = conn.cursor()

    # Natijani tekshirish
    c.execute("SELECT * FROM test_results WHERE id=?", (result_id,))
    result = c.fetchone()
    if not result:
        flash("Natija topilmadi", "error")
        return redirect(url_for('student.student_dashboard'))

    user_id = session['user_id']
    if result['user_id'] != user_id:
        flash("Boshqa foydalanuvchi testi", "error")
        return redirect(url_for('student.student_dashboard'))

    # Testni olish
    c.execute("SELECT * FROM tests WHERE id=?", (result['test_id'],))
    test = c.fetchone()

    # Savollarni olish
    c.execute("SELECT * FROM questions WHERE test_id=?", (test['id'],))
    all_questions = list(c.fetchall())

    # Savollarni aralashtirish va limit 30
    if len(all_questions) > 30:
        questions = random.sample(all_questions, 30)
    else:
        questions = all_questions
    random.shuffle(questions)

    questions_with_answers = []
    for q in questions:
        c.execute("SELECT * FROM answers WHERE question_id=?", (q['id'],))
        answers = list(c.fetchall())
        random.shuffle(answers)
        questions_with_answers.append({'question': q, 'answers': answers})

    # Agar test hali boshlanmagan bo'lsa, start_time ni yozish
    if not result['start_time']:
        start_time = datetime.now()
        c.execute("UPDATE test_results SET start_time=? WHERE id=?", (start_time, result_id))
        conn.commit()
    else:
        start_time = datetime.fromisoformat(result['start_time'])

    # POST bo‘lsa javoblarni saqlash
    if request.method == 'POST':
        score = 0
        max_score = 0

        for q in questions_with_answers:
            q_id = q['question']['id']
            max_score += 1

            selected_id = request.form.get(f'question_{q_id}')
            if selected_id:
                selected_id = int(selected_id)
                c.execute("SELECT * FROM answers WHERE id=?", (selected_id,))
                ans = c.fetchone()
                is_correct = ans['is_correct'] if ans else 0
                if is_correct:
                    score += 1

                c.execute("""
                    INSERT INTO user_answers (result_id, question_id, answer_id)
                    VALUES (?, ?, ?)
                """, (result_id, q_id, selected_id))
            else:
                c.execute("""
                    INSERT INTO user_answers (result_id, question_id, answer_id)
                    VALUES (?, ?, NULL)
                """, (result_id, q_id))

        c.execute("""
            UPDATE test_results
            SET score=?, max_score=?, end_time=?, completed=1
            WHERE id=?
        """, (score, max_score, datetime.now(), result_id))
        conn.commit()
        flash(f"Test tugadi! Siz {score}/{max_score} ball to‘pladingiz.", "success")
        return redirect(url_for('student.student_dashboard'))

    # Qolgan vaqtni hisoblash
    now = datetime.now()
    elapsed_seconds = (now - start_time).total_seconds()
    remaining_seconds = max(test['duration'] * 60 - elapsed_seconds, 0)

    return render_template(
        'student/take_test.html',
        test=test,
        questions=questions_with_answers,
        remaining_seconds=int(remaining_seconds)
    )

@bp.route('/view_result/<int:test_id>')
def view_result(test_id):
    if 'user_id' not in session:
        flash("Avval tizimga kiring", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Eng oxirgi natija
    c.execute("""
        SELECT * FROM test_results
        WHERE user_id=? AND test_id=? AND completed=1
        ORDER BY id DESC
        LIMIT 1
    """, (user_id, test_id))
    result = c.fetchone()

    if not result:
        flash("Natija topilmadi", "error")
        return redirect(url_for('student.student_dashboard'))

    # Test
    c.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    test = c.fetchone()

    # Savollar + foydalanuvchi javoblari + to‘g‘ri javoblar
    c.execute("""
        SELECT 
            q.id as question_id,
            q.title as question_title,

            ua.answer_id as user_answer_id,

            a.title as user_answer_text,

            correct_a.id as correct_answer_id,
            correct_a.title as correct_answer_text

        FROM questions q

        LEFT JOIN user_answers ua 
            ON ua.question_id = q.id AND ua.result_id = ?

        LEFT JOIN answers a 
            ON a.id = ua.answer_id

        LEFT JOIN answers correct_a 
            ON correct_a.question_id = q.id AND correct_a.is_correct = 1

        WHERE q.test_id=?
    """, (result["id"], test_id))

    questions = c.fetchall()

    return render_template(
        "student/view_result.html",
        test=test,
        result=result,
        questions=questions
    )
    
    
@bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Avval tizimga kiring", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Foydalanuvchi ma'lumotlari
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    # Foydalanuvchi testlari va natijalari
    c.execute("""
        SELECT tr.id AS result_id, tr.test_id, t.title AS test_title,
            tr.score, tr.max_score, tr.completed, tr.start_time, tr.end_time
        FROM test_results tr
        JOIN tests t ON tr.test_id = t.id
        WHERE tr.user_id=?
        ORDER BY tr.end_time DESC
    """, (user_id,))
    test_results = c.fetchall()

    return render_template('student/profile.html', user=user, test_results=test_results)



@bp.route("/test_ranking/<int:test_id>")
def test_ranking(test_id):
    

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

    return render_template("student/test_ranking.html", test=test, rankings=rankings)
