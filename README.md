# Menu App
A dynamic webapp using Python and Flask to build restaurant menus, with menu 
items pulled from a SQLite database. User is able to add, edit, and delete
database entries.

## Prerequisites
- Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- Install [vagrant](https://www.vagrantup.com/downloads.html)

## Getting Started

- After you've installed VirtualBox and Vagrant, run `vagrant up` from within
the project directory. This may take quite a while (many minutes) depending 
on how fast your Internet connection is.
- When `vagrant up` is finished running, run `vagrant ssh` to log into the
virtual machine
- Run `python database_setup.py` to initialize the database
- Run `python menu_app.py` to start the program
- Open a browser to `localhost:5000/restaurants`

## Authors

* **Riley Brazell** - *Initial work*

## Acknowledgments

* [OAuth code (42-155) from Udacity notes](https://github.com/udacity/ud330/tree/master/Lesson2)
* Udacity Full Stack Developer program, staff, reviewers
* Udacity discussion forums