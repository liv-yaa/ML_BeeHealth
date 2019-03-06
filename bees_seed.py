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


def add_bees_to_clar(csv_filename):
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
                            'zipcode':'str',
                            } 
    )

    # Get the maximum bee_id in the clarafai model and add 1
    next_id = get_hi_input_id() + 1

    print("next_id", next_id)

    # for i in range(len(df)):
    for i in range(40): # FOR NOW

        image_id = str(next_id + i)
        health_ = str(df.loc[i][5])
        datetime = str(df.loc[i][0])
        csv_filename = str(df.loc[i][1])
        zipcode = str(df.loc[i][3])

        # Edit health (a string) to make it a binary value (better for this purpose)
        health = 'y' if health_ == 'healthy' else 'n'

        # Edit fileanme to have the local path:
        local_filename = 'images/bees/' + csv_filename

        # print(image_id, health, datetime, csv_filename, zipcode, local_filename)

        if (health == 'y'):
            
            concepts=['health', 'is_bee'] # a list of concept names this image is associated with
            not_concepts=None  # a list of concept names this image is not associated with

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
                                    'zipcode': zipcode,
                                    },
                        # This could be a JSON object with long/lat https://clarifai.com/developer/guide/searches
                        # allow_duplicate_url=True,
                        )

        print("After", img.concepts, " are concepts and not concepts are ", img.not_concepts)

        image_list.append(img)

    print("Image list" , image_list)
    clarifai_app.inputs.bulk_create_images(image_list)


def add_nonbees_to_clar():

    # Add nonbees: This doesn't work...just manually did it for now :/
    # SO THIS PART ABOVE WORKS the part now is figuring out how to get nonbees.
    print("ADDING NONBEES")
    image_list = []
    
    nonbees = glob.glob('images/not_bees/*png')

    # print("nonbees", nonbees)

    # Get the maximum bee_id in the database
    next_id = get_hi_input_id() + 1

    print( "nextt_id", next_id )


    for i, img_name in enumerate(nonbees):
    # for i in range(200):

        nonbee_id = str(next_id + i)
        

        print("Before", img_name, nonbee_id)


        img = clarifai_app.inputs.create_image_from_filename(filename=img_name, 
                            image_id=nonbee_id,
                            concepts=None,
                            not_concepts=['is_bee'], 
                            metadata=None,
                            
                            allow_duplicate_url=True,
                            )

        # print("After creating img", str(img.filename), img.image_id) 
        print("After creating img", dir(img)) 

        # For the life of me can't figure out
    #     # Why can I not see this filename?
    #     # However, it looks like it's working to add the files to the model!

        print(img.concepts, " are concepts and not concepts are ", img.not_concepts)

        image_list.append(img)

    print("Image list added", image_list)

    if image_list != []:
        clarifai_app.inputs.bulk_create_images(image_list)


def load_bees_from_clarifai_to_db(all_bees):
    """ Load Image objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs 
    Convert Image objects to Bee objects, & add to our database.
    """

    all_images = list(all_bees)

    for img in all_images:
        print(img)
        # print(type(img))
        print(dir(img))
       
        image_url = img.url
        image_score = img.score
        
            
        if (img.concepts and img.not_concepts):
              
            image_concepts = img.concepts
            image_not_concepts = img.not_concepts

            # Unpack concepts to get image_health: 
            image_health = 'y' if 'health' in image_concepts and 'is_bee' in image_concepts else 'n'



            if (img.metadata):

                print("Alert metadata", img.metadata)
                image_dt = img.metadata['datetime']
                

                # # if (img.metadata['user_id']):
                #     image_user_id = int(img.metadata['user_id']) ## 
                    

                if (img.metadata['zipcode']):
                    image_zip = int(img.metadata['zipcode'])


                   

                # # if (img.metadata['image_id']):
                #     image_img_id = int(img.metadata['image_id'])
                   

            
        else:
            print("Alert")
            image_concepts = None
            image_not_concepts = None
            image_health = None

            image_dt = None

            image_user_id = None

            image_zip = None

            image_img_id = None

        print("After", image_concepts, " are concepts and not concepts are ", image_not_concepts)
        print("image_health", image_health)
        print("image_url", image_url)
        print("image_score", image_score)

        print("image_dt", image_dt)
        print("image_user_id", image_user_id)
        print("image_zip", image_zip) 
        print("image_img_id", image_img_id)



        print()





    #     zipcode = str(image.metadata['zipcode']) 

        # print("zipcode", zipcode)
    #     # print(type(zipcode))

    #     if 'bee' in image.concepts:

    #         if 'healthy' in image.concepts: 
    #             health = 'y' 

    #         else:
    #             health = 'n'

    #         # Create a bee
    #         a_bee = Bee(bee_id=image_id,
    #                     user_id=None, # All database bees will have no user_id
    #                     url=url,
    #                     health=health,
    #                     zipcode=zipcode,
    #                     )

    #         db.session.add(a_bee)

    # # Commit all Bee objects to the database
    # db.session.commit()


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
    # pprint(response)
    
    response_id = response['outputs'][0]['data']['concepts'][0]['id']
    
    response_confidence = response['outputs'][0]['data']['concepts'][0]['value']
    
    response_datetime = response['outputs'][0]['created_at']

    # print(response_datetime)


    response_tuple = (response_id, response_confidence, response_datetime)
    print("t", response_tuple)
    return response_tuple



def process_upload(user_id, health, local_filename, zipcode):
    """ Get prediction tuple from a user's uploaded image (which has metadata)
    Create a new Image object and add it to Clarifai 

    @ return the new Image object (Clar), which has a URL, and is ready to become our Bee object.
    """

    # print("user_id", user_id)
    # print("health", health)
    # print("local_filename", local_filename)
    # print("zipcode", zipcode)

    image_id = str(get_hi_input_id() + 1)
    # print("image_id", image_id)

    # get prediction_tuple which is (response_id, response_confidence, response_datetime)
    prediction_tuple = predict_with_model(local_filename)
    # print("prediction_tuple", prediction_tuple)

    # # Edit health (a string) to make it a binary value (better for this purpose)
    health = 'y' if health == 'healthy' else 'n'
    # print(
    #     "health now ", health)

    response_id = prediction_tuple[0]
    response_confidence = prediction_tuple[1]
    datetime = prediction_tuple[2]

    # print("response_id", response_id)
    # print("response_confidence", response_confidence)
    # print("datetime", datetime)


    if (health == 'y'):
            
        concepts=['health', 'is_bee'] # a list of concept names this image is associated with
        not_concepts=None  # a list of concept names this image is not associated with

    else:
        concepts = ['is_bee']
        not_concepts = ['health']
       
    # print("Before", concepts, " are concepts and not concepts are ", not_concepts)
    # print("")

    # Create image and add to Clar.
    img = clarifai_app.inputs.create_image_from_filename(
                    filename=local_filename, 
                    image_id=image_id,
                    concepts=concepts,
                    not_concepts=not_concepts,
                    metadata={ 'image_id': image_id,
                                'datetime': datetime, 
                                'zipcode': zipcode,
                                'user_id': user_id,
                                },
                    allow_duplicate_url=True,
                    )

    # Unpack all data in the newly created Image object    
    image_concepts = img.concepts
    image_not_concepts = img.not_concepts
    print("After", image_concepts, " are concepts and not concepts are ", image_not_concepts)

    # Unpack concepts to get image_health:
    image_health = 'y' if 'health' in image_concepts and 'is_bee' in image_concepts else 'n'
    print("image_health", image_health)

    image_url = img.url ##
    # print("image_url", image_url)

    image_score = img.score
    # print("image_score", image_score)

    image_dt = img.metadata['datetime']
    # print("image_dt", image_dt)

    image_user_id = int(img.metadata['user_id']) ## 
    # print("image_user_id", image_user_id)

    image_zip = int(img.metadata['zipcode'])
    # print("image_zip", image_zip)

    image_img_id = int(img.metadata['image_id'])
    # print("image_img_id", image_img_id)


    print()
    print()

    # Create a new Bee and add it to the database, pasing in metadata from img (Image object)
    add_new_image_to_db(user_id=image_user_id,
                        url=image_url,
                        health=image_health,
                        zipcode=image_zip,
                        image_id=image_img_id
                        )

    return prediction_tuple

    

def add_new_image_to_db(user_id, url, health, zipcode):
    """ Get one image (hosted by clarafai) - which has a url (on Clar)
    Create a Bee object and add it to the database 
    """

    # Get the maximum bee_id in the database
    # Note, the bee_id is not the same as the image_id in previous methods!
    result = db.session.query(func.max(Bee.bee_id)).one()
    bee_id = int(result[0]) + 1

    print(bee_id)


    # Create a new bee:
    bee = Bee(bee_id=bee_id,
                user_id=user_id,
                url=url, # From user_file
                health=health,
                zip_code=zipcode,
                image_id=image_id,

                )



    # flash("Bee created successfully.")

    # print("Bee id", bee.bee_id)
    # print("user_id", bee.user_id)
    # print()

    db.session.add(bee)
    db.session.commit()
    # flash("Bee added to database. Thank you!")

    # return boolean?!

    return None



def get_hi_input_id():
    # Get the highest input_id for all the bees in clar
    # @return maximum , an int
    all_ids = [bee.input_id for bee in clarifai_app.inputs.get_all()]

    count_len = len(all_ids)


    if all_ids == []:
        return 0
    else:
        
        # maximum = int(max(all_ids))
        # # print(type(maximum)) # an int
        # return maximum
        return count_len




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



    # # # # Give images and concepts from file to Clarifai
    # add_bees_to_clar(seed_filename)
    # print('Successfully added all bees.')
    # add_nonbees_to_clar()
    # print('Successfully added all nonbees.')


    # print(get_hi_input_id())

    # Add Bees to our database from Clarifai
    all_bees = clarifai_app.inputs.get_all()
    load_bees_from_clarifai_to_db(all_bees=all_bees)

    # Test
    # process_upload( 
    #     user_id=1, 
    #     health='healthy',
    #     local_filename='uploads/download.jpeg',
    #     zipcode='12345'
    #     )

    # process_upload( 
    #     user_id=1, 
    #     health='unhealthy',
    #     local_filename='uploads/001_043.png',
    #     zipcode='22111'
    #     )


    # print(predict_with_model(path='uploads/download.jpeg'))

