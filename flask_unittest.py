# http://flask.pocoo.org/docs/0.12/testing/
# https://fellowship.hackbrightacademy.com/materials/ft25a/lectures/testing/

import os
from unittest import TestCase
from server import app
from model import connect_to_db, db, example_data # example_data?
from flask import session

class FlaskTestCase(TestCase):
    """Flask tests."""

    def setUp(self):
        """Stuff to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()

        # Show Flask errors that happen during tests
        app.config['TESTING'] = True

    def test_index(self):
        """ Test landing page. """

        result = self.client.get("/")

