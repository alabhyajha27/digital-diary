from flask import Flask,render_template, redirect, url_for,request
from flask_login import login_user, logout_user, login_required,LoginManager,UserMixin,current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app=Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///database.db"
app.config["SECRET_KEY"] = "supersecretkey"
db=SQLAlchemy(app)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        existing_user=User.query.filter_by(username=username).first()
        if existing_user:
            return redirect(url_for("register",error="username already exists"))
        hashed_pass=generate_password_hash(password)
        new_user=User(username=username,password=hashed_pass)
        db.session.add(new_user)
        db.session.commit()
        return render_template("login.html")
    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')

        user=User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("login",error="username or password incorrect"))
    return render_template("login.html")

@app.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    if request.method=="POST":
        title=request.form.get("title")
        content=request.form.get("content")
        new_entry=DiaryEntry(
            title=title,
            content=content,
            user_id=current_user.id
        )
        db.session.add(new_entry)
        db.session.commit() 
        return redirect(url_for("dashboard"))
    entries=DiaryEntry.query.filter_by(user_id=current_user.id).order_by(DiaryEntry.date_created.desc()).all()
    return render_template("dashboard.html", entries=entries)

@app.route("/delete/<int:entry_id>")
@login_required
def delete_entry(entry_id):

    entry = DiaryEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        return "Unauthorized"

    db.session.delete(entry)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/update/<int:entry_id>", methods=["GET", "POST"])
@login_required
def update_entry(entry_id):

    entry = DiaryEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        return "Unauthorized"

    if request.method == "POST":
        entry.title = request.form.get("title")
        entry.content = request.form.get("content")

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("update.html", entry=entry)

@app.route("/logout",methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
def index():
    return render_template("register.html")

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)