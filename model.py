"""Models and database functions for texts project."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)
db = SQLAlchemy()


##############################################################################
# Model definitions

class Person (db.Model):
    """A recipient of a message."""

    __tablename__ = "people" 

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)

    def __repr__(self):
        """provide helpful representation when printed"""

        return f"""ID: {self.id}, Name:{self.name}"""

class PersonNumber (db.Model):

    __tablename__ = "peoplenumbers"

    phone_number = db.Column(db.String, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))

    def __repr__(self):
        """provide helpful representation when printed"""

        return f"""
                Phone Number: {self.phone_number}
                Person ID: {self.person_id}
                """

class Message(db.Model):
    """A text."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=True)
    date = db.Column(db.BigInteger)
    sender_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('people.id'))

    sender = db.relationship('Person', foreign_keys=[sender_id], backref='messages_received')
    recipient = db.relationship('Person', foreign_keys=[recipient_id], backref='messages_sent')
    folders = db.relationship("Folder", secondary="foldermessages", backref="messages")


    def convert_date(self):
        """date is given as a timestamp, seconds since 0:00, 1/1/2001, convert to actual date"""

        jan1_2001 = "01-Jan-2001"

        jan1_2001 = datetime.strptime(jan1_2001, "%d-%b-%Y")
        if self.date == 0:
            return "Date not available"
        elif 0 < self.date < 10000000000: # if date is in seconds
            actual_date = jan1_2001 + timedelta(0, self.date)
        elif self.date > 10000000000: # if date is in nanoseconds
            actual_date = jan1_2001 + timedelta(0, 0, self.date/1000)

        UTC_time_diff = -7*60*60 # 7 hours converted into seconds

        actual_date += timedelta(0, UTC_time_diff)

        actual_date = actual_date.strftime("%b %d, %Y, %I:%M:%S %p") # 'Aug 10, 2012, 01:15:22 AM'

        return actual_date

    def __repr__(self):
        """provide helpful representation when printed"""

        return f"""
                ID: {self.id}, 
                Text: {self.text}, 
                Date: {self.convert_date()}, 
                Sender_ID: {self.sender_id}
                Recipient_ID: {self.recipient_id}
                """

class Folder(db.Model):
    """A folder that can contain many texts."""

    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, unique=True)

class FolderMessage(db.Model):
    """An association table between texts and folders."""

    __tablename__ = "foldermessages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)

class User (db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password_hash = db.Column(db.String)

    def __repr__(self):
        """provide helpful representation when printed"""

        return f"""ID: {self.id}, Name:{self.name}, Email: {self.email}"""
##############################################################################
# Helper functions-

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///texts'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print("Connected to DB.")
