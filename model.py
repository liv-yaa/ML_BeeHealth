""" model.py
    Models and database functions for BeeMachine project.
"""

# Connect to the PostgreSQL database through the Flask-SQLAlchemy library
# Includes the 'session' object
from flask_sqlalchemy import SQLAlchemy

# Create a database object
db = SQLAlchemy()


##############################################################################
# Model definitions
class User(db.Model):
    """ A user of the app.
    Contains login information for the session (email, password).
    """

    __tablename__= 'users'

    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(20))


    def __repr__(self):
        """ Print format for User object """
        return f'<User id: {self.user_id}; email: {self.email}>'


    def get_user_bees(self):
        """ Retrieve all Bees that are tagged with this User's user_id 
        """
        
        # Return a list - need to test!!! 
        query_list = db.session.query(Bee).filter_by(user_id=self.user_id).all()
        return query_list


class Bee(db.Model):
    """ All Bee objects, both from Kaggle Dataset and from
        user generated bee Photos

        Every Bee does not have a user.
    """

    __tablename__= 'bees'

    bee_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True,
                        )

    user_id = db.Column(db.Integer, 
                        db.ForeignKey('users.user_id'),
                        nullable=True,
                        )

    url = db.Column(db.String(250), nullable=True) 
    health = db.Column(db.String(1), nullable=True) # 'y' if healthy, or 'n' if not.
    zip_code = db.Column(db.String(10), nullable=True)
    image_id = db.Column(db.String(10), nullable=True) # Just added this Tuesday.
    # We need it to search through for the latest image that's been added, so user can see
    # They have helped build the database


    user = db.relationship("User",
                           backref=db.backref("bees"))

    def __repr__(self):
        """ Print format for Bee object """
        return f'''<BEE OBJECT
                    Bee id: {self.bee_id}
                    Uploaded by: {self.user_id}
                    url: {self.url}
                    health: {self.health}
                    zip_code: {self.zip_code}
                    
                    >'''



##############################################################################
# Helper functions

# def connect_to_db(app, db_uri="postgresql:///bee_db"):
#     """ Connect database to our Flask app. """

#     # Configuration of a PostgreSQL database
#     app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['SQLALCHEMY_ECHO'] = True
#     db.app = app
#     db.init_app(app)

##############################################################################
# From testing-approaches-demo
def example_data():
    """Create some sample data."""

    # In case this is run more than once, empty out existing data
    Bee.query.delete()
    User.query.delete()

    # Add sample users and bees
    user1 = User(user_id="1", email="q@q.q", password="q")
    user2 = User(user_id="2", email="r@r.r", password="r")
    user3 = User(user_id="3", email="qr@qr.qr", password="qr")

    bee1 = Bee(user_id="1", url="", health="healthy", zip_code="12314")
    bee2 = Bee(user_id="2", url="", health="unhealthy", zip_code="41334")
    bee3 = Bee(user_id="3", url="", health="other", zip_code="52362")

   
    db.session.add_all([bee1, bee2, bee3, user1, user2, user3])
    db.session.commit()


def connect_to_db(app, db_uri="sqlite:///emp.db"):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == '__main__':

    from server import app
    connect_to_db(app)
    print("Connected to Database.")