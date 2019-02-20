""" File that seeds health_db database from Kaggle data in kaggle_data/ """
from sqlalchemy import func
import pandas as pd

# Local scripts
from model import User, connect_to_db, db
from server import app


def load_user_data(csv_filename):
    """ Load ratings from bee_data.csv into bees table 
    Note, here I have created "fake data - users_demo.csv" 
    This is how we save the User database for other people to load for now.
    """

    df = pd.read_csv(csv_filename,
                    index_col=False, # Tells reader to ignore headers                    
    )

    # Iterate and create User objects
    for i in range(len(df)):

        user_id = i # Integer

        # Parse a line
        email = str(df.loc[i][0])
        password = str(df.loc[i][1])

        # Constructor
        a_user = User(user_id=user_id,
                    email=email,
                    password=password,
                    )

        # Add the object to db.session
        db.session.add(a_user)

    # Commit all bees to the database
    db.session.commit()


def set_val_user_id():
    """ WHAT IS THIS FUNCTION FOR??? """

    # Get the maximum user_id in the database:
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


if __name__ == '__main__':
    connect_to_db(app)
    db.create_all()

    filename = "users_demo.csv"
    load_user_data(filename)

    # set_val_user_id()
