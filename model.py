""" model.py
    Models and database functions for BeeMachine project.
"""

# Connect to the PostgreSQL database through the Flask-SQLAlchemy library
# Includes the 'session' object
from flask_sqlalchemy import SQLAlchemy
# Create a database object
db = SQLAlchemy()




# Model Class Definitions

class User(db.Model):
    """ A user of the app.
    Contains login information for the session (email, password).
    """

    __tablename__= 'users'

    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        """ Print format for User object """
        return f'<User id: {self.user_id}; email: {self.email}>'


class Photo(db.Model):
    """ A photo of a bee, Uploaded by a user.

    """

    __tablename__= 'photos'

    photo_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True,
                        )


    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'))
    bee_id = db.Column(db.Integer,
                        db.ForeignKey('bees.bee_id'))


    user = db.relationship("User", backref=db.backref("photos", order_by=photo_id))
    bee = db.relationship("Bee", backref=db.backref("photos", order_by=photo_id))


    def __repr__(self):
        """ Print format for Photo object """
        return f'<Photo id: {self.photo_id}; {self.url}>'


class Bee(db.Model):
    """ All Bee objects, both from Kaggle Dataset and from
        user generated bee Photos

        Every Bee does not have a user, but does it have a Photo?
    """

    __tablename__= 'bees'

    bee_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True,
                        )

    url = db.Column(db.String(150)) # Keep
    health = db.Column(db.String(1)) # 'y' if healthy, or 'n' if not.

   

    def __repr__(self):
        """ Print format for Bee object """
        return f'''<BEE OBJECT
                    Bee id: {self.bee_id}
                    url: {self.url}
                    health: {self.health}
                    >'''



##############################################################################
# Helper functions

def connect_to_db(app):
    """ Connect database to our Flask app. """

    # Configuration of a PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///bee_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == '__main__':

    from server import app
    connect_to_db(app)
    print("Connected to Database.")
