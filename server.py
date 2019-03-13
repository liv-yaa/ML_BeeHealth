""" server.py
    Flask routes for BeeMachine project.
"""
import random, os, pdb
from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension 

from werkzeug.utils import secure_filename

from sqlalchemy import func

from model import Bee, User, connect_to_db, db
from bees_seed import process_upload, cl_model, give_model_feedback, predict_with_model, check_prediction

from os.path import join, dirname, realpath


# Create a Flask app
app = Flask(__name__)

# Added this config statement based on this demo for Amazon S3 integration: http://zabana.me/notes/upload-files-amazon-s3-flask.html
app.config.from_object("config")

# An upload folder for temporarily storing user uploads
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Moved to config:
# A secret key is required for Flask sessions and debug toolbar
# app.secret_key = 'XO'
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Ask Jinja to give us an error if there is an undefined variable in scope
app.jinja_env.undefined = StrictUndefined

@app.route('/')
def landing():
    """ Home page (the database viewer, image uploader) 
    Obviously, they need to be images next!

    If a user is logged in, let them upload a photo.

    """
    # Get current user
    user_id = session.get("user_id")

    # Get list of bees


    return render_template("landing.html", user_id=user_id)                     
                            


@app.route('/index')
def index():
    """ Home page (the database viewer, image uploader) 
    Obviously, they need to be images next!

    If a user is logged in, let them upload a photo.

    """
    # Get current user
    user_id = session.get("user_id")

    # Get list of bees

    healthy = Bee.query.filter_by(health='y').all()
    unhealthy = Bee.query.filter_by(health='n').all()

    # For loop? idk

    healthy_bees = random.sample(healthy, 16)

    unhealthy_bees = random.sample(unhealthy, 16)



    return render_template("index.html", 
                            user_id=user_id,
                            healthy_bees=healthy_bees,
                            unhealthy_bees=unhealthy_bees,

                            # Should i create allbees? 
                            
                            )



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
    # return redirect(f'/users/{a_user.user_id}')

    return redirect('/index')


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
    # return redirect(f"/users/{user.user_id}") 
    return redirect('/index') 


@app.route('/logout')
def logout():
    """Log out. - Does not work yet since session is not yet up. """

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/index")


@app.route('/users')
def get_users():
    """ Get all users - temporary for now - should be viewable by Admin only. """

    users = User.query.all()
    return render_template("all_users.html", 
                    users=users)


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


@app.route("/upload-success", methods=['POST'])
def upload_file():
    """       
        Show a form for uploading a photo.

        In this method, we (temporarily?) store the image in a local folder named "uploads"

        After this method,
        - Image needs to be evaluated
        - We need to host the image on Clarafai.
    """

    # Get other data
    user_id = session.get("user_id")
    health = request.form["health"] # Change this to a button!!!! "healthy" else "n" gives us 'y' or 'n' in clarafai.
    zipcode = request.form["zipcode"]

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files["file"]

    # Handle if user did not select file:
    if file.filename == '':
        flash ('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Build the relative path:
        folder = app.config['UPLOAD_FOLDER']
        local_filename = folder + "/" + filename

        # Use method to our model's prediction
        
        # Also adds the new Bee to our database and to Clar app.
        # get prediction_tuple which is (response_id, response_name,
        # response_confidence, response_datetime)
    # 

        prediction_output = process_upload(user_id=user_id, 
                                    health=health, 
                                    local_filename=local_filename,
                                    zipcode=int(zipcode),
                                    ) # returns (bee_confidence, health_confidence, prediction_success)


        message = ""
        bee_confidence = False
        health_confidence = False
        prediction_success = False
        try:
            bee_confidence = prediction_output[0]
            health_confidence = prediction_output[1]
            prediction_success = prediction_output[2]

        except:
            print("bad array")



        if bee_confidence >= 0.5:


            if health_confidence >= 0.5:
                message += "Bee was predicted to be a healthy bee"

            elif health_confidence < 0.5:
                message += "Bee was predicted to be an unhealthy bee"



        else:
            message += "error"

            if health_confidence >= 0.5:
                message += ("Bee did not pass prediction for is_bee",
                    "yet it was predicted to be healthy")

            elif health_confidence > 0.5:
                message += ("Bee did not pass prediction for is_bee",
                    "and it was predicted to be healthy")



        return render_template("upload_success.html", 
                                        prediction_success=prediction_success,
                                        bee_confidence=bee_confidence,
                                        health_confidence=health_confidence,

                                        message=message,
                                        
                                       
                                        )

    else:
        flash('Error')
        return redirect(request.url)

    
@app.route('/charts')
def ml_charts():
    """ Exciting page for demo of the machine learning model
    """

    return render_template("charts.html")


@app.route('/links')
def links():
    """ Exciting page for links and resources about honeybees
    """

    return render_template("links.html")


## Helper functions ##
def allowed_file(filename):
    """ Determines whether filename is legal """
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

    # print(check_prediction("unhealth", predict_with_model( 
    #     path='uploads/download.jpeg')))
    # print(check_prediction("health", predict_with_model( 
    #     path='uploads/download.jpeg')))
    # print(check_prediction("unhealth", predict_with_model( 
    #     path='uploads/038_293.png')))
    # print(check_prediction("health", predict_with_model( 
    #     path='uploads/038_293.png')))




    app.run(host="0.0.0.0", debug=True)



