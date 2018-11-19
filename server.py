"""Texts Analysis"""

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash, session,
                   Markup, jsonify)
from werkzeug import secure_filename
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, Person, Message, Folder, User, Group
from utility import *
from seed import *
from passlib.hash import argon2
from datetime import date
from dateutil.relativedelta import *

app = Flask(__name__)
connect_to_db(app)
db.create_all()

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/index')
def index():

    return render_template("index.html")


@app.route('/')
def home():
    """Homepage."""

    if "user_id" in session.keys():
        user = User.query.filter(User.id == session["user_id"]).first()
        if user:
            name = user.name
        else:
            name = "None"
        return render_template("homepage.html", name=name)
    else:
        message = Markup("Please log in to view your homepage.")
        flash(message)
        return render_template("login.html")


@app.route("/registration")
def show_registration_page():
    """Show registration page."""

    return render_template("registration.html")


@app.route("/login")
def show_login_page():
    """Show login page."""

    return render_template("login.html")


@app.route("/process-registration", methods=["POST"])
def process_registration():
    """Register a new user."""

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    hashed = argon2.hash(password)

    email_users = db.session.query(User.email)
    emails = email_users.filter(User.email == email).all()

    if not emails:
        user = User(name=name, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        session["name"] = user.name
        message = Markup("You are now registered.")
        flash(message)
        return render_template("upload.html")

    else:
        message = Markup("There is already an account associated with this email address.")
        flash(message)
        return render_template("login.html")


@app.route('/upload')
def show_upload_page():

    return render_template("upload.html")


@app.route('/process-upload', methods=['POST'])
def upload_file():
    contacts = request.files['contacts']
    texts = request.files['texts']

    contacts_filename = secure_filename(contacts.filename)
    texts_filename = secure_filename(texts.filename)

    contacts.save(contacts_filename)
    texts.save(texts_filename)

    user_id = session["user_id"]
    name = session["name"]

    # adding the information of the newly uploaded files to the databases:

    # these functions are imported from seed.py
    load_people_table(contacts_filename, user_id, name)
    load_peoplenumbers_table(contacts_filename, texts_filename, user_id, name)
    load_messages(texts_filename, user_id, name)

    return redirect("/")


@app.route("/process-login")
def log_in_user():
    """Log in an existing user."""

    email = request.args.get("email")
    password = request.args.get("password")

    email_users = db.session.query(User.email)
    saved_email = email_users.filter(User.email == email).first()

    # if email is not in the database
    if not saved_email:
        message = Markup("Invalid credentials.")
        flash(message)        
        return redirect("/login")

    # if the email is saved in the database
    else:
        user_obj = User.query.filter(User.email == email).first()
        saved_hash = user_obj.password_hash

        # if the right password was entered
        if argon2.verify(password, saved_hash):
            session["user_id"] = user_obj.id
            session["name"] = user_obj.name
            message = Markup("You are now logged in.")
            flash(message)
            return redirect("/")
        # if the wrong password was entered
        else:
            message = Markup("Invalid credentials.")
            flash(message)
            return redirect("/login")


@app.route("/logout")
def show_logout_page():
    """Bring a currently logged in user to the logout page."""

    return render_template("logout.html")


@app.route("/process-logout")
def log_out_user():
    """Log out a user."""

    session.clear()
    message = Markup("You have been successfully logged out.")
    flash(message)

    return render_template("login.html")


@app.route("/contacts")
def show_contacts():
    """Show contact names and phone numbers."""

    groups = Group.query.filter(Group.user_id == session["user_id"]).all()

    contacts = Person.query.filter(Person.user_id==session["user_id"]).order_by(Person.name).all()

    return render_template("contacts.html", contacts=contacts, groups=groups)


@app.route("/api/contacts")
def api_show_contacts():
    """Show contact names and phone numbers."""

    contacts = Person.query.filter(Person.user_id==session["user_id"]).order_by(Person.name).all()

    json_contacts = []
    for contact in contacts:
        contact_attributes = {
            'id': contact.id,
            'name': contact.name,
            'user_id': contact.user_id
        }

        json_contacts.append(contact_attributes)

    return jsonify({'contacts': json_contacts})


@app.route("/api/groups")
def api_show_groups():

    groups = Group.query.filter(Group.user_id == session["user_id"]).all()

    json_groups = []
    for group in groups:
        group_attributes = {
            'id': group.id,
            'title': group.title,
            'user_id': group.user_id
        }

        json_groups.append(group_attributes)

    return jsonify({'groups': json_groups})


@app.route("/contacts/<int:name_id>")
def display_info_about_contact(name_id):
    """Given the name of a person, return all messages sent and received by that person, in order by date."""

    to_or_from_contact = (Message.sender_id==name_id) | (Message.recipient_id == name_id)

    messages = Message.query.filter(Message.user_id==session["user_id"], 
                                   to_or_from_contact).order_by(Message.date).all()

    person = Person.query.filter((Person.user_id==session["user_id"]), (Person.id == name_id)).one()

    groups = Group.query.filter(Group.user_id == session["user_id"]).all()

    user_id = session["user_id"]

    the_emoji = get_most_loved_emoji(person.name, user_id)

    number_sent = count_number_sent_texts_by_name(person.name, user_id)

    number_received = count_number_received_texts_by_name(person.name, user_id)

    words_sent = count_words_in_sent_texts_with_name(person.name, user_id)

    words_received = count_words_in_received_texts_with_name(person.name, user_id)

    return render_template("texts_with_person.html", messages=messages, 
                                                     name=person.name, 
                                                     the_emoji=the_emoji, 
                                                     number_sent=number_sent, 
                                                     number_received=number_received,
                                                     words_sent=words_sent,
                                                     words_received=words_received,
                                                     groups=groups)

@app.route("/api/contacts/<int:name_id>")
def api_display_info_about_contact(name_id):
    """Given the name of a person, return all messages sent and received by that person, in order by date."""

    to_or_from_contact = (Message.sender_id == name_id) | (Message.recipient_id == name_id)

    messages = Message.query.filter(Message.user_id==session["user_id"], 
                                   to_or_from_contact).order_by(Message.date).all()

    person = Person.query.filter((Person.user_id==session["user_id"]), (Person.id == name_id)).one()
    groups = Group.query.filter(Group.user_id == session["user_id"]).all()
    user_id = session["user_id"]
    the_emoji = get_most_loved_emoji(person.name, user_id)
    number_sent = count_number_sent_texts_by_name(person.name, user_id)
    number_received = count_number_received_texts_by_name(person.name, user_id)
    words_sent = count_words_in_sent_texts_with_name(person.name, user_id)
    words_received = count_words_in_received_texts_with_name(person.name, user_id)

    groups_in = person.groups

    group_titles = []
    for group in person.groups:
        group_titles.append(group.title)

    json_contact_info = [
        {
            'name': person.name,
            'most_loved_emoji': the_emoji,
            'number_sent': number_sent,
            'number_received': number_received,
            'words_sent': words_sent,
            'words_received': words_received,
            'groups': group_titles
        }
    ]

    return jsonify({"contact_info": json_contact_info})

@app.route("/api/general-search")
def api_general_search(): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""
    
    form_data = request.args

    print("\n\n\n\n\n\nLOOK HERE: ", form_data)

    if start_date and end_date and keyword:
        start_date = form_data["start_date"]
        end_date = form_data["end_date"]
        keyword = form_data["keyword"]

        start = convert_date_to_nanoseconds(start_date)
        end = convert_date_to_nanoseconds(end_date)

        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        start<=Message.date, 
                                        Message.date <= end,
                                        Message.text.like(f"%{keyword}%")).order_by(Message.date).all()

    elif not form_data['start_date'] or not form_data['end_date'] and form_data['keyword']:
        keyword = form_data["keyword"]
        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        Message.text.like(f"%{keyword}%")).order_by(Message.date).all()

    elif form_data['start_date'] and form_data['end_date'] and not form_data['keyword']:
        start_date = form_data["start_date"]
        end_date = form_data["end_date"]

        start = convert_date_to_nanoseconds(start_date)
        end = convert_date_to_nanoseconds(end_date)

        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        start<=Message.date, 
                                        Message.date <= end).order_by(Message.date).all()

    json_messages = []
    for message in messages:
        message_attributes = {
            'id': message.id,
            'user_id': message.user_id,
            'text': message.text,
            'date': message.date,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id
        }

        json_messages.append(message_attributes)

    return jsonify({"messages": json_messages})


@app.route("/daterange")
def get_messages_in_date_range(): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""
    name = request.args.get("name")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")

    start = convert_date_to_nanoseconds(date_start)
    end = convert_date_to_nanoseconds(date_end)

    person = Person.query.filter(Person.name==name, 
                                (Person.user_id==session["user_id"]))[0]

    to_or_from_contact = (Message.sender_id==person.id) | (Message.recipient_id == person.id)

    messages = Message.query.filter(Message.user_id==session["user_id"], 
                                    start<=Message.date, 
                                    Message.date <= end,
                                    to_or_from_contact).order_by(Message.date).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("texts_by_date.html", messages=messages, folders=folders)


@app.route('/api/daterange')
def api_get_messages_in_date_range(): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""
    name = request.args.get("name")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")

    start = convert_date_to_nanoseconds(date_start)
    end = convert_date_to_nanoseconds(date_end)

    person = Person.query.filter(Person.name==name, 
                                (Person.user_id==session["user_id"]))[0]

    to_or_from_contact = (Message.sender_id==person.id) | (Message.recipient_id == person.id)

    messages = Message.query.filter(Message.user_id==session["user_id"], 
                                    start<=Message.date, 
                                    Message.date <= end,
                                    to_or_from_contact).order_by(Message.date).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    json_messages = []
    for message in messages:
        message_attributes = {
            'id': message.id,
            'user_id': message.user_id,
            'text': message.text,
            'date': message.date,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id
        }

        json_messages.append(message_attributes)

    json_folders = []
    for folder in folders:
        folder_attributes = {
            'id': folder.id,
            'title': folder.title,
            'user_id': folder.user_id
        }

        json_folders.append(folder_attributes)

    return jsonify({'messages': json_messages, 'folders': json_folders})


@app.route("/graph-frequencies")
def display_graph_message_counts():

    name = request.args.get("name")
    interval = request.args.get("interval")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")
    second_name = request.args.get("name2")

    user_id = session["user_id"]

    data_dict = {"datasets" : [{
        "fill": False,
        "pointRadius": 6,
        "pointBorderColor": '#001516',
    }, {
        "fill": False,
        "pointRadius": 6,
        "pointBorderColor": '#001516',
    }]}

    (timeblocks1, message_counts1) = get_message_count_in_date_range(name, interval, date_start, date_end, user_id)

    data_dict["labels"] = timeblocks1
    lines_list = data_dict["datasets"]
    lines_list[0]["data"] = message_counts1
    lines_list[0]["label"] = name
    lines_list[0]["borderColor"] = "#33FDFF"
    lines_list[0]["pointBackgroundColor"] = "#33FDFF"

    if not second_name:
        lines_list.pop() # remove the settings for the second line if there isn't one
    else:
        (timeblocks2, message_counts2) = get_message_count_in_date_range(second_name, interval, date_start, date_end, user_id)
        lines_list[1]["data"] = message_counts2
        lines_list[1]["label"] = second_name
        lines_list[1]["borderColor"] = "#D51414"
        lines_list[1]["pointBackgroundColor"] = "#D51414"

    return render_template("frequency-graph.html", data_dict=data_dict, interval=interval)

@app.route("/api/graph-frequencies")
def api_display_graph_message_counts():

    name = request.args.get("name")
    interval = request.args.get("interval")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")
    second_name = request.args.get("name2")

    user_id = session["user_id"]

    data_dict = {"datasets" : [
        {
            "fill": False,
            "pointRadius": 6,
            "pointBorderColor": '#001516',
        },
        {
            "fill": False,
            "pointRadius": 6,
            "pointBorderColor": '#001516',
    }]}

    (timeblocks1, message_counts1) = get_message_count_in_date_range(name, interval, date_start, date_end, user_id)

    data_dict["labels"] = timeblocks1
    first_line = data_dict["datasets"][0]
    lines_list = data_dict["datasets"]
    first_line["data"] = message_counts1
    first_line["label"] = name
    first_line["borderColor"] = "#33FDFF"
    first_line["pointBackgroundColor"] = "#33FDFF"

    if not second_name:
        lines_list.pop() # remove the settings for the second line if there isn't one
    else:
        (timeblocks2, message_counts2) = get_message_count_in_date_range(second_name, interval, date_start, date_end, user_id)
        lines_list[1]["data"] = message_counts2
        lines_list[1]["label"] = second_name
        lines_list[1]["borderColor"] = "#D51414"
        lines_list[1]["pointBackgroundColor"] = "#D51414"

    return jsonify(data_dict)


@app.route("/keyword")
def find_texts_by_keyword():
    """Find texts that match on a keyword or phrase with a specific person from their page."""

    form_data = request.args.to_dict()
    keyword = form_data["keyword"]

    if "person_name" in form_data.keys():
        name = form_data["person_name"]

        person = Person.query.filter(Person.user_id == session["user_id"],
                                     Person.name == name).one()

        to_or_from_contact = (Message.sender_id == person.id) | (Message.recipient_id == person.id)

        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        Message.text.like(f"%{keyword}%"),
                                        to_or_from_contact).all()

    else:
        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        Message.text.like(f"%{keyword}%")).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("texts_by_keyword.html", messages=messages, folders=folders)

@app.route("/api/keyword")
def api_find_texts_by_keyword():
    """Find texts that match on a keyword or phrase with a specific person from their page."""

    form_data = request.args.to_dict()
    
    keyword = form_data["keyword"]

    if "person_name" in form_data.keys():
        name = form_data["person_name"]

        person = Person.query.filter(Person.user_id == session["user_id"],
                                     Person.name == name).one()

        to_or_from_contact = (Message.sender_id == person.id) | (Message.recipient_id == person.id)

        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        Message.text.like(f"%{keyword}%"),
                                        to_or_from_contact).all()

    else:
        messages = Message.query.filter(Message.user_id==session["user_id"], 
                                        Message.text.like(f"%{keyword}%")).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    json_messages = []
    for message in messages:
        message_attributes = {
            'id': message.id,
            'user_id': message.user_id,
            'text': message.text,
            'date': message.date,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id
        }

        json_messages.append(message_attributes)

    json_folders = []
    for folder in folders:
        folder_attributes = {
            'id': folder.id,
            'title': folder.title,
            'user_id': folder.user_id
        }

        json_folders.append(folder_attributes)


    return jsonify({'messages': json_messages, 'folders': json_folders})

@app.route("/folders")
def show_folders():

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("folders.html", folders=folders)

@app.route("/api/folders")
def api_show_folders():

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    json_folders = []
    for folder in folders:
        folder_attributes = {
            'id': folder.id,
            'title': folder.title,
            'user_id': folder.user_id
        }

        json_folders.append(folder_attributes)


    return jsonify({'folders': json_folders})

@app.route("/new-folder", methods=["POST"])
def make_new_folder():
    """Make a new folder into which texts can be saved."""

    folder_name = request.form.get("folder_name")

    new_folder = Folder(user_id=session["user_id"], title=folder_name)

    db.session.add(new_folder)

    db.session.commit()

    return redirect("/folders")

@app.route("/add-message-to-folder", methods=["POST"])
def add_message_to_folder():
    """Add a chosen message to a chosen folder."""

    message_id = request.form.get("message_id")
    folder_id = request.form.get("folder_id")

    folder = Folder.query.filter(Folder.id==folder_id, Folder.user_id == session["user_id"]).one()
    message = Message.query.filter(Message.id==message_id, Message.user_id == session["user_id"]).one()

    folder.messages.append(message)

    db.session.add(folder)

    db.session.commit()

    return redirect(f"/folders/{folder_id}")

@app.route("/folders/<int:folder_id>")
def show_messages_in_folder(folder_id):

    folder = Folder.query.filter(Folder.id==folder_id, Folder.user_id == session["user_id"]).one()

    folder_title = folder.title

    messages = folder.messages # list of messages in that folder

    me = Person.query.filter(Person.user_id == session["user_id"], Person.name == session["name"]).one()
    print(me)

    return render_template("messages-by-folder.html", messages=messages, folder_title=folder_title, me=me)

@app.route("/api/folders/<int:folder_id>")
def api_show_messages_in_folder(folder_id):

    folder = Folder.query.filter(Folder.id==folder_id, Folder.user_id == session["user_id"]).one()

    folder_title = folder.title

    messages = folder.messages # list of messages in that folder

    json_messages = []
    for message in messages:
        message_attributes = {
            'id': message.id,
            'user_id': message.user_id,
            'text': message.text,
            'date': message.date,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id
        }

        json_messages.append(message_attributes)


    return jsonify({'messages': json_messages})

@app.route("/new-group", methods=["POST"])
def make_new_group():

    group_name = request.form.get("group_name")

    new_group = Group(user_id=session["user_id"], title=group_name)

    db.session.add(new_group)

    db.session.commit()

    return redirect("/contacts")

@app.route("/add-person-to-group", methods=["POST"])
def add_person_to_group():
    
    group_id = request.form.get("group_id")
    name = request.form.get("person_name")

    person = Person.query.filter(Person.name == name, Person.user_id == session["user_id"]).one()
    group = Group.query.filter(Group.id==group_id, Group.user_id == session["user_id"]).one()

    group.members.append(person)

    db.session.add(group)

    db.session.commit()

    return redirect(f"/contacts/group/{group_id}")

@app.route("/contacts/group/<int:group_id>")
def show_people_in_group(group_id):

    group = Group.query.filter(Group.id==group_id, Group.user_id == session["user_id"]).one()

    group_title = group.title

    members = group.members # list of people in that group

    return render_template("people-by-group.html", members=members, group_title=group_title)

@app.route("/api/contacts/group/<int:group_id>")
def api_show_people_in_group(group_id):

    group = Group.query.filter(Group.id==group_id, Group.user_id == session["user_id"]).one()

    group_title = group.title

    members = group.members # list of people in that group

    json_members = []
    for member in members:
        member_attributes = {
            'id': member.id,
            'name': member.name,
            'user_id': member.user_id
        }

        json_members.append(member_attributes)

    return jsonify({"group_name": group.title, "members": json_members})

@app.route("/one-year-ago-today")
def show_messages_on_this_day():

    today = date.today() # datetime.date(2018, 11, 6)

    year_ago = today - relativedelta(years=+1) #datetime.date(2017, 11, 6)

    # need to get 0:00 of one_year_ago in nanoseconds
    year_ago_start = datetime(year=year_ago.year, 
                              month=year_ago.month, 
                              day=year_ago.day, 
                              hour=0, 
                              minute=0, 
                              second=0, 
                              microsecond=0)


    # need to get 0:00 of one_year_ago + one day in nanoseconds
    year_ago_next_day = year_ago + relativedelta(days=+1)

    year_ago_end = datetime(year=year_ago_next_day.year, 
                            month=year_ago_next_day.month, 
                            day=year_ago_next_day.day, 
                            hour=0, 
                            minute=0, 
                            second=0, 
                            microsecond=0)

    start = convert_datetime_to_nanoseconds(year_ago_start)
    end = convert_datetime_to_nanoseconds(year_ago_end)

    # then do query to find texts between those two nanoseconds
    messages = Message.query.filter((Message.user_id==session["user_id"]), 
                                    (start<=Message.date), (Message.date < end)).order_by(Message.date).all()

    me = Person.query.filter(Person.user_id == session["user_id"], Person.name == session["name"]).one()

    return render_template("one-year-ago-today.html", messages=messages, me=me)

@app.route("/api/one-year-ago-today")
def api_show_messages_on_this_day():

    today = date.today() # datetime.date(2018, 11, 6)

    year_ago = today - relativedelta(years=+1) #datetime.date(2017, 11, 6)

    # need to get 0:00 of one_year_ago in nanoseconds
    year_ago_start = datetime(year=year_ago.year, 
                              month=year_ago.month, 
                              day=year_ago.day, 
                              hour=0, 
                              minute=0, 
                              second=0, 
                              microsecond=0)


    # need to get 0:00 of one_year_ago + one day in nanoseconds
    year_ago_next_day = year_ago + relativedelta(days=+1)

    year_ago_end = datetime(year=year_ago_next_day.year, 
                            month=year_ago_next_day.month, 
                            day=year_ago_next_day.day, 
                            hour=0, 
                            minute=0, 
                            second=0, 
                            microsecond=0)

    start = convert_datetime_to_nanoseconds(year_ago_start)
    end = convert_datetime_to_nanoseconds(year_ago_end)

    # then do query to find texts between those two nanoseconds
    messages = Message.query.filter((Message.user_id==session["user_id"]), 
                                    (start<=Message.date), (Message.date < end)).order_by(Message.date).all()

    me = Person.query.filter(Person.name == session["name"]).one()

    friends = set()
    for message in messages:
        if message.sender not in friends and message.sender != me:
            friends.add(message.sender)
        elif message.recipient not in friends and message.recipient != me:
            friends.add(message.recipient)

    json_messages = []
    for message in messages:
        message_attributes = {
            'id': message.id,
            'user_id': message.user_id,
            'text': message.text,
            'date': message.date,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id
        }

        json_messages.append(message_attributes)

    json_friends = []
    for friend in friends:
        friend_attributes = {
            'id': friend.id,
            'name': friend.name,
            'user_id': friend.user_id
        }

        json_friends.append(friend_attributes)

    return jsonify({'messages': json_messages, 'friends': json_friends})

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