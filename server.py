"""Texts Analysis"""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session,
                   Markup, jsonify)

from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Person, Message, Folder

from datetime import datetime, timedelta

from dateutil.relativedelta import *

import emoji as e

from seed import *


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/contacts")
def show_contacts():
    """Show contact names and phone numbers."""

    contacts = Person.query.order_by(Person.name).all()
    return render_template("contacts.html", contacts=contacts)


@app.route("/contacts/<int:name_id>")
def display_info_about_contact(name_id):
    """Given the name of a person, return all messages sent and received by that person, in order by date."""

    messages = Message.query.filter((Message.sender_id==name_id) | (Message.recipient_id == name_id)).order_by(Message.date).all()

    person = Person.query.filter(Person.id == name_id).one()

    the_emoji = get_your_most_commonly_used_emoji_by_name(person.name)

    number_sent = count_number_sent_texts_by_name(person.name)

    number_received = count_number_received_texts_by_name(person.name)

    words_sent = count_words_in_sent_texts_with_name(person.name)

    words_received = count_words_in_received_texts_with_name(person.name)

    return render_template("texts_with_person.html", messages=messages, 
                                                     name=person.name, 
                                                     the_emoji=the_emoji, 
                                                     number_sent=number_sent, 
                                                     number_received=number_received,
                                                     words_sent=words_sent,
                                                     words_received=words_received)

def convert_date_to_nanoseconds(date):
    """Given a date in the format MM-DD-YYYY, convert it to nanoseconds since 01-01-2001."""

    jan1_2001 = "01-01-2001"

    jan1_2001 = datetime.strptime(jan1_2001, "%m-%d-%Y")

    date = datetime.strptime(date, "%m-%d-%Y")

    difference = date - jan1_2001

    seconds_difference = (difference.days*24*60*60) + difference.seconds

    nanoseconds_difference = (seconds_difference*1000000000) + (difference.microseconds*1000)

    return nanoseconds_difference

@app.route("/daterange", methods=["POST"])
def get_messages_in_date_range(): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""
    name = request.form.get("name")
    date_start = request.form.get("start_date")
    date_end = request.form.get("end_date")

    start = convert_date_to_nanoseconds(date_start)
    end = convert_date_to_nanoseconds(date_end)

    person = Person.query.filter_by(name=name)[0]

    messages = Message.query.filter((start<=Message.date), (Message.date <= end),((Message.sender_id == person.id) | (Message.recipient_id == person.id))).order_by(Message.date).all()

    return render_template("texts_by_date.html", messages=messages)

@app.route("/graph-frequencies")
def display_graph_message_counts():

    name = request.args.get("name")
    interval = request.args.get("interval")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")
    second_name = request.args.get("name2")

    (timeblocks1, message_counts1) = get_message_count_in_date_range(name, interval, date_start, date_end)

    if not second_name:
         data_dict = { 
            "labels": timeblocks1,
             "datasets" : [
             {
                "data": message_counts1,
                "label": name,
                "fill": False,
                "borderColor": '#33FDFF',
                "pointRadius": 6,
                "pointBackgroundColor": '#33FDFF',
                "pointBorderColor": '#001516'}
            ]
        }

    else:
        (timeblocks2, message_counts2) = get_message_count_in_date_range(second_name, interval, date_start, date_end)

        data_dict = { 
            "labels": timeblocks1,
             "datasets" : [
             {
                "data": message_counts1,
                "label": name,
                "fill": False,
                "borderColor": '#33FDFF',
                "pointRadius": 6,
                "pointBackgroundColor": '#33FDFF',
                "pointBorderColor": '#001516'},
            {
                "data": message_counts2,
                "label": second_name,
                "fill": False,
                "borderColor": '#D51414',
                "pointRadius": 6,
                "pointBackgroundColor": '#D51414',
                "pointBorderColor": '#001516'}
            ]
        }

    return render_template("frequency-graph.html", data_dict=data_dict, interval=interval)

def get_message_count_in_date_range(name, interval, date_start, date_end): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""

    person = Person.query.filter_by(name=name).one()

    if interval == "Year":
        temp_start = int(date_start)
        timeblocks = []

        while temp_start < int(date_end):
            timeblocks.append(temp_start)
            temp_start += 1

        message_counts = []
        for year in timeblocks:
            full_start_date = f"01-01-{year}"
            full_end_date = f"01-01-{year+1}"

            start = convert_date_to_nanoseconds(full_start_date)
            end = convert_date_to_nanoseconds(full_end_date)

            message_count = Message.query.filter((start <= Message.date), (Message.date < end),
                                                 ((Message.sender_id == person.id) | (Message.recipient_id == person.id))).count()


            message_counts.append(message_count)

    if interval == "Month":
        timeblocks = []
        temp_start = datetime.strptime(date_start, "%m-%Y")
        temp_end = datetime.strptime(date_end, "%m-%Y")
        while temp_start < temp_end:
            formatted_temp_start = temp_start.strftime("%B %Y")
            timeblocks.append(formatted_temp_start)
            temp_start += relativedelta(months=+1)

        message_counts = []
        for month in timeblocks:
            month_as_dt_obj = datetime.strptime(month, "%B %Y")
            formatted_start_date = month_as_dt_obj.strftime("%m-%d-%Y")
            new_temp_end = month_as_dt_obj + relativedelta(months=+1)
            formatted_temp_end = new_temp_end.strftime("%m-%d-%Y")

            start = convert_date_to_nanoseconds(formatted_start_date)
            end = convert_date_to_nanoseconds(formatted_temp_end)

            message_count = Message.query.filter((start <= Message.date), (Message.date < end),
                                                 ((Message.sender_id == person.id) | (Message.recipient_id == person.id))).count()


            message_counts.append(message_count)

    return (timeblocks, message_counts)

def get_your_most_commonly_used_emoji_by_name(name):
    """Get most commonly used emoji with a person by name."""

    person = Person.query.filter_by(name=name).one()

    messages = Message.query.filter(Message.recipient_id == person.id).all()

    emoji_dict = {}
    for message in messages:
        for character in message.text:
            if character in e.UNICODE_EMOJI:
                emoji_dict[character] = emoji_dict.get(character, 0) + 1

    saved_count = 0
    saved_emoji = ''
    for (emoji, count) in emoji_dict.items():
        if count > saved_count:
            saved_count = count
            saved_emoji = emoji

    return saved_emoji

@app.route("/keyword")
def find_texts_by_keyword():
    """Given a key word or phrase, return all the texts that contain it."""

    keyword = request.args.get("keyword")

    messages = Message.query.filter(Message.text.like(f"%{keyword}%")).all()

    return render_template("texts_by_keyword.html", messages=messages)

def count_words_in_sent_texts_with_name(name):
    """Count how many words are in texts with a person."""

    person = Person.query.filter_by(name=name).one()

    messages = Message.query.filter(Message.recipient_id == person.id).all()

    num_words = 0
    for message in messages:
        if message.text:
            split_text = message.text.split(" ")
            num_words += len(split_text)

    return num_words

def count_words_in_received_texts_with_name(name):
    """Count how many words are in texts with a person."""

    person = Person.query.filter_by(name=name).one()

    messages = Message.query.filter(Message.sender_id == person.id).all()

    num_words = 0
    for message in messages:
        if message.text:
            split_text = message.text.split(" ")
            num_words += len(split_text)

    return num_words

def count_number_received_texts_by_name(name):
    """Given a person, count how many texts they have sent you."""

    person = Person.query.filter_by(name=name).one()

    number_received = Message.query.filter(Message.sender_id == person.id).count()

    return number_received

def count_number_sent_texts_by_name(name):
    """Given a person, count how many texts you have sent them."""
    
    person = Person.query.filter_by(name=name).one()

    number_sent = Message.query.filter(Message.recipient_id == person.id).count()

    return number_sent


@app.route("/folders")
def show_folders():

    folders = Folder.query.all()

    return render_template("folders.html", folders=folders)


@app.route("/new-folder")
def make_new_folder():
    """Make a new folder into which texts can be saved."""

    folder_name = request.args.get("folder_name")

    new_folder = Folder(title=folder_name)

    db.session.add(new_folder)

    db.session.commit()

    return redirect("/folders")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=8000, host='0.0.0.0')