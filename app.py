from flask import Flask, redirect, session, url_for
from routes.auth import bp as auth
from routes.admin import bp as admin
from routes.student import bp as student
from datetime import timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.permanent_session_lifetime = timedelta(seconds=72000)

# Blueprintlarni ulash
app.register_blueprint(auth)
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(student, url_prefix='/student')


@app.route("/")
def compas():
    if session.get("user_id"):
        if session.get("role") == "admin":
            return redirect("/admin")
        else:
            return redirect("/student")
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5300, debug=True)