"""Seeding database for texts project."""

import sqlite3
from model import Message, Person, PersonNumber
from model import connect_to_db, db 
from collections import defaultdict
import re
from datetime import datetime, timedelta

def make_contacts_dictionary():
    """Load phone numbers from sqlite database into psql database."""

    print("Making Contacts Dictionary", datetime.now())

    sqliteConnection=sqlite3.connect("contacts.db")
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT c0First, c1Last, c16Phone FROM ABPersonFullTextSearch_content")

    contacts = defaultdict(set)

    for row in sqliteCursor:

        try:
            first_name = row[0]
        except IndexError:
            first_name = ''

        try:
            last_name = row[1]
        except IndexError:
            last_name = ''
    
        full_name = f"{first_name} {last_name}"


        try:
            ph_numbers = row[2] # example: '1 (203) 739-9406 +12037399406 01112037399406 0012037399406 12037399406 2037399406 7399406 '
        except IndexError:
            continue

        pattern = re.compile('\+\d\d\d\d\d\d\d\d\d\d\d')

        try:
            match = pattern.search(ph_numbers) 
        except TypeError:
            continue

        if match:
            ph_number = match.group()

            if ph_number:
                contacts[full_name].add(ph_number)

    return contacts

def load_people_table(database):

    print("Populating people table", datetime.now())

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Person.query.delete()

    sqliteConnection = sqlite3.connect(database)
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT id FROM handle")

    contacts = make_contacts_dictionary()

    for row in sqliteCursor:
        phone_number = row[0]

        # if this phone number isn't already in the table
        if Person.query.filter_by(phone_number=phone_number).all() == []:
            person = Person(phone_number=phone_number)

            for (name, phone_number_set) in contacts.items():
                if phone_number in phone_number_set:
                    person.name = name

        db.session.add(person)
    
    # make me id 0 - later make this user input, or grab from registration info?
    me = Person(id=0, phone_number="", name='Priyanka Altman') 

    db.session.add(me)

    db.session.commit()

def load_peoplenumbers_table(database):

    print("Populating peoplenumbers table", datetime.now())

    sqliteConnection = sqlite3.connect(database)
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT ROWID, id FROM handle")

    for row in sqliteCursor:
        provided_id = row[0]
        phone_number = row[1]

        # if the id isn't already in the table
        if not PersonNumber.query.get(provided_id):
            person_phone_number = PersonNumber(provided_id=provided_id, phone_number=phone_number)

            db.session.add(person_phone_number)

    db.session.commit()



def load_messages(database):
    """Load messages from sqlite database into psql database."""
    print("Populating messages table", datetime.now())

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate messages
    Message.query.delete()

    sqliteConnection = sqlite3.connect(database)
    sqliteCursor = sqliteConnection.cursor()

    # populate new phone numbers table
    sqliteCursor.execute("SELECT text, handle_id, date, is_from_me FROM message")


    for row in sqliteCursor:
        try:
            text = row[0]
            phone_number_id = row[1]
            date = row[2]
            is_from_me = row[3]
        except IndexError:
            continue
        # if the text was sent FROM me
        if is_from_me == 1:
            message = Message(text=text, 
                              date=date, 
                              sender_id=0, 
                              recipient_id=phone_number_id)
        
        # if the text was sent TO me
        else:
            message = Message(text=text, 
                              date=date, 
                              sender_id=phone_number_id, 
                              recipient_id=0)
        

        db.session.add(message)

    db.session.commit()
    print("Done!", datetime.now())


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data

    load_people_table("phone_backup.db")
    load_peoplenumbers_table("phone_backup.db")

    #load_phone_numbers("phone_backup.db")
    #load_messages("phone_backup.db")


