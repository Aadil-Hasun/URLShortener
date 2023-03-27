from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from sqlalchemy.orm import backref
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length
from short_url import long_to_short
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
path = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SECRET_KEY'] = 'This_is_a_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class SigninForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=9)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=24)])


class SignupForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=9)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid Email')])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=24)])


class UrlForm(FlaskForm):
    long_url = StringField('Paste a Long URL in the box to convert: ', validators=[InputRequired()])


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    email = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class Url(db.Model):
    __tablename__ = 'url'
    short_url = db.Column(db.String(), primary_key=True)
    long_url = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    users = db.relationship("Users", backref=backref("users", uselist=False))

    def __init__(self, short_url, long_url, user_id):
        self.short_url = short_url
        self.long_url = long_url
        self.user_id = user_id


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = Users.query.filter_by(name=form.username.data).first()
            if user:
                return render_template("signup.html", form=form, error="This username already exists…")
            else:
                new_user = Users(name=form.username.data, email=form.email.data, password=form.password.data)
                db.session.add(new_user)
                db.session.commit()
                return render_template("login.html", form=SigninForm())
        else:
            return render_template("signup.html", form=form, error="Please, try again..")
    return render_template("signup.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = SigninForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(name=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('shorten_url'))
        return render_template("login.html", form=form, error="Username or Password entered is invalid")
    return render_template("login.html", form=form)


@app.route('/shorten-url', methods=['GET', 'POST'])
@login_required
def shorten_url():
    form = UrlForm()
    if request.method == 'POST':
        shortened_url = ''
        if form.validate_on_submit():
            short_id = long_to_short()
            user = Users.query.filter_by(id=current_user.id).first()
            new_url = Url(short_url=short_id, long_url=form.long_url.data, user_id=user.id)
            print(short_id)
            db.session.add(new_url)
            db.session.commit()
            shortened_url = 'http://localhost:5001/' + short_id
        return render_template('shorten_url.html', form=form, name=current_user.name, url_short=shortened_url)
    return render_template('shorten_url.html', form=form, name=current_user.name)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/<variable>')
def get_org_url(variable):
    url = Url.query.filter_by(short_url=variable).first()
    if url:
        return redirect(url.long_url)
    else:
        return redirect(url_for('index'))


@app.route('/history')
@login_required
def get_history():
    form = UrlForm()
    url_data = Url.query.filter_by(user_id=current_user.id).all()
    return render_template('shorten_url.html', form=form, data=url_data, history_name=current_user.name)


if __name__ == '__main__':
    app.run(host="localhost", port=5001, debug=True)
