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
from bees_seed import process_upload, cl_model, give_model_feedback, predict_with_model

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

    healthy_bees5 = random.sample(healthy, 5)
    healthy_bees7 = random.sample(healthy, 7)
    unhealthy_bees6 = random.sample(unhealthy, 6)
    unhealthy_bees4 = random.sample(unhealthy, 4)


    return render_template("index.html", 
                            user_id=user_id,
                            healthy_bees5=healthy_bees5,
                            healthy_bees7=healthy_bees7,

                            unhealthy_bees6=unhealthy_bees6,
                            unhealthy_bees4=unhealthy_bees4,
                            
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

        prediction_tuple = process_upload(user_id=user_id, 
                                    health=health, 
                                    local_filename=local_filename,
                                    zipcode=int(zipcode),
                                    ) # returns prediction_tuple

        performance = str(check_prediction(health, prediction_tuple))
        print("health", health) # Prediction (string)
        print("performance", performance) # Boolean

        if performance:
            try:
                print("Prediction was accurate ", prediction_tuple[2])
                print("Adding image to model as a positive example. ")
                # add image as a positive example  
            except:
                print("Error with performance")

        else:
            print("Prediction was not accurate. ")
            print("Adding image to model as a NEGATIVE example. ")

                # Add image 

        # # This is going to become true once image is added.
        # # needed for Jinja conditional...
        image_added = "None"     
        add_image_attempt="none"

        prediction_tuple="slkjdf"
        performance = "ljhlg"


        return render_template("upload_success.html", 
                                        prediction_tuple=prediction_tuple,
                                        performance=performance,
                                        image_added=image_added,
                                        add_image_attempt=add_image_attempt,
                                       
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


# def check_prediction(health_string, prediction_tuple):
#     """ Checks whether prediction tuple matches input of health specified by user """
#     response_string = prediction_tuple[0]
#     response_confidence = prediction_tuple[1]

#     print("response_string", response_string)
#     print(
#         "response_confidence", response_confidence
#         )

#     return response_string == health_string




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



