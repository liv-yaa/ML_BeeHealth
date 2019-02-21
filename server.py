""" server.py
    Flask routes for BeeMachine project.
"""
import random
from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from sqlalchemy import func

from model import Bee, User, connect_to_db, db


# Create a Flask app
app = Flask(__name__)

# Added this config statement based on this demo for Amazon S3 integration: http://zabana.me/notes/upload-files-amazon-s3-flask.html
app.config.from_object("config")

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

# There are two '/register' routes: One will render template and get info from 
# login form, the other processes the information and adds it to the session.

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
    """ Get all users - temporary for now """

    users = User.query.all()
    return render_template("all_users.html", users=users)


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    """Show info about user.
        Show all Bees created by that user, if they exist.
        

        NOT DONE YET: Show a form for uploading a photo.
    """

    user = User.query.get(user_id)

    user_bees = user.get_user_bees()

    return render_template("user.html", 
                            user=user,
                            user_bees=user_bees,
                            )



# @app.route('/upload-success', methods=['GET'])
# def upload():
#     """ I want to make this AJAX! In place. For now, this will be a form.
#     """

#     return render_template("upload_success.html")


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



# @app.route('/bee-add-success')
# def upload():
#     """ I want to make this AJAX! In place. For now, this will be a form.
#     """

#     return render_template("bee_add_success.html")




if __name__ == '__main__':

    # We want the DebugToolbarExtension to be invokable
    app.debug = True
    # app.jinja_env.auto_reload = app.debug

    # Use method written in model.py to connect our SQLAlchemy database to our Flask app
    connect_to_db(app)

    # Use the flask DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
