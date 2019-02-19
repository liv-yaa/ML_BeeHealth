""" File that seeds health_db database from Kaggle data in kaggle_data/ 
FROM CLARIFAI API - gets images


What is the dir of bee object?
'allow_dup_url', 'base64', 'concepts', 'crop', 'dict', 
'feedback_info', 'file_obj', 'filename', 'geo', 'input_id', 
'metadata', 'not_concepts', 'regions', 'score', 
'status', 'url'

"""

# API Requests / Get
from clarifai.rest import ClarifaiApp
# from clarifai.rest.client import create_image_from_filename # https://media.readthedocs.org/pdf/clarifai-python/latest/clarifai-python.pdf (pg11)

from gcloud import storage

import pandas as pd

from model import User, Photo, Bee, connect_to_db, db
from server import app

clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56")
# model = app.public_models.general_model
# response = model.predict_by_url('url!!')

# https://github.com/googleapis/google-cloud-python/issues/1295
# client = storage.Client() # Environ set up
# bucket = client.bucket('mlbees')
# blob = bucket.blob('my-blob')
# url_lifetime = 3600  # Seconds in an hour
# serving_url = blob.generate_signed_url(url_lifetime)

# print("serving_url ", serving_url)

def add_images_concepts(csv_filename):
    """
    Load images to Clarifai model, using custom tags from the csv file.
    """
    print("csv file ", csv_filename)

    # df is a pandas DataFrame
    df = pd.read_csv(csv_filename, # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
                    index_col=False, # from docs: tells reader to ignore headers
                    parse_dates={'datetime':[1, 2]}, # from docs: This will parse columns 1, 2 as date and call result 'datetime'
                    dtype={'health':'category', 
                            'datetime':'datetime64[ns]',
                            'csv_filename':'str',
                            'zip_code':'str',
                            } # Data type for data, column respectively.
    )

    image_list = []

    # for i in range(len(df)):
    for i in range(100): # FOR NOW

        bee_id = i # Integer assigned to each new Bee
        health_ = str(df.loc[i][5])
        datetime = df.loc[i][0]
        csv_filename = str(df.loc[i][1])
        zip_code = str(df.loc[i][3])

        # Edit health (a string) to make it better for queries (a binary value)
        health = 'y' if health_ == 'healthy' else 'n'

        # Edit fileanme to have the local path:
        local_filename = 'bee_imgs/' + csv_filename
        
        # print(bee_id,
        #     health,
        #     datetime,
        #     csv_filename,
        #     zip_code,
        #     local_filename)

        # Constructor of ClImage: ClImage(url='', 
                    # filename='/tmp/user/dog.jpg', 
                    # concepts=[''], 
                    # not-concepts=[''],
                    # metadata={'id':123, '': ...})

        # local_filename = "temp"

        if (health == 'y'):
            img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                            # image_id=bee_id,
                            concepts=['health'],
                            not_concepts=None,
                            # metadata={'datetime': datetime, 'zip_code': zip_code},
                            # geo=None # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                            )
        else:
            img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                            # image_id=bee_id,
                            concepts=None,
                            not_concepts=['health'],
                            # metadata={'datetime': datetime, 'zip_code': zip_code},
                            # geo=None # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                            )



        print("URL: ", img.url)
        # print("Filename: ", img.filename)
        print("img concepts: ", img.concepts)
        # print("img not concepts: ", img.not_concepts)
        # print("metadata: ", img.metadata)
        # print(img)
        print()
        
        image_list.append(img)

    clarifai_app.inputs.bulk_create_images(image_list)

    # We are trying to get images by url and upload them to our file!
    # Let's grab them from Google:
    # https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.images#Image_get_serving_url






def load_bees_from_clarifai():
    """ Load bee objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs 
    """

    all_bees = list(clarifai_app.inputs.get_all())

    for i in range(len(all_bees)):

         
        bee = all_bees[i] 
        bee_id = bee.bee_id
        health = bee.health
        url = bee.url 

        a_bee = Bee(bee_id=bee_id,
                        url=url,
                        health=health,
                        )

        db.session.add(a_bee)

    # Commit all Bee objects to the database
    db.session.commit()


if __name__ == '__main__':

    # Flask database initialization
    connect_to_db(app)
    db.create_all()

    # Get Bees from file
    seed_filename = "bee_data.csv" 
    add_images_concepts(seed_filename)

    # Add Bees to database
    # load_bees_from_clarifai()