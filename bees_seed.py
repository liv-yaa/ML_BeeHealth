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
from clarifai.rest import ClarifaiApp #  Clarifai Application Object
                                        #   This is the entry point of the Clarifai Client API.
                                        #   With authentication to an application, you can access
                                        #   all the models, concepts, and inputs in this application through
                                        #   the attributes of this class.
                                        # |  To access the models: use ``app.models``
                                        # |  To access the inputs: use ``app.inputs``
                                        # |  To access the concepts: use ``app.concepts``


import json
import requests
import glob
from pprint import pprint

from sqlalchemy import func
import pandas as pd

from model import Bee, connect_to_db, db


clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56") # move this
MODEL_ID = 'Detection of Health in Bees with Images'
cl_model = clarifai_app.models.get(MODEL_ID)
seed_filename = "bee_data.csv" 


def add_images_concepts_to_clar(csv_filename):
    """
    Load images to Clarifai model, using custom tags from the csv file.
    """
    # Create a list to store all images we're passing to Clarafai app
    image_list = []

    # Read csv file, df is a pandas DataFrame
    df = pd.read_csv(csv_filename, 
                    index_col=False, 
                    parse_dates={'datetime':[1, 2]}, # This will parse columns 1, 2 as date and call result 'datetime'
                    dtype={'health':'category', 
                            'datetime':'datetime64[ns]',
                            'csv_filename':'str',
                            'zip_code':'str',
                            } 
    )

    # Get the maximum bee_id in the database
    result = db.session.query(func.max(Bee.bee_id)).one()
    nonbee_id = int(result[0]) + 1

    print("nonbee_id", nonbee_id)

    # for i in range(len(df)):
    for i in range(40): # FOR NOW

        image_id = str(nonbee_id + i)
        health_ = str(df.loc[i][5])
        datetime = str(df.loc[i][0])
        csv_filename = str(df.loc[i][1])
        zip_code = str(df.loc[i][3])

        # Edit health (a string) to make it a binary value (better for this purpose)
        health = 'y' if health_ == 'healthy' else 'n'

        # Edit fileanme to have the local path:
        local_filename = 'images/bees/' + csv_filename

        # print(image_id, health, datetime, csv_filename, zip_code, local_filename)

        if (health == 'y'):
            
            concepts=['health', 'is_bee'], # a list of concept names this image is associated with
            not_concepts=None,  # a list of concept names this image is not associated with

        else:
            concepts = ['is_bee']
            not_concepts = ['health']
           
        print("Before", concepts, " are concepts and not concepts are ", not_concepts)
        print("image_id", image_id)
        img = clarifai_app.inputs.create_image_from_filename(filename=local_filename, 
                        image_id=image_id,
                        concepts=concepts,
                        not_concepts=not_concepts,
                        metadata={ 'image_id': image_id,
                                    'datetime': datetime, 
                                    'zip_code': zip_code,
                                    },
                        # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                        allow_duplicate_url=True,
                        )

        print("After", img.concepts, " are concepts and not concepts are ", img.not_concepts)

        image_list.append(img)

    print("Image list" , image_list)

    # Add nonbees: This doesn't work...just manually did it for now :/
    # SO THIS PART ABOVE WORKS the part now is figuring out how to get nonbees.
    # print("ADDING NONBEES")
    
    # nonbees = glob.glob('images/not_bees/*png')

    # print("nonbees", nonbees)

    # Get the maximum bee_id in the database
    # result = db.session.query(func.max(Bee.bee_id)).one()
    # nonbee_id = int(result[0]) + 1


    # # for img_name in nonbees:
    # for i in range(200):

    #     img_name = 'images/not_bees/000' + str(i) + '.png'
    #     nonbee_id = str(nonbee_id + i)

    #     print("Before", img_name, nonbee_id)


    #     img = clarifai_app.inputs.create_image_from_filename(filename=img_name, 
    #                         image_id=image_id,
    #                         concepts=None,
    #                         not_concepts=['is_bee'], 
    #                         metadata=None,
                            
    #                         allow_duplicate_url=True,
    #                         )

    #     print("After creating img", str(img.filename)) # For the life of me can't figure out
    #     # Why can I not see this filename?
    #     # However, it looks like it's working to add the files to the model!

    #     print(img.concepts, " are concepts and not concepts are ", img.not_concepts)

    #     image_list.append(img)

    # print("Image list added", image_list)


    clarifai_app.inputs.bulk_create_images(image_list)



def load_bees_from_clarifai_to_db():
    """ Load Image objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs 
    Convert Image objects to Bee objects, & add to our database.
    """

    all_bees = list(clarifai_app.inputs.get_all())


    print(all_bees)


    for i in range(len(all_bees)):

        image = all_bees[i] 
        url = image.url
        image_id = int(image.metadata['image_id'])
        zip_code = str(image.metadata['zip_code']) 

        if 'bee' in image.concepts:

            if 'healthy' in image.concepts: 
                health = 'y' 

            else:
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
    Trains, then Makes a prediction with the model.
    @model_version_id = integer, version this time around
   
    @path = local filename
    """

    # Set a model version id because I want to keep track of progress
    # model.model_version = model_version_id

    # print(model.model_version)

    # Train model!
    cl_model.train(sync=False) # False goes faster


    response = cl_model.predict_by_filename(path)
    pprint(response)
    
    # response_id = response['outputs'][0]['data']['concepts'][0]['id']
    
    # response_confidence = response['outputs'][0]['data']['concepts'][0]['value']
    
    # response_datetime = response['outputs'][0]['created_at']

    # print(response_datetime)


    # response_tuple = (response_id, response_confidence, response_datetime)
    # pprint("t", response_tuple)
    # return response_tuple



def process_img_upload(user_id, photo_url, photo_health):
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

def process_upload(img_path):
    """ method that gets called when a user uploads one photo 
    - Gets prediction for user (using model version n)
    - Adds new photo to model
    - Adds new photo to bee_db
    - Trains new model (version n+1)

    @param img_path , the local path 'uploads/..'
    @return prediction tuple (response_id, response_confidence)
    """

    prediction_tuple = predict_with_model(img_path)

    # Attempt to add image to clarafai model
    # We need to do this first because the model.py database object has a URL.
    # So first thing we need to create is a URL.
    # add_image_clar = add_new_image_to_clar(,


    #                                         )

    # # Created is a URL ready to add to db.
    # add_image_db = add_new_image_to_db(user_id=user_id,


    #                                 )


    # Train model!



    return prediction_tuple



if __name__ == '__main__':

    # Flask database initialization
    from server import app
    connect_to_db(app)
    db.create_all()

    # Get model versions:
    # pprint(cl_model.list_versions())

    # Clear it from Clarifai. Be careful!!!!!!!!!
    # clarifai_app.inputs.delete_all()
    # print('Successfully deleted all.')

    # # Give images and concepts from file to Clarifai
    add_images_concepts_to_clar(seed_filename)
    print('Successfully added all.')

    # Add Bees to our database from Clarifai
    # load_bees_from_clarifai_to_db()

    # cl_model.train(sync=False) # False goes faster

    # process_upload( 
    #     img_path='uploads/download.jpeg')

