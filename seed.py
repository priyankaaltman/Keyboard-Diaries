"""Seeding database for texts project."""

import sqlite3
from model import Person, PersonNumber, Message
from model import connect_to_db, db 
from collections import defaultdict
import re
from datetime import datetime, timedelta

def make_contacts_dictionary(contacts_database):
    """Load phone numbers from sqlite database into psql database."""

    print("Making Contacts Dictionary", datetime.now())

    sqliteConnection=sqlite3.connect(contacts_database)
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

        
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
        else:
            full_name = f"{first_name}"


        try:
            ph_numbers = row[2] # example: '1 (203) 739-9406 +12037399406 01112037399406 0012037399406 12037399406 2037399406 7399406 '
        except IndexError:
            continue

        pattern = re.compile(r'\+\d\d\d\d\d\d\d\d\d\d\d') # test this, if fails, remove r

        try:
            match = pattern.search(ph_numbers) 
        except TypeError:
            continue

        if match:
            ph_number = match.group()

            if ph_number:
                contacts[full_name].add(ph_number)

    return contacts

def load_people_table(contacts_database, user_id, name):

    print("Populating people table, which has autoincremented ids and names", datetime.now())

    contacts = make_contacts_dictionary(contacts_database)

    for contact in contacts.keys():
        person = Person(user_id=user_id, name=contact)

        db.session.add(person)

    me = Person(user_id=user_id, name=name)

    db.session.add(me)

    db.session.commit()

def load_peoplenumbers_table(contacts_database, texts_database, user_id, name):

    print("Populating peoplenumbers table", datetime.now())

    contacts = make_contacts_dictionary(contacts_database)

    sqliteConnection = sqlite3.connect(texts_database)
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT id FROM handle")

    for row in sqliteCursor:
        phone_number = row[0]

        for (name, phone_number_set) in contacts.items():
            if phone_number in phone_number_set:

                # take name and get the id it has in the people table
                matching_person = Person.query.filter(Person.name==name, Person.user_id==user_id).all() # list of tuples
                matching_person = matching_person[0] # to get the actual person object

                # check if phone number is already in peoplenumbers table
                if not PersonNumber.query.filter(PersonNumber.phone_number==phone_number, PersonNumber.user_id == user_id).all():

                    # make that id the id in the peoplenumbers table
                    personnumber = PersonNumber(user_id=user_id, 
                                                phone_number=phone_number, 
                                                person_id=matching_person.id)

                    db.session.add(personnumber)

    my_person_object_list = Person.query.filter(Person.name==name, Person.user_id==user_id).all()
    my_person_object = my_person_object_list[0]
    me = PersonNumber(user_id=user_id, phone_number='', person_id = my_person_object.id)
    #db.session.add(me)

    db.session.commit()

def load_messages(texts_database, user_id, name):
    """Load messages from sqlite database into psql database."""
    print("Populating messages table", datetime.now())

    sqliteConnection = sqlite3.connect(texts_database)
    sqliteCursor = sqliteConnection.cursor()

    sqliteCursor.execute("SELECT ROWID, id FROM handle")

    # make a dictionary with provided ids as keys and phone numbers as values
    provided_ids = {}

    for row in sqliteCursor:
        provided_ids[row[0]] = row[1]


    # populate new phone numbers table
    sqliteCursor.execute("SELECT text, handle_id, date, is_from_me FROM message")

    count = 0 # for printing purposes
    for row in sqliteCursor:
        if count % 1000 == 0:
            print(count)
        try:
            text = row[0]
            provided_id = row[1]
            date = row[2]
            is_from_me = row[3]
        except IndexError:
            continue

        for prov_id, ph_num in provided_ids.items():
            # if the id from the handle table matches that from the message table
            if prov_id == provided_id:
                # do a query, using the phone number, to look up the corresponding actual ID in the peoplenumbers table
                pers_num_obj_list = PersonNumber.query.filter(PersonNumber.phone_number==ph_num, PersonNumber.user_id==user_id).all()

                if pers_num_obj_list:
                    pers_num_obj = pers_num_obj_list[0]

                    my_person_object_list = Person.query.filter(Person.name==name, Person.user_id==user_id).all()
                    my_person_object = my_person_object_list[0]

                    # if the text was sent FROM me
                    if is_from_me == 1:
                        message = Message(user_id=user_id,
                                          text=text, 
                                          date=date, 
                                          sender_id=my_person_object.id, 
                                          recipient_id=pers_num_obj.person_id)
            
                    # if the text was sent TO me
                    else:
                        message = Message(user_id=user_id,
                                          text=text, 
                                          date=date, 
                                          sender_id=pers_num_obj.person_id, 
                                          recipient_id=my_person_object.id)
        

        db.session.add(message)
        count += 1

    db.session.commit()
    print("Done!", datetime.now())


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()


    # uncomment the following if running seed.py directly instead of calling 
    # functions in server.py:

    # load_people_table("contacts.db")
    # load_peoplenumbers_table("contacts.db", "phone_backup.db")
    # load_messages("phone_backup.db")


