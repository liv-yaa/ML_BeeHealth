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
from clarifai.rest import FeedbackInfo, ClarifaiApp #  Clarifai Application Object
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
MODEL_ID = 'BeeHealth'
cl_model = clarifai_app.models.get(MODEL_ID)
seed_filename = "bee_data.csv"
THRESHOLD = 0.4     # Value for prediction 


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

    print("ADDING BEE IMAGES")

    for i in range(len(df)):
    # for i in range(10): # FOR NOW

        image_id = str(next_id + i)
        health_ = str(df.loc[i][5])
        datetime = str(df.loc[i][0])
        csv_filename = str(df.loc[i][1])
        zipcode = str(df.loc[i][3])
        user_id = None

        # Edit health (a string) to make it a binary value (better for this purpose)
        health = 'y' if health_ == 'healthy' else 'n'

        # Edit fileanme to have the local path:
        img_name = 'images/bees/' + csv_filename

        print("local img_name", img_name )

        # print(image_id, health, datetime, csv_filename, zipcode, local_filename)

        if (health == 'y'):
            
            concepts=['health', 'is_bee'] # a list of concept names this image is associated with
            not_concepts=[]  # a list of concept names this image is not associated with

        else:
            concepts = ['is_bee']
            not_concepts = ['health']
           
        print("Before", concepts, " are concepts and not concepts are ", not_concepts)
        print("image_id", image_id)
        img = clarifai_app.inputs.create_image_from_filename(filename=img_name, 
                        image_id=image_id,
                        concepts=concepts,
                        not_concepts=not_concepts,
                        metadata={ 'image_id' : image_id,
                                    'user_id': user_id,
                                    'datetime': datetime, 
                                    'zipcode': zipcode,
                                    },
                        allow_duplicate_url=True,
                        )

        print("After", img.concepts, " are concepts and not concepts are ", img.not_concepts)
        print("image_id", img.metadata['image_id'])
        print("img.input_id", img.input_id)
        print("img.url", img.url)
        print("img.filename", img.filename)
        print()
        print(dir(img))

        image_list.append(img)

    print("Image list" , image_list)
    clarifai_app.inputs.bulk_create_images(image_list)


def add_nonbees_to_clar():
    """
    Load images to Clarifai model, using custom tags from the csv file.
    """

    print("ADDING NONBEES")
    image_list = []
    
    nonbees = glob.glob('images/not_bees/*png')

    # Get the maximum bee_id in the database
    # next_id = get_hi_input_id() + 1

    next_id = 100000 # Hard coding this b/c my helper function was too slow
    print("next_id", next_id)

    for i, img_name in enumerate(nonbees):
    # for i in range(200):

        image_id = str(next_id + i)
        

        print("Before", img_name, image_id)


        img = clarifai_app.inputs.create_image_from_filename(
                            filename=img_name, 
                            image_id=image_id,
                            concepts=[],
                            not_concepts=['is_bee'], 
                            metadata={ 'image_id' : image_id,
                                'user_id': None,
                                'datetime': None, 
                                'zipcode': None,
                                },
                            
                            allow_duplicate_url=True,
                            )

        # print("After creating img", str(img.filename), img.image_id) 
        print("After creating img", dir(img)) 
        print("image_id", img.metadata['image_id'])
        print("img.input_id", img.input_id)
        print("img.url", img.url)
        print("img.filename", img.filename)
        print()

        print(img.concepts, " are concepts and not concepts are ", img.not_concepts)

        image_list.append(img)

    print("Image list added", image_list)

    if image_list != []:
        clarifai_app.inputs.bulk_create_images(image_list)


def load_bees_from_clarifai_to_db(all_images):
    """ Load Image objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs 
    Convert Image objects to Bee objects, & add to our database.

    @all_images is both bee and nonbee Images.
    - nonbee Images will not have metadata
    - bee Images will have metadata:
        - metadata will be a dict {}

    """

    print("Length of all_images", len(all_images))

    # Initialize bee_id
    i = 1 

    for img in all_images:
        print(img)
        # print(type(img))
        print(dir(img))
       
        image_url = img.url
        image_score = img.score
        image_concepts = img.concepts
        image_not_concepts = img.not_concepts

        # Unpack concepts to get image_health: 
        if (image_concepts != None):
            image_health = 'y' if 'health' in image_concepts else 'n'
        else:
            image_health = None


        try:
            if (img.metadata['datetime']):
                image_dt = img.metadata['datetime']
            else:
                image_dt = None
                
            if img.metadata:
                if (img.metadata['zipcode']):
                    image_zip = int(img.metadata['zipcode'])
                elif (img.metadata['zip_code']):
                    image_zip = int(img.metadata['zip_code'])
            else:
                image_zip = None


            if (img.metadata['image_id']):
                image_img_id = int(img.metadata['image_id'])
            else:
                image_img_id = None
        except KeyError:
            print("KeyError")
        except:
            print("Other error")

        if img.concepts and 'is_bee' in img.concepts: # Make sure that only bees are added! Not nonbees!

            # Create a bee
            a_bee = Bee(bee_id=i,
                        user_id=None, # All database bees will have no user_id
                        url=image_url,
                        health=image_health,
                        zip_code=image_zip,
                        image_id=image_img_id
                        )

            db.session.add(a_bee)

            i = i + 1 # Increment

            print("bee added, a_bee.bee_id", a_bee.bee_id)
            print()

    print("Length of all_images ", len(all_images))

    # Commit all Bee objects to the database
    db.session.commit()


def predict_with_model(path):
    """ https://clarifai.com/developer/guide/train#predict-with-the-model
    Trains, then Makes a prediction with the model.
    @model_version_id = integer, version this time around
   
    @path = local filename
    """

    # # Set a model version id because I want to keep track of progress
    # model.model_version = model_version_id

    # print(model.model_version)

    # Train model!
    cl_model.train(sync=False) # False goes faster

    response = cl_model.predict_by_filename(path)
    # pprint(response)

    response_dict = {}

    for i in range(2):

        response_name_i = response['outputs'][0]['data']['concepts'][i]['name']

        # print(response_name_i)

        if response_name_i == 'health':
            health_response_name = response['outputs'][0]['data']['concepts'][i]['name']
            health_response_value = response['outputs'][0]['data']['concepts'][i]['value']

        elif response_name_i == 'is_bee':
            is_bee_response_name = response['outputs'][0]['data']['concepts'][i]['name']
            is_bee_response_value = response['outputs'][0]['data']['concepts'][i]['value']
    

    # print("is_bee_response_name", is_bee_response_name)
    # print("is_bee_response_value", is_bee_response_value)
    # print("health_response_name", health_response_name)
    # print("health_response_value", health_response_value)

    # Add results to a succinct dictionary
    response_dict['is_bee'] = (is_bee_response_name, is_bee_response_value)
    response_dict['health'] = (health_response_name, health_response_value)


    # print(response_dict)
        
    return response_dict



def process_upload(user_id, health, local_filename, zipcode):
    """ Get prediction dict from a user's uploaded image (which has response)
    Determine whether prediction was accurate.
    Help train the model based on this information.
    Create a new Image object and add it to Clarifai. 

    @ return the new Image object (Clar), which has a URL, and is ready to become 
    our Bee object in the database
    """
    # # Edit health (a string) to make it a binary value (better for this purpose)
    health = 'y' if health == 'healthy' else 'n'
    # print(
        # "health now ", health)


    # Get prediction_dict which is key:(name, value)
    prediction_dict = predict_with_model(local_filename) #Clar method
    # print("prediction_dict", prediction_dict)

    # Get the rest of the values from prediction_tuple
    
    is_bee_output_id = prediction_dict['is_bee'][0]
    is_bee_output_value = prediction_dict['is_bee'][1]
    health_output_id = prediction_dict['health'][0]
    health_output_value = prediction_dict['health'][1]
    

    print("is_bee", is_bee_output_id, is_bee_output_value)
    print("health", health_output_id, health_output_value)

    predicted_concepts = []
    predicted_not_concepts = []


    # if is_bee_output_id == 'is_bee':

        

    #     if is_bee_output_value > THRESHOLD: # Should I change this?

    #         predicted_concepts.append('is_bee')
    #         print('Prediction says is_bee')


    # else:
    #     print('Prediction says NOT is_bee')


    # if health_output_id == 'health':

        

    #     if health_output_value > THRESHOLD: # Should I change this?
    #         predicted_not_concepts.append('health')
    #         print("Prediction says health")

    # else:
    #     print('Prediction says NOT health')


    # print("predicted_concepts", predicted_concepts)
    # print("predicted_not_concepts", predicted_not_concepts)



    # if ('health' in concepts):

    #     if ('health' in predicted_concepts):

    #         give_model_feedback(
    #             input_id='health', 
    #             url=url,                 
    #             concepts=predicted_concepts,
    #             not_concepts=predicted_not_concepts,
    #             output_id='health',
    #             )

    #     else:
    #         give_model_feedback(
    #             input_id='health', 
    #             url=url,                 
    #             concepts=predicted_concepts,
    #             not_concepts=predicted_not_concepts,
    #             output_id='health',
    #             )


       

    # # Get other metadata needed
    image_id = str(get_hi_input_id() + 1)
    # print("image_id", image_id)
    print("user_id", user_id)
    print("health", health)
    print("local_filename", local_filename)
    print("zipcode", zipcode)





    # We need to get 
        # input_id (str) - the id of what it SHOULD BE
        # url (str), 
        # concepts, not_concepts (inferred), 
        # output_id (required) - the id of the output RECIEVED from the API call



    # Create image and add to Clar.


    img = clarifai_app.inputs.create_image_from_filename(
                    filename=local_filename, 
                    image_id=image_id,
                    concepts=concepts,
                    not_concepts=not_concepts,
                    metadata={ 'image_id': image_id,
                                'user_id': user_id,
                                'datetime': datetime, 
                                'zipcode': zipcode,
                                'response_confidence': response_confidence,
                                
                                },
                    allow_duplicate_url=True,
                    )

    # # Unpack all data in the newly created Image object    
    image_concepts = img.concepts
    image_not_concepts = img.not_concepts
    print("After", image_concepts, " are concepts and not concepts are ", image_not_concepts)

    i = clarifai_app.inputs.get(input_id=image_id)

    print("Successfully added to clar app: ", i.input_id)

    # # Unpack concepts to get image_health:

    
    image_health = 'y' if 'health' in image_concepts and 'is_bee' in image_concepts else 'n'
    print("image_health", image_health)

    image_url = img.url ##
    print("image_url", image_url)

    image_score = img.score
    print("image_score", image_score)

    if img.metadata:
        image_dt = img.metadata['datetime']
        print("image_dt", image_dt)

        image_user_id = int(img.metadata['user_id']) ## 
        print("image_user_id", image_user_id)

        image_zip = int(img.metadata['zipcode'])
        print("image_zip", image_zip)

        image_img_id = int(img.metadata['image_id'])
        print("image_img_id", image_img_id)

        image_confidence = int(img.metadata['response_confidence'])
        print("image_confidence", image_confidence)

    else:
        print("not a bee")


    # print()
    # print()

    # # Create a new Bee and add it to the database, pasing in metadata from img (Image object)
    success = add_new_image_to_db(user_id=image_user_id,
                        url=image_url,
                        health=image_health,
                        zipcode=image_zip,
                        image_id=image_img_id
                        )

    # new_tuple THURSDAY ADD SUCCESS TO THIS
    # I am adding this because in order 

    return prediction_tuple, success
    # Needs to return health, performance


def give_model_feedback(input_id, url, concepts, not_concepts, output_id):
    """ https://www.clarifai.com/developer/guide/feedback#prediction-feedback
    # This is going to depend on performance 

    Here:
    - input_id = what it should be ('health' or 'is_bee')
    - output_id = the id ass'd with the output recueved from the prediction call

    If the prediction is correct:
    

    """
    # We need to get 
        # input_id (str) - the id of what it SHOULD BE
        # url (str), 
        # concepts, not_concepts (inferred), 
        # output_id (required) - the id of the output RECIEVED from the API call


    cl_model.send_concept_feedback(
        # input_id='{input_id}', # What format should this be in?? String!
        input_id=input_id, # String
        url=url, # String
        concepts=concepts, # List of strings
        not_concepts=not_concepts, # List of strings
        feedback_info=FeedbackInfo(event_type='annotation',
                                    # output_id='{output_id}', @ 
                                    output_id=output_id, # This should be a string idk why its in a dict
                                    ), # 

        ) # Returns None. Just passes this along to Clarafai.


    

def add_new_image_to_db(user_id, url, health, zipcode, image_id):
    """ Get one image (hosted by clarafai) - which has a url (on Clar)
    Create a Bee object and add it to the database 
    """

    # Get the maximum bee_id in the database
    # Note, the bee_id is not the same as the image_id in previous methods!
    result = db.session.query(func.max(Bee.bee_id)).one()
    bee_id = int(result[0]) + 1

    print(bee_id)

    success = False

    try:


        # Create a new bee:
        bee = Bee(bee_id=bee_id,
                    user_id=user_id,
                    url=url, # From user_file
                    health=health,
                    zip_code=zipcode,
                    image_id=image_id,

                    )



        print("Bee created successfully.")

        print("Bee id", bee.bee_id)
        print("user_id", bee.user_id)
        print()

        db.session.add(bee)
        db.session.commit()
        # flash("Bee added to database. Thank you!")

        print("Bee added to database. Thank you!")


        # i = db.session.query(Bee).filter_by(bee_id=bee_id)

        print("Successfully added to db: ", bee.bee_id)

        success = True

    except:
        print("Unable to create Bee object.")


    return success



def get_hi_input_id():
    # Get the highest input_id for all the bees in clar
    # @return maximum , an int
    all_ids = [bee.input_id for bee in clarifai_app.inputs.get_all()]

    count_len = len(all_ids)


    if count_len > 0:
        
        # maximum = int(max(all_ids))
        # # print(type(maximum)) # an int
        # return maximum
        return count_len
    else:
        return 0



def check_prediction(health_string, prediction_tuple):
    """ Checks whether prediction tuple matches input of health specified by user """
    response_string = prediction_tuple[0]
    response_confidence = prediction_tuple[1]

    print("response_string", response_string)
    print(
        "response_confidence", response_confidence
        )

    return response_string == health_string




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

    # all_ = list(clarifai_app.inputs.get_all())
    # # for i in all_:
    # #     print(i.metadata['image_id'], "is uploaded")

    # # Add Bees to our database from Clarifai
    # load_bees_from_clarifai_to_db(all_images=all_)
    # print("Upload success")

    # Test
    process_upload( 
        user_id=1, 
        health='healthy',
        local_filename='uploads/download.jpeg',
        zipcode='12345'
        )
    print(
        )

    process_upload( 
        user_id=1, 
        health='unhealthy',
        local_filename='uploads/001_043.png',
        zipcode='22111'
        )


    # print(predict_with_model(path='uploads/download.jpeg'))
    # print(predict_with_model(path='uploads/001_043.png'))

