# guided by: https://jjude.com/pg-to-sqlite/

import sys
import psycopg2
import sqlite3

# create a postgresql db

pgConnection = psycopg2.connect(dbname='pg_phone_backup', user='priyanka', host='localhost', password='abc')
pgCursor = pgConnection.cursor()
# pgCursor.execute('CREATE DATABASE pg_phone_backup')
pgCursor.execute("CREATE TABLE phone_numbers (id SERIAL PRIMARY KEY, \
                                              phone_number VARCHAR(100) NOT NULL, \
                                              fname VARCHAR, \
                                              lname VARCHAR)")

pgCursor.execute("CREATE TABLE messages (id SERIAL PRIMARY KEY, \
                                         text TEXT, \
                                         phone_id INTEGER REFERENCES phone_numbers(id), \
                                         date INTEGER,\
                                         is_from_me INTEGER)") 

# note: is_from_me = 1 if yes, 0 if no

# connect to sqlite
sqliteConnection = sqlite3.connect("phone_backup.db")
sqliteCursor = sqliteConnection.cursor()

# populate new phone numbers table
sqliteCursor.execute("SELECT ROWID, id FROM handle")

rows = sqliteCursor.fetchall()

for row in rows:
    pgCursor.execute("INSERT INTO phone_numbers (id, phone_number) \
                      VALUES (%s, %s)", (row[0], row[1]))

pgConnection.commit()

# populate new messages table
sqliteCursor.execute("SELECT text, handle_id, date_delivered, is_from_me FROM message")

rows = sqliteCursor.fetchall()

for row in rows:

    # unclear why, but some texts have a phone_id of 0, which doesn't match any 
    # number and but each of those texts is not to the same one number, so for 
    # now, ignore them
    if row[1] != 0:
        pgCursor.execute("INSERT INTO messages (text, phone_id, date, is_from_me) \
                          VALUES (%s, %s, %s, %s)", (row[0], row[1], row[2], row[3]))


pgConnection.commit()

# close first sqlite connection
sqliteConnection.close()

# make a new sqlite connection to the contacts database
sqliteConnection = sqlite3.connect("contacts.db")
sqliteCursor = sqliteConnection.cursor()

#add names to phone numbers table:

sqliteCursor.execute("SELECT c0First, c1Last, c16Phone FROM ABPersonFullTextSearch_content")

rows = sqliteCursor.fetchall()

for row in rows:
    # get the phone number in the same format as in the phone numbers table
    # (desired: +12037399406)
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

    pgCursor.execute("SELECT phone_number FROM phone_numbers")

    saved_numbers = pgCursor.fetchall()

    for number in saved_numbers:
        number = number[0]
        if ph_number == number:
            pgCursor.execute("UPDATE phone_numbers SET fname = (%s) \
                              WHERE phone_number = %s", (row[0], ph_number))
            pgCursor.execute("UPDATE phone_numbers SET lname = (%s) \
                              WHERE phone_number = %s", (row[1], ph_number))

pgConnection.commit()




# close all connections
sqliteConnection.close()
pgConnection.close()


# if we parsed through a .txt file of texts instead of querying:

# to parse through message table

# for row in rows:
#     text_all = row.split("(", 1) # limit split by 1
#     text = text_all[1] # take part of row after the open parenthesis
#     text_split = text.split(",") # split up contents by commas
#     row_id = text_split[0] # primary key
#     text_content = text_split[2]
#     handle_id = text_split[5] # handle_id is id of phone number being texted
#     date = text_split[17] # in seconds since 1/1/2001

# # to parse through handle table (starts line 221870)
# for row in rows:
#     handle_all = row.split("(", 1) #limit split by 1
#     info = handle_all[1] # take part of row after the open parenthesis
#     info_split = info.split(",") # split up contents by commas
#     handle_id = info_split[0] # primary key, foreign key in messages table
#     handle_ph_number = info_split[1]
#     handle_type = info_split[3] # SMS or iMessage

