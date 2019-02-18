""" File that seeds health_db database from Kaggle data in kaggle_data/ 
FROM CLARIFAI API - gets images

"""

# API Requests / Get
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage

import pandas as pd

from model import User, Photo, Bee, connect_to_db, db
from server import app

clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56")
# model = app.public_models.general_model
# response = model.predict_by_url('url!!')

def images_up_with_concepts(csv_filename):
    """
    Load images to Clarifai model, using custom tags from csv file.
    """
    print("csv file")

    # df is a pandas DataFrame
    df = pd.read_csv(csv_filename, # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
                    index_col=False, # from docs: tells reader to ignore headers
                    parse_dates={'datetime':[1, 2]}, # from docs: This will parse columns 1, 2 as date and call result 'datetime'
                    dtype={'subspecies':'category', 'health':'category'} # Data type for data, column respectively.
    )

    image_list = []

    # for i in range(len(df)):
    for i in range(30): # FOR NOW

        # bee_id = i # Integer

        health_ = str(df.loc[i][5])
        # datetime = df.loc[i][0]
        local_filename = str(df.loc[i][1])
        # location = str(df.loc[i][2])
        # zip_code = str(df.loc[i][3])
        # subspecies = str(df.loc[i][4])
        # pollen_carrying = str(df.loc[i][6])
        # caste = str(df.loc[i][7])


        # Edit health (a string) to make it better for queries (a binary value)
        health = 'y' if health_ == 'healthy' else 'n'
        

        if (health == 'y'):
            img = ClImage(local_filename,  concepts=['health'])
        else:
            img = ClImage(local_filename, not_concepts=['health'])

        image_list.append(img)

    clarifai_app.inputs.bulk_create_images(image_list)





def load_bees_from_clarifai():
    """ Load bee objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs
    
     """

    print("Getting bees")

    all_bees = list(clarifai_app.inputs.get_all())



    # Iterate and create Bee objects
    for i in range(len(all_bees)):
    # for i in range(30): # FOR NOW

        bee_id = i 
        bee = all_bees[i] # Gets object from list
        health = "y" # for now
        url = bee.url # Attribute

        new_bee = Bee(bee_id=bee_id,
                        url=url,
                        health=health,
                        )

        # What is the dir of bee object?
        # 'allow_dup_url', 'base64', 'concepts', 'crop', 'dict', 
        #'feedback_info', 'file_obj', 'filename', 'geo', 'input_id', 
        #'metadata', 'not_concepts', 'regions', 'score', 
        #'status', 'url'

        # print("Dict: ", dict(bee))
        print("Concepts: ", bee.concepts)

        db.session.add(new_bee)

        # provide some sense of progress
        if i % 100 == 0:
            print("Status: ", i)




    # Commit all bees to the database
    db.session.commit()


if __name__ == '__main__':
    connect_to_db(app)
    db.create_all()

    seed_filename = "bee_data.csv" 
    images_up_with_concepts(seed_filename)

    # load_bees_from_clarifai()