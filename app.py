from flask import Flask, render_template, flash, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
# from typing import Optional, List
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
# from sqlalchemy.orm import Mapped
# from sqlalchemy.orm import mapped_column
# from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship


app = Flask(__name__)

UPLOAD_FOLDER = './uploaded'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True,
                         nullable=False)
    password = db.Column(db.String(250),
                         nullable=False)
    files = db.relationship('Upload', backref='users')
    # children: Mapped[List["BlobMixin"]] = relationship(back_populates="users")
    

# class BlobMixin(object):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     mimetype = db.Column(db.Unicode(length=255), nullable=False)
#     filename = db.Column(db.Unicode(length=255), nullable=False)
#     blob = db.Column(db.LargeBinary(), nullable=False)
#     size = db.Column(db.Integer, nullable=False)
#     parent_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"))
#     parent: Mapped["Users"] = relationship(back_populates="blobmixin")

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    data = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# Initialize app with extension
db.init_app(app)
# Create database within app context
 
with app.app_context():
    db.create_all()


@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File saved!')
            upload = Upload(filename=file.filename, data=file.read(), user_id=current_user.get_id())
            db.session.add(upload)
            db.session.commit()
        
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
  # If the user made a POST request, create a new user
    if request.method == "POST":
        user = Users(username=request.form.get("username"),
                     password=request.form.get("password"))
        # Add the user to the database
        db.session.add(user)
        # Commit the changes made
        db.session.commit()
        # Once user account created, redirect them
        # to login route (created later on)
        return redirect(url_for("login"))
    # Renders sign_up template if user made a GET request
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	# If a post request was made, find the user by
	# filtering for the username
	if request.method == "POST":
		user = Users.query.filter_by(
			username=request.form.get("username")).first()
		# Check if the password entered is the
		# same as the user's password
		if user.password == request.form.get("password"):
			# Use the login_user method to log in the user
			login_user(user)
			return redirect(url_for("index"))
		# Redirect the user back to the home
		# (we'll create the home route in a moment)
	return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/uploads")
def uploaded_files():
    users = Users.query.all()
    return render_template("uploads.html", users=users)



if __name__ == "__main__":
    app.run(debug=True)