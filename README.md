# Menu App
This app Uses Flask and SQLAlchemy to build dynamic restaurant menus. Users can log in with Google OAuth 2.0 to add their own restaurants and apps. Tracks and respects user accounts, will not let a user edit or delete an entry that wasn't created by them. Written in Python.

## Prerequisites
Requires [Flask](http://flask.pocoo.org/), [SQLAlchemy](http://www.sqlalchemy.org/) and [oauth2client](https://github.com/google/oauth2client)

## Getting Started

- Clone or download and unzip the project files
- Run `python database_setup.py` to initialize the database
- (optional) Run `python lotsofmenus.py` to fill the database with pre-made data
- Run `python menu_app.py` to start the program
- Open a browser to `localhost:5000/restaurants`
- Login with Google OAuth2.0 to add/edit restaurants and menu items

## Authors

* **Riley Brazell** - *Initial work*

## Acknowledgments

* [OAuth code from Udacity notes](https://github.com/udacity/ud330/tree/master/Lesson2)
* Udacity Full Stack Developer program, staff, reviewers
* Udacity discussion forums
