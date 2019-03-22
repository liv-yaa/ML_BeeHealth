# http://flask.pocoo.org/docs/0.12/testing/
# https://fellowship.hackbrightacademy.com/materials/ft25a/lectures/testing/

# import os
from unittest import TestCase
from server import app
from model import Bee, User, connect_to_db, db, example_data
# from flask import session

class FlaskTestCase(TestCase):
    """Flask tests."""

    def setUp(self):
        """Stuff to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()

        # Connect to temporary database
        connect_to_db(app, "sqlite:///")

        # Create tables and add sample data
        db.create_all()
        example_data()

    def test_find_bee(self):
        """Can we find an employee in the sample data?"""

        bee1 = Bee.query.filter(Bee.bee_id == "1").first()
        self.assertEqual(bee1.name, "1")


    def test_index(self):
        """ Test landing page. """

        # result = self.client.get("/")
        self.assertIn("THE BEE MACHINE")

    def test_login(self):
        """ Test login page. """

        result = self.client.post("/login",
                                    data={"email": "ww@ww.ww", "password": "ww"},
                                    follow_redirects=True
                                    )
        self.assertIn("Welcome, User No.", result.data)




if __name__=="__main__":
    import unittest

    unittest.main()


