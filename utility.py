"""Utility functions for project."""

from model import connect_to_db, db, Person, Message, Folder

import emoji as e

from datetime import datetime, timedelta

from dateutil.relativedelta import *

def convert_date_to_nanoseconds(date):
    """Given a date in the format MM-DD-YYYY, convert it to nanoseconds since 01-01-2001."""

    jan1_2001 = "01-01-2001"

    jan1_2001 = datetime.strptime(jan1_2001, "%m-%d-%Y")

    date = datetime.strptime(date, "%m-%d-%Y")

    difference = date - jan1_2001

    seconds_difference = (difference.days*24*60*60) + difference.seconds

    nanoseconds_difference = (seconds_difference*1000000000) + (difference.microseconds*1000)

    return nanoseconds_difference

def convert_datetime_to_nanoseconds(datetime_obj):
    """Given a datetime object, convert it to nanoseconds since 01-01-2001."""

    jan1_2001 = datetime.strptime("01-01-2001, 00:00:00.000000", "%m-%d-%Y, %H:%M:%S.%f")

    difference = datetime_obj - jan1_2001

    UTC_time_diff = 7*60*60 # 7 hours converted into seconds

    seconds_difference = (difference.days*24*60*60) + difference.seconds + UTC_time_diff

    nanoseconds_difference = (seconds_difference*1000000000) + (difference.microseconds*1000)

    return nanoseconds_difference

def count_number_received_texts_by_name(name, user_id):
    """Given a person, count how many texts they have sent you."""

    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

    number_received = Message.query.filter(Message.sender_id == person.id, 
                                           Message.user_id==user_id).count()

    return number_received

def count_number_sent_texts_by_name(name, user_id):
    """Given a person, count how many texts you have sent them."""
    
    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

    number_sent = Message.query.filter(Message.recipient_id == person.id, 
                                       Message.user_id==user_id).count()

    return number_sent

def count_words_in_received_texts_with_name(name, user_id):
    """Count how many words are in texts with a person."""

    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

    messages = Message.query.filter(Message.sender_id == person.id, 
                                    Message.user_id==user_id).all()

    num_words = 0
    for message in messages:
        if message.text:
            split_text = message.text.split(" ")
            num_words += len(split_text)

    return num_words

def count_words_in_sent_texts_with_name(name, user_id):
    """Count how many words are in texts with a person."""

    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

    messages = Message.query.filter(Message.recipient_id == person.id, 
                                    Message.user_id==user_id).all()

    num_words = 0
    for message in messages:
        if message.text:
            split_text = message.text.split(" ")
            num_words += len(split_text)

    return num_words

def get_message_count_in_date_range(name, interval, date_start, date_end, user_id): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""

    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

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

            message_count = Message.query.filter((start <= Message.date), 
                                                (Message.date < end),
                                                (Message.user_id == user_id),
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

            message_count = Message.query.filter((start <= Message.date), 
                                                (Message.date < end),
                                                (Message.user_id == user_id),
                                                ((Message.sender_id == person.id) | (Message.recipient_id == person.id))).count()


            message_counts.append(message_count)

    return (timeblocks, message_counts)

def get_your_most_commonly_used_emoji_by_name(name, user_id):
    """Get most commonly used emoji with a person by name."""

    person = Person.query.filter(Person.name==name, 
                                 Person.user_id==user_id).one()

    messages = Message.query.filter((Message.recipient_id == person.id), 
                                    (Message.user_id == user_id)).all()

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


