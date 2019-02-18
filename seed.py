""" File that seeds health_db database from Kaggle data in kaggle_data/ """
# Outside tools
import pandas as pd

# Local scripts
from model import User, Photo, Bee, connect_to_db, db
from server import app


def load_bee_data(csv_filename):
    """ Load ratings from bee_data.csv into bees table """

    print("bees")

    # df is a pandas DataFrame
    df = pd.read_csv(csv_filename, # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
                    index_col=False, # from docs: tells reader to ignore headers
                    parse_dates={'datetime':[1, 2]}, # from docs: This will parse columns 1, 2 as date and call result 'datetime'
                    dtype={'subspecies':'category', 'health':'category'} # Data type for data, column respectively.
    )


    # Iterate and create Bee objects ex: https://www.datacamp.com/community/tutorials/pandas-tutorial-dataframe-python

    for i in range(len(df)):
    # for i in range(30): # FOR NOW

        bee_id = i # Integer

        # Parse a line
        health_ = str(df.loc[i][5])
        datetime = df.loc[i][0]
        filename = str(df.loc[i][1])
        location = str(df.loc[i][2])
        zip_code = str(df.loc[i][3])
        subspecies = str(df.loc[i][4])
        pollen_carrying = str(df.loc[i][6])
        caste = str(df.loc[i][7])


        # Edit health (a string) to make it better for queries (a binary value)
        health = 'y' if health_ == 'healthy' else 'n'
        

        # Constructor
        a_bee = Bee(bee_id=bee_id,
                    health=health,
                    datetime=datetime,
                    filename=filename,
                    location=location,
                    zip_code=zip_code,
                    subspecies=subspecies,
                    pollen_carrying=pollen_carrying,
                    caste=caste,
                    )

        print(a_bee)

        # Add the object to db.session
        db.session.add(a_bee)

        # provide some sense of progress
        if i % 100 == 0:
            print("Status: ", i)



    # Commit all bees to the database
    db.session.commit()


if __name__ == '__main__':
    connect_to_db(app)
    db.create_all()


    seed_filename = "bee_data.csv" 
    load_bee_data(seed_filename)
