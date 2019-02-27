""" File that seeds health_db database from Kaggle data in kaggle_data/ 
FROM CLARIFAI API - gets images
    train the model in synchronous or asynchronous mode. Synchronous will block until the
    model is trained, async will not.
    >> Set to asynchronous

    Methods are:
    - add_images_concepts (our bulk initial setup of local files to Clar)
    - load_bees_from_clar (getting images from Clar to our Postgres (?) database)
    - add_one_image (single image upload of user's local file, stored temp, to Clar)
    - load_one_image (add a single image to Postgres database)
    - more methods...
"""

# API Requests / Get
from clarifai.rest import ClarifaiApp


import json
import requests
from pprint import pprint

from sqlalchemy import func
import pandas as pd

from model import Bee, connect_to_db, db


clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56")
MODEL_ID = 'test'
cl_model = clarifai_app.models.get(MODEL_ID)

def add_images_concepts_to_clar(csv_filename):
    """
    Load images to Clarifai model, using custom tags from the csv file.
    """

    # df is a pandas DataFrame
    df = pd.read_csv(csv_filename, 
                    index_col=False, 
                    parse_dates={'datetime':[1, 2]}, # This will parse columns 1, 2 as date and call result 'datetime'
                    dtype={'health':'category', 
                            'datetime':'datetime64[ns]',
                            'csv_filename':'str',
                            'zip_code':'str',
                            } 
    )

    image_list = []

    # for i in range(len(df)):
    for i in range(120): # FOR NOW

        image_id = i # Integer assigned to each new Bee
        health_ = str(df.loc[i][5])
        datetime = df.loc[i][0]
        csv_filename = str(df.loc[i][1])
        zip_code = str(df.loc[i][3])

        # Edit health (a string) to make it better for queries (a binary value)
        health = 'y' if health_ == 'healthy' else 'n'

        # Edit fileanme to have the local path:
        local_filename = 'bee_imgs/' + csv_filename

        if (health == 'y'):
            img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                            # image_id=bee_id,
                            concepts=['health'],
                            not_concepts=None,
                            metadata={ 'image_id': image_id,
                                        # 'datetime': datetime, 
                                        'zip_code': zip_code,
                                        },
                            geo=None, # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                            allow_duplicate_url=True,
                            )
        else:
            img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                            # image_id=bee_id,
                            concepts=None,
                            not_concepts=['health'],
                            metadata={ 'image_id': image_id,
                                        # 'datetime': datetime, 
                                        'zip_code': zip_code,
                                        },
                            geo=None, # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                            allow_duplicate_url=True,
                            )

        image_list.append(img)

    clarifai_app.inputs.bulk_create_images(image_list)


def load_bees_from_clarifai_to_db():
    """ Load Image objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs 
    Convert Image objects to Bee objects, & add to our database.
    """

    all_images = list(clarifai_app.inputs.get_all())

    for i in range(len(all_images)):

        image = all_images[i] 
        
        url = image.url
        image_id = int(image.metadata['image_id'])
        zip_code = str(image.metadata['zip_code']) 
        health = None

        if (image.concepts): 
            health = 'y' 
        elif (image.not_concepts):
            health = 'n'

        # Create a bee
        a_bee = Bee(bee_id=image_id,
                    user_id=None, # All database bees will have no user_id
                    url=url,
                    health=health,
                    zip_code=zip_code,
                    )

        db.session.add(a_bee)

    # Commit all Bee objects to the database
    db.session.commit()


def predict_with_model(path):
    """ https://clarifai.com/developer/guide/train#predict-with-the-model
    Makes a prediction with the model.
    @model_version_id = integer, version this time around
   
    @path = local filename
    """

    # Set a model version id because I want to keep track of progress
    # model.model_version = model_version_id

    # print(model.model_version)

    response = cl_model.predict_by_filename(path)
    
    response_id = response['outputs'][0]['data']['concepts'][0]['id']
    
    response_confidence = response['outputs'][0]['data']['concepts'][0]['value']
    
    response_datetime = response['outputs'][0]['created_at']


    response_tuple = (response_id, response_confidence, response_datetime)
    print("t", response_tuple)
    return response_tuple



def add_new_image_to_clar(user_id, photo_url, photo_health):
    """ Get prediction tuple from a user's uploaded image (which has metadata)
    Create a new Bee object

    and add it to Clarifai """

    image_id = i # Need to get nteger assigned to each new Bee


    health_ = str(df.loc[i][5])
    datetime = df.loc[i][0]
    csv_filename = str(df.loc[i][1])
    zip_code = str(df.loc[i][3])

    # Edit health (a string) to make it better for queries (a binary value)
    health = 'y' if health_ == 'healthy' else 'n'

    # Edit fileanme to have the local path:
    local_filename = 'bee_imgs/' + csv_filename

    if (health == 'y'):
        img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                        # image_id=bee_id,
                        concepts=['health'],
                        not_concepts=['sick'],
                        metadata={ 'image_id': image_id,
                                    # 'datetime': datetime, 
                                    'zip_code': zip_code,
                                    },
                        geo=None, # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                        allow_duplicate_url=True,
                        )
    else:
        img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                        # image_id=bee_id,
                        concepts=['sick'],
                        not_concepts=['health'],
                        metadata={ 'image_id': image_id,
                                    # 'datetime': datetime, 
                                    'zip_code': zip_code,
                                    },
                        geo=None, # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                        allow_duplicate_url=True,
                        )



    clarifai_app.inputs.bulk_create_images(image_list)

    


def add_new_image_to_db():
    """ Get one image (hosted by clarafai) - which has a url (on Clar)
    Create a Bee object and add it to the database 
    """

    # Get the maximum bee_id in the database
    result = db.session.query(func.max(Bee.bee_id)).one()
    bee_id = int(result[0]) + 1


    # Create a new bee:
    # bee = Bee(bee_id=bee_id,
    #             user_id=user_id,
    #             url=image, # From user_file
    #             health=health,
    #             zip_code=zipcode,

    #             )

    # flash("Bee created successfully.")

    # db.session.add(bee)
    # db.session.commit()
    # flash("Bee added to database. Thank you!")



if __name__ == '__main__':

    # Flask database initialization
    from server import app
    connect_to_db(app)
    db.create_all()

    # Clear it from Clarifai. Be careful!!!!!!!!!
    # clarifai_app.inputs.delete_all()
    # print('Successfully deleted all.')

    # # Give images and concepts from file to Clarifai
    # seed_filename = "bee_data.csv" 
    # add_images_concepts(seed_filename)
    # print('Successfully added all.')

    # Add Bees to our database from Clarifai
    # load_bees_from_clarifai()

    # model.train(sync=False) # False goes faster

    predict_with_model( 
        path='uploads/download.jpeg')