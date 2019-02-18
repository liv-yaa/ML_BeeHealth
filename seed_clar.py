""" File that seeds health_db database from Kaggle data in kaggle_data/ 
FROM CLARIFAI API - gets images

"""

# API Requests / Get
from clarifai.rest import ClarifaiApp
clarifai_app = ClarifaiApp(api_key="58dc8755e39d4043a98554b44bbcaf56")
# model = app.public_models.general_model
# response = model.predict_by_url('url!!')

# Local scripts
from model import User, Photo, Bee, connect_to_db, db
from server import app


def load_bees_from_clarifai():
    """ Load bee objects by using GET request from Clarifai API
    https://clarifai.com/developer/guide/inputs#get-inputs
    
     """

    print("Getting bees")

    all_bees = list(clarifai_app.inputs.get_all())

    print(len(all_bees))

    # Iterate and create Bee objects
    # for i in range(len(all_bees)):
    for i in range(30): # FOR NOW

        bee_id = i 
        bee = all_bees[i] # Gets object from list
        health = "y" # for now
        url = bee.url # Attribute

        new_bee = Bee(bee_id=bee_id,
                        url=url,
                        health=health,
                        )

        print(new_bee)

        db.session.add(new_bee)

        # provide some sense of progress
        if i % 100 == 0:
            print("Status: ", i)






    # Commit all bees to the database
    db.session.commit()


if __name__ == '__main__':
    connect_to_db(app)
    db.create_all()

    load_bees_from_clarifai()