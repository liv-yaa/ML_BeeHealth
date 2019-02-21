""" File that seeds health_db database from Kaggle data in kaggle_data/ 
FROM CLARIFAI API - gets images

"""

# API Requests / Get
from clarifai.rest import ClarifaiApp
clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56")
MODEL_ID = 'test'


from sqlalchemy import func
import pandas as pd

from model import Bee, connect_to_db, db
# from server import app

def set_val_bee_id():
    """ WHAT IS THIS FUNCTION FOR??? """

    # Get the maximum user_id in the database:
    result = db.session.query(func.max(Bee.bee_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('bees_bee_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


def add_images_concepts(csv_filename):
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


def clear_all():
    """
    BE CAREFUL!
    Clear all images to Clarifai model, including concepts.
    """
    clarifai_app.inputs.delete_all()


def load_bees_from_clarifai():
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


def add_photo_to_clarifai():
    """ Get a users photo and add it to the database. """

    # Get the maximum user_id in the database??? set_val_bee_id??? do i need to?
    pass


def create_model(model_id):
    """ https://clarifai.com/developer/guide/train#train 
    Creates a model with a given model_name
    """
    model = clarifai_app.models.create(model_id, concepts=['health'])

    return model


def train_model(model_id):
    """ Trains a model with a given model_id (name) """

    model = clarifai_app.models.get(model_id)

    model.train()

    model_name = model.model_name

    print(f"Model {model_name} trained.")
    

def predict_with_model(model_id, model_version_id, url):
    """ https://clarifai.com/developer/guide/train#predict-with-the-model
    Makes a prediction with the model.
    @model_id = name of the model
    @model_version_id = integer, version this time around
    @url = a string, the URL of the photo we are analyzing!

    """

    model = clarifai_app.models.get(model_id)

    # Set a model version id because I want to keep track of progress
    model.model_version = model_version_id

    print(model.model_version)

    response = model.predict_by_url(url)

    print( response.created_at)




if __name__ == '__main__':

    # Flask database initialization
    # connect_to_db(app)
    # db.create_all()

    # Clear it from Clarifai. Be careful!!!!!!!!!
    # clear_all()
    # print('Successfully deleted all.')

    # # Give images and concepts from file to Clarifai
    # seed_filename = "bee_data.csv" 
    # add_images_concepts(seed_filename)
    # print('Successfully added all.')

    # Add Bees to our database from Clarifai
    # load_bees_from_clarifai()

    train_model(MODEL_ID)

    print(predict_with_model(model_id=MODEL_ID, 
        model_version_id='2', 
        url='https://www.ahs.com/static-srvm/trmx/blog-images/How-To-Tell-If-Youre-Allergic-To-A-Bee-Sting-Main.jpg'))
