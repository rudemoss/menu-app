from flask import Flask, render_template, request, url_for, redirect, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

# Connect to sql database and create session object
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/restaurants')
def showRestaurants():
	restaurants = session.query(Restaurant).all()
	return render_template('restaurants.html', restaurants=restaurants)


# serialize function returns all values inside MenuItem or 
# Restaurant entry, one by one. jsonify function returns this as a JSON object
@app.route('/restaurants/JSON')
def showRestaurantsJSON():
	restaurant = session.query(Restaurant).all()
	return jsonify(restaurants = [r.serialize for r in restaurant])


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def showMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(
		restaurant_id=restaurant.id).all()

	return jsonify(MenuItems = [i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
	menuItem = session.query(MenuItem).filter_by(id=menu_id).one()

	return jsonify(MenuItem = menuItem.serialize)


# Create new entry on Restaurant table, request form data from 
# newRestaurant.html
@app.route('/restaurants/new', methods=['GET', 'POST'])
def newRestaurant():
	if request.method == 'POST':
		newRestaurant = Restaurant(name = request.form['name'])
		session.add(newRestaurant)
		session.commit()

		return redirect(url_for('showRestaurants'))

	else:
		return render_template('newRestaurant.html')


# Get current attributes for selected restaurant, get form data from 
# editRestaurant.html, overwrite old name values
@app.route('/restaurants/<int:restaurant_id>/edit', 
	methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
	editedRestaurant = session.query(Restaurant).filter_by(
		id=restaurant_id).one()

	if request.method == 'POST':
		if request.form['name']:
			editedRestaurant.name = request.form['name']
		session.add(editedRestaurant)
		session.commit()

		return redirect(url_for('showRestaurants'))
	else:
		return render_template(
			'editRestaurant.html', 
			restaurant_id=restaurant_id, 
			r=editedRestaurant)


# Get id of selected restaurant entry to delete from Restaurants table
@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	deletedRestaurant = session.query(Restaurant).filter_by(
		id=restaurant_id).one()

	if request.method =='POST':
		session.delete(deletedRestaurant)
		session.commit()

		return redirect(url_for('showRestaurants'))
	else:
		return render_template(
			'deleteRestaurant.html', 
			restaurant_id=restaurant_id, 
			r=deletedRestaurant)


# Query Restaurant and MenuItem tables, the MenuItem table needs an integer
# for the restaurant id and another for the item's id
@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
	return render_template('menu.html', restaurant=restaurant, items=items)


# Creates new MenuItem entry, pulls form data from newMenuItem.html
@app.route('/restaurants/<int:restaurant_id>/menu/new', 
	methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItem(
			name 			= request.form['name'],
			description 	= request.form['desc'],
			price 			= request.form['price'],
			course 			= request.form['course'],
			restaurant_id 	= restaurant_id)

		session.add(newItem)
		session.commit()

		return redirect(url_for('showMenu', restaurant_id=restaurant_id))
	else:
		return render_template(
			'newMenuItem.html', restaurant_id=restaurant_id)


# Get the current values for a MenuItem entry, check all form data from 
# 	editMenuItem.html, replace current MenuItem values with those from forms
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', 
	methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	editedItem = session.query(MenuItem).filter_by(
		restaurant_id=restaurant_id, id=menu_id).one()

	if request.method == 'POST':
		if request.form['name']: editedItem.name = request.form['name']
		if request.form['desc']: editedItem.description = request.form['desc']
		if request.form['price']: editedItem.price 	= request.form['price']
		if request.form['course']: editedItem.course = request.form['course']

		session.add(editedItem)
		session.commit()

		return redirect(url_for('showMenu', restaurant_id=restaurant_id))

	else:
		return render_template(
			'editMenuItem.html', restaurant_id=restaurant_id, item=editedItem)


# Needs both restaurant id and menu item id to select corrent MenuItem entry
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', 
	methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	deletedItem = session.query(MenuItem).filter_by(
		restaurant_id=restaurant_id, id=menu_id).one()

	if request.method == 'POST':
		session.delete(deletedItem)
		session.commit()

		return redirect(url_for('showMenu', restaurant_id=restaurant_id))

	else:
		return render_template(
			'deleteMenuItem.html', 
			restaurant_id=restaurant_id, 
			item=deletedItem)


if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)