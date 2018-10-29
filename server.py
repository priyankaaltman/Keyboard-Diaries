"""Texts Analysis"""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session,
                   Markup, jsonify)

from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Person, Message

from datetime import datetime, timedelta

from dateutil.relativedelta import *

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

@app.route('/login')
def login():
    """Log in page."""



@app.route("/contacts")
def show_contacts():
    """Show contact names and phone numbers."""

    contacts = Person.query.order_by(Person.name).all()
    return render_template("contacts.html", contacts=contacts)


def get_sender_by_message_id(message_id):
    """Given a message id, return the name of the person who sent it."""

    sender = Message.query.get(message_id).sender

    return sender

@app.route("/contacts/<int:name_id>")
def get_messages_with_sender_id(name_id):
    """Given the name of a person, return all messages sent and received by that person, in order by date."""

    messages = Message.query.filter((Message.sender_id==name_id) | (Message.recipient_id == name_id)).order_by(Message.date).all()

    return render_template("texts_with_person.html", messages=messages)

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

    return render_template("texts_with_person.html", messages=messages)

@app.route("/graph-frequencies")
def get_message_count_in_date_range(name, interval, date_start, date_end): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""

    name = request.args.get("name")
    interval = request.args.get("interval")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")
    name2 = request.args.get("name2")

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


    data_dict = { 
            "labels": timeblocks,
            "datasets" : [
                {
                    "data": message_counts,
                    "label": name,
                    "fill": False,
                    "borderColor": '#33FDFF',
                    "pointRadius": 6,
                    "pointBackgroundColor": '#33FDFF',
                    "pointBorderColor": '#001516'
            }]
        }


    return render_template("frequency-graph.html", data_dict=data_dict, interval=interval, name=name)

@app.route("/frequency-graph")
def show_frequency_graph():

    return render_template("frequency-graph.html")


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