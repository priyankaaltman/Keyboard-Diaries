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

app = Flask(__name__)
connect_to_db(app)
db.create_all()


# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
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
def register_new_user():
    """Register a new user."""

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    hashed = argon2.hash(password)

    email_users = db.session.query(User.email)
    emails = email_users.filter(User.email == email).all()

    if emails == []:
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

    return render_template(upload.html)

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

    # adding the information of the newly uploaded files to the database:

    # connect_to_db(app)
    # db.create_all()  # In case tables haven't been created, create them

    # these functions are imported from seed.py
    load_people_table(contacts_filename, user_id, name)
    load_peoplenumbers_table(contacts_filename, texts_filename, user_id, name)
    load_messages(texts_filename, user_id, name)

    return redirect("/")

@app.route("/process-login", methods=["POST"])
def log_in_user():
    """Log in an existing user."""

    email = request.form.get("email")
    password = request.form.get("password")

    email_users = db.session.query(User.email)
    saved_email = email_users.filter(User.email == email).first()

    # if the email is not in the database
    if not saved_email:
        message = Markup("This email is not registered. Please register now.")
        flash(message)
        return redirect("/registration")

    # if the email is saved in the database
    else:
        user_obj = User.query.filter(User.email == email).first()
        saved_hash = user_obj.password_hash

        # if the right password was entered
        if argon2.verify(password, saved_hash):
            session["user_id"] = user_obj.id
            message = Markup("You are now logged in.")
            flash(message)
            return redirect("/")
        # if the wrong password was entered
        else:
            message = Markup("Incorrect password. Please try again.")
            flash(message)
            return render_template("login.html")

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

@app.route("/contacts/<int:name_id>")
def display_info_about_contact(name_id):
    """Given the name of a person, return all messages sent and received by that person, in order by date."""

    messages = Message.query.filter(Message.user_id==session["user_id"], 
                                   ((Message.sender_id==name_id) | (Message.recipient_id == name_id))).order_by(Message.date).all()

    person = Person.query.filter((Person.user_id==session["user_id"]), (Person.id == name_id)).one()

    groups = Group.query.filter(Group.user_id == session["user_id"]).all()

    user_id = session["user_id"]

    print("LOOK HERE: ", user_id)

    the_emoji = get_your_most_commonly_used_emoji_by_name(person.name, user_id)

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

@app.route("/daterange", methods=["POST"])
def get_messages_in_date_range(): 
    """Given a specified date range (in format MM-DD-YYYY), return all messages with a certain person during that time frame."""
    name = request.form.get("name")
    date_start = request.form.get("start_date")
    date_end = request.form.get("end_date")

    start = convert_date_to_nanoseconds(date_start)
    end = convert_date_to_nanoseconds(date_end)

    person = Person.query.filter(Person.name==name, 
                                (Person.user_id==session["user_id"]))[0]

    messages = Message.query.filter((Message.user_id==session["user_id"]), 
                                    (start<=Message.date), (Message.date <= end),
                                    ((Message.sender_id == person.id) | (Message.recipient_id == person.id))).order_by(Message.date).all()

    folders = Folder.query.all()

    return render_template("texts_by_date.html", messages=messages, folders=folders)

@app.route("/graph-frequencies")
def display_graph_message_counts():

    name = request.args.get("name")
    interval = request.args.get("interval")
    date_start = request.args.get("start_date")
    date_end = request.args.get("end_date")
    second_name = request.args.get("name2")

    user_id = session["user_id"]

    (timeblocks1, message_counts1) = get_message_count_in_date_range(name, interval, date_start, date_end, user_id)

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
        (timeblocks2, message_counts2) = get_message_count_in_date_range(second_name, interval, date_start, date_end, user_id)

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

@app.route("/keyword")
def find_texts_by_keyword():
    """Given a key word or phrase, return all the texts that contain it."""

    keyword = request.args.get("keyword")

    messages = Message.query.filter((Message.user_id==session["user_id"]), 
                                    (Message.text.like(f"%{keyword}%"))).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("texts_by_keyword.html", messages=messages, folders=folders)

@app.route("/keyword-person")
def find_texts_by_keyword_and_person():
    """Find texts that match on a keyword or phrase with a specific person from their page."""

    keyword = request.args.get("keyword")
    name = request.args.get("person_name")

    person = Person.query.filter((Person.user_id == session["user_id"]),
                                 Person.name == name).one()

    messages = Message.query.filter((Message.user_id==session["user_id"]), 
                                    (Message.text.like(f"%{keyword}%")),
                                    ((Message.sender_id == person.id) | (Message.recipient_id == person.id))).all()

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("texts_by_keyword.html", messages=messages, folders=folders)

@app.route("/folders")
def show_folders():

    folders = Folder.query.filter(Folder.user_id==session["user_id"]).all()

    return render_template("folders.html", folders=folders)

@app.route("/new-folder")
def make_new_folder():
    """Make a new folder into which texts can be saved."""

    folder_name = request.args.get("folder_name")

    new_folder = Folder(user_id=session["user_id"], title=folder_name)

    db.session.add(new_folder)

    db.session.commit()

    return redirect("/folders")

@app.route("/add-message-to-folder")
def add_message_to_folder():
    """Add a chosen message to a chosen folder."""

    message_id = request.args.get("message_id")
    folder_id = request.args.get("folder_id")

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

    return render_template("messages-by-folder.html", messages=messages, folder_title=folder_title)

@app.route("/new-group")
def make_new_group():

    group_name = request.args.get("group_name")

    new_group = Group(user_id=session["user_id"], title=group_name)

    db.session.add(new_group)

    db.session.commit()

    return redirect("/contacts")

@app.route("/add-person-to-group")
def add_person_to_group():
    
    group_id = request.args.get("group_id")
    name = request.args.get("person_name")

    print("NAME: ", name)

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