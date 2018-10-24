"""Seeding database for texts project."""

import sqlite3
from model import Message, Person
from model import connect_to_db, db 

from datetime import datetime, timedelta

def load_phone_numbers(database):
    """Load phone numbers from sqlite database into psql database."""

    print("Making Contacts Dictionary")

    sqliteConnection=sqlite3.connect("contacts.db")
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT c0First, c1Last, c16Phone FROM ABPersonFullTextSearch_content")

    contacts = {}

    for row in sqliteCursor:
        ph_numbers = row[2] # example: '1 (203) 739-9406 +12037399406 01112037399406 0012037399406 12037399406 2037399406 7399406 '
        if ph_numbers:
            if ")" in ph_numbers:
                ph_numbers = ph_numbers.split(")")
                ph_numbers = ph_numbers[1]
                ph_numbers = ph_numbers.split(" ")
                ph_number = ph_numbers[2]
            else: # example: '+12037399406 0111...'
              ph_numbers = ph_numbers.split(" ")
              ph_number = ph_number[0]

        if row[0] and row[1]:
            full_name = row[0] + " " + row[1]
        if not row[1]:
            full_name = row[0]
        if not row[0]:
            full_name = row[1]

        contacts[ph_number] = full_name

    print("Populating people table")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Person.query.delete()

    sqliteConnection = sqlite3.connect(database)
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT ROWID, id FROM handle")

    for row in sqliteCursor:
        phone_number = Person(id=row[0], phone_number=row[1])
        if row[1] in contacts.keys():
            phone_number.name = contacts[row[1]]

        db.session.add(phone_number)
    
    # make me id 0 - later make this user input, or grab from registration info?
    me = Person(id=0, phone_number="", name='Priyanka Altman') 

    db.session.add(me)

    db.session.commit()

def load_messages(database):
    """Load messages from sqlite database into psql database."""
    print("Populating messages table")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate messages
    Message.query.delete()

    sqliteConnection = sqlite3.connect(database)
    sqliteCursor = sqliteConnection.cursor()

    # populate new phone numbers table
    sqliteCursor.execute("SELECT text, handle_id, date, is_from_me FROM message")

    for row in sqliteCursor:
        # if the text was sent FROM me
        if row[3] == 1:
            message = Message(text=row[0], 
                              date=row[2], 
                              sender_id=0, 
                              recipient_id=row[1])
        
        # if the text was sent TO me
        else:
            message = Message(text=row[0], 
                              date=row[2], 
                              sender_id=row[1], 
                              recipient_id=0)
        

        db.session.add(message)

    db.session.commit()
    print("Done!")


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_phone_numbers("phone_backup.db")
    load_messages("phone_backup.db")


