""" server.py
    Flask routes for BeeMachine project.
"""
import random, os
from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from werkzeug.utils import secure_filename

from sqlalchemy import func

from model import Bee, User, connect_to_db, db


# Create a Flask app
app = Flask(__name__)

# Added this config statement based on this demo for Amazon S3 integration: http://zabana.me/notes/upload-files-amazon-s3-flask.html
app.config.from_object("config")

# An upload folder for temporarily storing user uploads
UPLOAD_FOLDER = os.path.basename('uploads')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Moved to config:
# A secret key is required for Flask sessions and debug toolbar
# app.secret_key = 'XO'
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Ask Jinja to give us an error if there is an undefined variable in scope
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """ Home page (the database viewer, image uploader) 
    Obviously, they need to be images next!

    If a user is logged in, let them upload a photo.

    """

    # Get list of bees

    healthy = Bee.query.filter_by(health='y').all()
    unhealthy = Bee.query.filter_by(health='n').all()

    healthy_bees = random.sample(healthy, 10)
    unhealthy_bees = random.sample(unhealthy, 10)


    return render_template("index.html", 
                            healthy_bees=healthy_bees,
                            unhealthy_bees=unhealthy_bees)



@app.route('/register', methods=['GET'])
def register_form():
    """ Form to show when user signs up """
    return render_template("registration_form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """ Processing the registration when user signs up """

    email = request.form["email"]
    password = request.form["password"]

    # Get most recent user_id:
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0]) + 1


    # Create a new user and add them to the session.
    a_user = User(user_id=max_id, email=email, password=password)
    db.session.add(a_user)
    db.session.commit()
    flash(f"User {email} added.")

    # Log the user in automatically:
    session["user_id"] = a_user.user_id
    flash("Logged in")

    # Redirect to the users page
    return redirect(f'/users/{a_user.user_id}')


@app.route('/login', methods=['GET'])
def login_form():
    """ Show the login form, where we will get input values email & password """

    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_process():
    """ Process the login (previous route ^). 
    Works upon submission of the Submit button.
    """

    # Get variables from the form (login.html):
    email = request.form["email"]
    password = request.form["password"]

    # See if there are any users yet in our db
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("That user information does not exist.")
        return redirect("/login")

    if user.password != password:
        flash("Incorrect password")
        return redirect("/login")

    # If we succesfully find a match, add the user_id to the session
    session["user_id"] = user.user_id

    flash("Logged in")
    return redirect(f"/users/{user.user_id}") 


@app.route('/logout')
def logout():
    """Log out. - Does not work yet since session is not yet up. """

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/")


@app.route('/users')
def get_users():
    """ Get all users - temporary for now - should be viewable by Admin only. """

    users = User.query.all()
    return render_template("all_users.html", users=users)


@app.route("/users/<int:user_id>", methods=['GET'])
def user_detail(user_id):
    """Show info about user.
        Show all Bees created by that user, if they exist.

    """

    user = User.query.get(user_id)

    user_bees = user.get_user_bees()

    return render_template("user.html", 
                            user=user,
                            user_bees=user_bees,
                            )


@app.route("/users/<int:user_id>", methods=['GET', 'POST'])
def upload_file(user_id):
    """       

        Show a form for uploading a photo.
        Createa Bee from the data submitted by that user.

        NOT DONE YET: We need to host the image on Clarafai.

    """

    if request.method == 'POST':

        # Get other data
        health = request.form["health"]
        zipcode = request.form["zipcode"]

        user_id = session.get("user_id")
        if not user_id:
            raise Exception("No user logged in.")

        # Handle file specified by user (on their local machine)
        # Check if the post request has the file part:
        if 'file' not in request.files:
            flash('no file part')
            return redirect(request.url)

        file = request.files["user-file"]

        # Handle if user does not select file:
        if file.filename == '':
            flash ('No selected file')
            return redirect(request.url) 

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))



            return redirect(redirect("/upload-success", 
                                        
                                        health=health,
                                        zipcode=zipcode,
                                        user_id=user_id,
                                        filename=filename,
                                        ))
    

    # filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    # image_path.save(filename)

    print()



    # image = "https://www.istockphoto.com/no/photos/honey-bee?sort=mostpopular&mediatype=photography&phrase=honey%20bee"






@app.route('/upload-success', methods=['POST'])
def upload_success():
    """ I want to make this AJAX! In place. For now, this will be a form.
    """

    return render_template("upload_success.html")


# @app.route('/upload-success', methods=['POST'])
# def upload():
#     """ I want to make this AJAX! In place. For now, this will be a form.
#     """

#     # Get image and health from the form upload_success.html
#     image = request.form["image"]
#     health = request.form["health"]

#     # # See if there are any users yet in our db
#     # user = User.query.filter_by(email=email).first()

#     # if not user:
#     #     flash("That user information does not exist.")
#     #     return redirect("/login")

#     # if user.password != password:
#     #     flash("Incorrect password")
#     #     return redirect("/login")

#     # # If we succesfully find a match, add the user_id to the session
#     # session["user_id"] = user.user_id

#     # flash("Logged in")

#     return redirect("/bee-add-success")


## Helper functions ##
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



if __name__ == '__main__':

    # We want the DebugToolbarExtension to be invokable
    app.debug = True
    # app.jinja_env.auto_reload = app.debug

    # Use method written in model.py to connect our SQLAlchemy database to our Flask app
    connect_to_db(app)

    # Use the flask DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
