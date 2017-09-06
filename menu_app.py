from database_setup import Base, Restaurant, MenuItem, User
from flask import Flask, render_template, request, url_for,\
	redirect, jsonify, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random, string, json, requests, httplib2


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) 
        for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


## OAUTH CODE START ##
# Revoke a current user's token and reset their login_session
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
        	json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(
        	json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
        	json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


## LOCAL PERMISSIONS CODE START ##
def createUser(login_session):
    newUser = User(
    	name=login_session['username'], 
    	email=login_session['email'], 
    	picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
    	email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(
    	id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(
        	email=email).one()
        return user.id
    except:
        return None
## LOCAL PERMISSION CODE END ##


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
    	% access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result.status == 200:
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(
        	json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
## OAUTH CODE END ##


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


@app.route('/')
@app.route('/restaurants')
def showRestaurants():
	restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
	if 'username' not in login_session:
		return render_template('publicrestaurants.html',
								restaurants=restaurants)
	else:
		return render_template('restaurants.html', restaurants=restaurants)


# Create new entry on Restaurant table, request form data from 
# newRestaurant.html
@app.route('/restaurants/new', methods=['GET', 'POST'])
def newRestaurant():
	if 'username' not in login_session:
		return redirect('/login')

	if request.method == 'POST':
		newRestaurant = Restaurant(name = request.form['name'],
								user_id = login_session['user_id'])
		session.add(newRestaurant)
		session.commit()
		flash('New Restaurant Created')

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

	if 'username' not in login_session:
		return redirect('/login')

	if editedRestaurant.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
		
	if request.method == 'POST':
		if request.form['name']:
			editedRestaurant.name = request.form['name']
		session.add(editedRestaurant)
		session.commit()
		flash('Restaurant Successfully Edited')

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

	if 'username' not in login_session:
		return redirect('/login')

	if deletedRestaurant.user_id != login_session['user_id']:
		return "<script> function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"

	if request.method =='POST':
		session.delete(deletedRestaurant)
		session.commit()
		flash('Restaurant Successfully Deleted')

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
	restaurant = session.query(Restaurant).filter_by(
		id=restaurant_id).one()
	creator = getUserInfo(restaurant.user_id)
	items = session.query(MenuItem).filter_by(
		restaurant_id=restaurant_id).all()

	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicmenu.html', 
			items=items, 
			restaurant=restaurant, 
			creator=creator)
	else:
		return render_template('menu.html', 
			restaurant=restaurant, 
			items=items)


# Creates new MenuItem entry, pulls form data from newMenuItem.html
@app.route('/restaurants/<int:restaurant_id>/menu/new', 
	methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(
		id=restaurant_id).one()
	if request.method == 'POST':
		newItem = MenuItem(
			name 			= request.form['name'],
			description 	= request.form['desc'],
			price 			= request.form['price'],
			course 			= request.form['course'],
			restaurant_id 	= restaurant_id,
			user_id 		= restaurant.user_id)

		session.add(newItem)
		session.commit()
		flash('Menu Item Created')

		return redirect(url_for('showMenu', 
						restaurant_id=restaurant_id)
		)
	else:
		return render_template('newMenuItem.html', 
								restaurant_id=restaurant_id
		)


# Get the current values for a MenuItem entry, check all form data from 
# 	editMenuItem.html, replace current MenuItem values with those from forms
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', 
	methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedItem = session.query(MenuItem).filter_by(
		restaurant_id=restaurant_id, id=menu_id).one()
	user = session.query(User).filter_by(
		id = login_session['user_id']).one()
	
	if editedItem.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this menu item. Please create your own menu item in order to edit.');}</script><body onload='myFunction()''>"

	if request.method == 'POST':
		if request.form['name']: 
			editedItem.name = request.form['name']
		if request.form['desc']: 
			editedItem.description = request.form['desc']
		if request.form['price']: 
			editedItem.price 	= request.form['price']
		if request.form['course']: 
			editedItem.course = request.form['course']

		session.add(editedItem)
		session.commit()
		flash('Menu Item Successfully Edited')

		return redirect(url_for('showMenu', 
			restaurant_id=restaurant_id))

	else:
		return render_template('editmenuitem.html', 
			restaurant_id=restaurant_id, 
			menu_id=menu_id, 
			item=editedItem)



# Needs both restaurant id and menu item id to select corrent MenuItem entry
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', 
	methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	deletedItem = session.query(MenuItem).filter_by(
		restaurant_id=restaurant_id, id=menu_id).one()

	if 'username' not in login_session:
		return redirect('/login')
	
	if deletedItem.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to delete this menu item. Please create your own menu item in order to delete.');}</script><body onload='myFunction()''>"

	if request.method == 'POST':
		session.delete(deletedItem)
		session.commit()
		flash('Menu Item Successfully Deleted')

		return redirect(url_for('showMenu', restaurant_id=restaurant_id))

	else:
		return render_template(
			'deleteMenuItem.html', 
			restaurant_id=restaurant_id, 
			item=deletedItem)


if __name__ == '__main__':
	app.secret_key = 'super secret key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)