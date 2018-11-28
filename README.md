# Keyboard Diaries

Keyboard Diaries allows users to tap into the insights and treasures stored within their iPhone text history. After uploading their contacts and messages databases from their iPhone or laptop backup, users can:
- search their texts by date or keyword
- learn their most commonly used emoji with each contact
- view graphs comparing their frequency of texting with different contacts
- save texts to folders for easy future reference

### Tech Stack
SQLite, PostgreSQL, Python, Flask, Jinja, JavaScript, HTML5, CSS3, Bootstrap, React

### Setup

Install the dependencies from requirements.txt using pip install:

```sh
pip install -r requirements.txt
```

Run the following command:

```sh
createdb texts
```
Start the server:

```sh
python server.py
```
Register with an email and password - your password is stored as a hash in the database.

Navigate to "Upload My Files" in the upper right of the navbar, and follow the instructions to find your backup database files on your computer. Keyboard Diaries is currently only functional for iPhone texts, and requires an iPhone backup to a computer (not iCloud).

### Features

![alt text](https://github.com/priyankaaltman/Keyboard-Diaries/blob/master/static/Readme_Screenshots/Home.png "Home")
