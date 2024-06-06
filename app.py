import base64
from datetime import datetime

import bson
import gridfs
import os
from bson.objectid import ObjectId
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
app.secret_key = "mysecretkey"
app.config['MONGO_DBNAME'] = 'loginex'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/loginex'
app.config['UPLOAD_FOLDER'] = 'static/img/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

mongo = PyMongo(app)

users = mongo.db.users
Cafes = mongo.db.manager
menu = mongo.db.menu
orders = mongo.db.orders

logging.basicConfig(level=logging.ERROR)

gender = ['Male', 'Female', 'Other']
fs = gridfs.GridFS(mongo.db)
ENTRIES_PER_PAGE = 10


# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def is_allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# @app.before_request
# def before_request():
#     if 'cart' not in session:
#         session['cart'] = []
#

#
#
# @app.errorhandler(413)
# def too_large(e):
#     return flash("File is too large", "413")


@app.route("/")
def index():
    return render_template("homepage.html")


@app.route("/about")
def about():
    return render_template("AboutUs.html")


@app.route("/contact")
def contact():
    return render_template("ContactUs.html")


# =====================User============================

@app.route("/user")
def user():
    if 'user' in session:
        cafes = mongo.db.manager.find()  # Fetch all cafés
        cafe_list = []
        # print(cafe_list)
        for cafe in cafes:
            # Ensure 'image' exists and is not None
            image_data = base64.b64encode(cafe['cimage']).decode('utf-8') if 'cimage' in cafe else None
            if image_data:
                print("Image data successfully encoded")

            cafe_list.append({
                '_id': str(cafe.get('_id')),  # Convert ObjectId to string
                'cafe_id': cafe.get('cafe_id'),
                'cafe_name': cafe.get('cafe_name', 'Unnamed Café'),
                'cimage': image_data,  # Store the base64-encoded image data
            })

        return render_template("user/u_dashboard.html", cafes=cafe_list)  # Correct the template path

    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = users.find_one({'username': request.form['user']})

        if username:
            if users.find_one({'username': request.form['user'], 'password': request.form['pass']}):
                session['user'] = request.form['user']
                return redirect(url_for('user'))
            else:
                flash("Invalid password")
        else:
            flash("Invalid username")

        return redirect(url_for('login'))  # Redirect to the login page to show the flash message

    return render_template("user/userlogin.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    dropdown_data = request.form.get('dropdown')
    if request.method == "POST":
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})
        if existing_user is None:
            users.insert_one({'fname': request.form['fname'],
                              'lname': request.form['lname'],
                              'email': request.form['email'],
                              'phone': request.form['Phone'],
                              'age': request.form['age'],
                              'gender': dropdown_data,
                              'username': request.form['username'],
                              'password': request.form["pass"],
                              })
            session['username'] = request.form['username']
            flash("Registration successful!", "success")
            return redirect(url_for('user'))
        else:
            flash("User already exists", "error")
            return redirect(url_for('register'))
    return render_template("user/register.html", gender=gender)


@app.route('/get_user_menu/<obj_id>', methods=['GET', 'POST'])
def get_user_menu(obj_id):
    obj = ObjectId(obj_id)
    if 'user' not in session:  # Ensure user is logged in
        return redirect(url_for('user'))

    coursor = Cafes.find_one({'_id': obj})
    # print(coursor)
    cafe_id = coursor.get('cafe_id')
    # print(cafe_id)

    # Fetch all menu items from the collection
    menu_items = menu.find({'cafe_id': cafe_id})  # This will give you a cursor with all documents in the collection

    # Prepare the data to be rendered in the HTML template
    items_with_images = []
    for item in menu_items:
        # Convert binary image data to base64
        image_data = base64.b64encode(item['image']).decode('utf-8') if 'image' in item else None
        items_with_images.append({
            '_id': item.get('_id'),
            'name': item.get('name'),
            'description': item.get('description'),
            'rating': item.get('rating', 0),
            'price': item.get('price', 0),
            'image_data': image_data
        })

    # Render the template with the list of menu items
    return render_template("user//menu.html", menu_items=items_with_images)


@app.route('/place_order', methods=['POST'])
def place_order():
    item_id = request.form.get('menu_item_id')  # Get the item ID from the POST data
    quantity = int(request.form.get('quantity', 1))  # Get the quantity from the form
    user = session.get('user')
    print(user)
    try:
        object_id = ObjectId(item_id)  # Convert to ObjectId
    except Exception as e:
        flash(f"Invalid item ID: {e}", "error")
        return redirect(url_for('get_user_menu'))  # Redirect to the menu page if invalid

    # Fetch the item from the menu collection in MongoDB
    item = mongo.db.menu.find_one({"_id": object_id})
    userdetail = users.find_one({"username": user})
    # print(item)
    print(userdetail)

    if not item:
        flash("Item not found", "error")
        return redirect(url_for('get_user_menu'))

    if not userdetail:
        print('no user')

    order_item = {
        'item_name': item.get('name', 'Unknown Item'),
        'item_price': float(item.get('price', 0.0)),
        'quantity': quantity,
        'total_price': float(item.get('price', 0.0)) * quantity
    }

    # Create a new order document
    order = {
        'user': user,
        'phone': userdetail['phone'],
        'cafe': item.get('cafe_id'),
        'items': [order_item],
        'time': item.get('time'),
        'timestamp': datetime.now(),  # Record the time the order was placed
        'status': 'Pending'  # Set initial status as 'Pending'
    }

    # Insert the new order into the "orders" collection
    result = mongo.db.orders.insert_one(order)

    if result.acknowledged:
        flash("Order placed successfully!", "success")
        # Redirect to view the order details
        order_id = result.inserted_id
        return redirect(url_for('view_order', order_id=order_id))
    else:
        flash("Failed to place order.", "error")
        return redirect(url_for('get_user_menu'))


@app.route('/view_order/<order_id>', methods=['GET'])
def view_order(order_id):
    try:
        # Convert order_id to ObjectId and fetch the order
        id = ObjectId(order_id)
        order = mongo.db.orders.find_one({"_id": id})
        # print(order)
        if not order:
            flash("Order not found.", "error")
            return render_template('user/view_order.html', order=None)

        order_details = []
        for item in order['items']:
            order_details.append({
                'item_name': item.get('item_name'),
                'item_price': item.get('item_price'),
                'quantity': item.get('quantity'),
                'total_price': item.get('total_price'),
            })
        # print(order_details)
        # Add subtotal, shipping, and total calculations if available
        subtotal = sum(item['total_price'] for item in order_details)
        shipping_cost = order.get('shipping_cost', 0.0)
        total_price = subtotal + shipping_cost

        # Prepare the order context for the template
        order_context = {
            'order_id': str(order['_id']),
            'timestamp': order['timestamp'],
            'items': order_details,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total_price': total_price,
            'status': order.get('status', 'Pending')
        }
        print(order_context)
        return render_template('user/view_order.html', order=order_context)

    except Exception as e:
        print(e)
        flash(f"Invalid order ID: {e}", "error")
        return render_template('user/view_order.html', order=None)


@app.route('/display_order', methods=['GET', 'POST'])
def display_orders():
    try:
        # Fetch the current user from the session
        user = session.get('user')
        if not user:
            flash("User not logged in.", "error")
            return render_template('user/order_details.html', orders=None)

        # Find all orders for the user
        user_orders = orders.find({"user": user})
        user_orders_list = list(user_orders)  # Convert the cursor to a list

        # If no orders are found, display an error message
        if not user_orders_list:
            flash("No orders found.", "error")
            return render_template('user/order_details.html', orders=None)

        # Prepare a list to hold details of each order
        all_orders_context = []
        overall_total_price = 0  # Variable to keep track of the overall total price

        # Iterate through each order and gather its details
        for order in user_orders_list:
            order_details = []
            for item in order.get('items', []):
                order_details.append({
                    'item_name': item.get('item_name'),
                    'item_price': item.get('item_price'),
                    'quantity': item.get('quantity'),
                    'total_price': item.get('total_price'),
                })

            # Calculate the subtotal, shipping, and total price for the order
            subtotal = sum(item['total_price'] for item in order_details)
            shipping_cost = order.get('shipping_cost', 0.0)
            total_price = subtotal + shipping_cost
            overall_total_price += total_price  # Add the total price of the current order to the overall total price
            # Prepare the context for the current order
            order_context = {
                'order_id': str(order['_id']),
                'timestamp': order.get('timestamp'),
                'items': order_details,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'total_price': total_price,
                'status': order.get('status', 'Pending')
            }

            # Add the current order's context to the list of all orders
            all_orders_context.append(order_context)

        print('all orders:', all_orders_context)
        print('overall total price:', overall_total_price)

        # Render the template with the list of all orders and the overall total price
        return render_template('user/order_details.html', orders=all_orders_context,
                               overall_total_price=overall_total_price)

    except Exception as e:
        print(e)
        flash(f"Error retrieving orders: {e}", "error")
        return render_template('user/order_details.html', orders=None)


# ===============Manager======================================
@app.route("/manager")
def mgrdashboard():
    if 'cafe_id' in session:
        try:
            cafe = session.get('cafe_id')
            if not cafe:
                flash("User not logged in.", "error")
                return render_template('Manager/m_dashboard.html', orders=None)

            user_orders = orders.find({"cafe": cafe})
            user_orders_list = list(user_orders)
            print(user_orders)

            if not user_orders_list:
                flash("No orders found.", "error")
                # print(user_orders_list)
                return render_template('Manager/m_dashboard.html', orders=None)

            all_orders_context = []
            overall_total_price = 0

            for order in user_orders_list:
                order_details = []
                for item in order.get('items', []):
                    order_details.append({
                        'item_name': item.get('item_name'),
                        'item_price': item.get('item_price'),
                        'quantity': item.get('quantity'),
                        'total_price': item.get('total_price'),
                    })

                subtotal = sum(item['total_price'] for item in order_details)
                shipping_cost = order.get('shipping_cost', 0.0)
                total_price = subtotal + shipping_cost
                overall_total_price += total_price

                order_context = {
                    'order_id': str(order['_id']),
                    'user': order['user'],
                    'timestamp': order.get('timestamp'),
                    'items': order_details,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'total_price': total_price,
                    'status': order.get('status', 'Pending'),
                    'contact': order.get('phone'),
                    'waiting_time': order.get('waiting_time', 'N/A')
                }

                all_orders_context.append(order_context)
                print(all_orders_context)

            return render_template('Manager/m_dashboard.html', orders=all_orders_context,
                                   overall_total_price=overall_total_price)

        except Exception as e:
            print(e)
            flash(f"Error retrieving orders: {e}", "error")
            return render_template('Manager/m_dashboard.html', orders=None)
    return redirect(url_for('manager_login'))


@app.route("/manager_login", methods=["GET", "POST"])
def manager_login():
    if request.method == "POST":
        username = Cafes.find_one({'cafe_id': request.form['user']})
        if username:
            if Cafes.find_one({'cafe_id': request.form['user'], 'password': request.form['pass']}):
                session['cafe_id'] = request.form['user']
                return redirect(url_for('mgrdashboard'))
            else:
                flash("Invalid username or password", "error")
        else:
            flash("Invalid username or password", "error")
    return render_template("Manager/mgrlogin.html")


@app.route("/manager_register", methods=["GET", "POST"])
def manager_register():
    if request.method == "POST":
        # Check if cafe_id is provided
        if 'cafe_id' not in request.form:
            flash("Cafe ID is required", 'error')
            return render_template("Manager/mgrregister.html")

        cafe_id = request.form['cafe_id']

        # Check if the user already exists
        existing_user = Cafes.find_one({'cafe_id': cafe_id})

        if existing_user:
            flash("User already exists", 'error')
            return render_template("Manager/mgrregister.html")
        # print(image)
        # Check if image is uploaded
        if 'image' not in request.files:
            flash('No image uploaded!', 'error')
            return render_template("Manager/mgrregister.html")

        image = request.files['image']
        image_filename = secure_filename(image.filename)

        # Validate the image file type
        if not is_allowed_file(image_filename):
            flash('Invalid file type!', 'error')
            return render_template("Manager/mgrregister.html")

        try:
            image_data = image.read()
        except Exception as e:
            flash(f"Error reading image: {e}", 'error')
            return render_template("Manager/mgrregister.html")

        # Insert new manager into the database
        Cafes.insert_one({
            'fname': request.form['fname'],
            'lname': request.form['lname'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'cafe_name': request.form['cname'],
            'location': request.form['address'],
            'cafe_id': cafe_id,
            'password': request.form['password'],
            'cimage': image_data
        })

        # Set session data
        session['cafe_id'] = cafe_id

        # Redirect to the manager dashboard
        return redirect(url_for('mgrdashboard'))

    # Render the registration page for GET requests or after a failed POST request
    return render_template("Manager/mgrregister.html")


@app.route('/get_manager_menu', methods=['GET', 'POST'])
def get_manager_menu():
    cuser = session.get('cafe_id')
    if 'cafe_id' not in session:  # Ensure user is logged in
        return redirect(url_for('manager_login'))
    # print(session)

    # Fetch all menu items from the collection
    menu_items = menu.find({"cafe_id": cuser})  # This will give you a cursor with all documents in the collection

    # Prepare the data to be rendered in the HTML template
    items_with_images = []
    for item in menu_items:
        # Convert binary image data to base64
        image_data = base64.b64encode(item['image']).decode('utf-8') if 'image' in item else None
        items_with_images.append({
            '_id': item.get('_id'),
            'name': item.get('name'),
            'description': item.get('description'),
            'rating': item.get('rating', 0),
            'price': item.get('price', 0),
            'time': item.get('time', 0),
            'image_data': image_data
        })

    # Render the template with the list of menu items
    return render_template("Manager/manager_menu.html", menu_items=items_with_images, menu=menu)


@app.route("/menu/add", methods=["GET", "POST"])
def add_menu_item():
    if 'cafe_id' not in session:
        return redirect(url_for('manager_login'))

    cafe_id = session.get("cafe_id")

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded!', 'error')
            return render_template("Manager/manageraddmenulist.html")

        image = request.files['image']
        image_filename = secure_filename(image.filename)

        if not is_allowed_file(image_filename):
            flash('Invalid file type!', 'error')
            return render_template("Manager/manageraddmenulist.html")

        try:
            image_data = image.read()
        except Exception as e:
            flash(f"Error reading image: {e}", 'error')
            return render_template("Manager/manageraddmenulist.html")

        # Ensure cafe_id is set
        if not cafe_id:
            cafe_id = request.form.get("cafe_id")
            if not cafe_id:
                flash('Cafe ID is missing!', 'error')
                return redirect(url_for("index"))

        name = request.form.get("item-name")
        rating = float(request.form.get("item-rating"))
        description = request.form.get("item-description")
        price = float(request.form.get("item-price"))
        time = float(request.form.get("item-time"))

        try:
            menu.insert_one({
                "image": image_data,
                "name": name,
                "description": description,
                "rating": rating,
                "price": price,
                "time": time,
                "cafe_id": cafe_id
            })
            flash('Menu item added successfully!', 'success')
            return redirect(url_for("get_manager_menu"))
        except Exception as e:
            # Log the error
            logging.error(f"Error adding menu item: {e}")
            flash(f"Error adding menu item: {e}", 'error')

    return render_template("Manager/manageraddmenulist.html", menu=menu)


@app.route('/update_item/<item_id>', methods=['POST', 'GET'])
def update_item(item_id):
    # Validate the item_id
    try:
        obj_id = bson.ObjectId(item_id)
    except bson.errors.InvalidId:
        flash("Invalid item ID.", "error")
        return redirect(url_for('get_manager_menu'))

    # Fetch the item
    item = menu.find_one({"_id": obj_id})
    if not item:
        flash("Menu item not found.", "error")
        return redirect(url_for('get_manager_menu'))

    # Prepare image data if available
    image_data = base64.b64encode(item.get("image", b"")).decode("utf-8") if item.get("image") else None

    if request.method == 'POST':
        # Handle form data and update the item
        name = request.form.get("Item-name")
        description = request.form.get("Item-description")
        rating = float(request.form.get("Item-rating", 0))
        price = float(request.form.get("Item-price", 0))

        # Check for image update
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            image_data = image.read()

        # Update the item in the database
        menu.update_one(
            {"_id": obj_id},
            {"$set": {
                "name": name,
                "description": description,
                "rating": rating,
                "price": price,
                "image": image_data
            }}
        )

        flash("Menu item updated successfully!", "success")
        return redirect(url_for("get_manager_menu"))

    # Render the edit form with pre-filled data
    return render_template("Manager/edit_menu_item.html", item=item, item_id=item_id, image_data=image_data)


@app.route('/delete_menu/<item_id>', methods=['DELETE', 'POST'])
def delete_menu(item_id):
    # Validate the ObjectId
    try:
        obj_id = bson.ObjectId(item_id)
    except bson.errors.InvalidId:
        flash("Invalid item ID.", "error")
        return redirect(url_for('get_manager_menu'))

    # Delete the document from MongoDB
    try:
        result = menu.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            flash("Menu item not found.", "error")
            return redirect(url_for("get_manager_menu"))

        flash("Menu item deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting menu item: {e}", "error")
        return redirect(url_for("get_manager_menu"))

    return redirect(url_for("get_manager_menu"))


# @app.route('/manager_orders', methods=['GET', 'POST'])
# def manager_display_orders():
#     try:
#         cafe = session.get('cafe_id')
#         if not user:
#             flash("User not logged in.", "error")
#             return render_template('Manager/m_dashboard.html', orders=None)
#
#         user_orders = orders.find({"cafe_id": cafe})
#         user_orders_list = list(user_orders)
#
#         if not user_orders_list:
#             flash("No orders found.", "error")
#             return render_template('Manager/m_dashboard.html', orders=None)
#
#         all_orders_context = []
#         overall_total_price = 0
#
#         for order in user_orders_list:
#             order_details = []
#             for item in order.get('items', []):
#                 order_details.append({
#                     'item_name': item.get('item_name'),
#                     'item_price': item.get('item_price'),
#                     'quantity': item.get('quantity'),
#                     'total_price': item.get('total_price'),
#                 })
#
#             subtotal = sum(item['total_price'] for item in order_details)
#             shipping_cost = order.get('shipping_cost', 0.0)
#             total_price = subtotal + shipping_cost
#             overall_total_price += total_price
#
#             order_context = {
#                 'order_id': str(order['_id']),
#                 'timestamp': order.get('timestamp'),
#                 'items': order_details,
#                 'subtotal': subtotal,
#                 'shipping_cost': shipping_cost,
#                 'total_price': total_price,
#                 'status': order.get('status', 'Pending'),
#                 'contact': order.get('contact'),
#                 'waiting_time': order.get('waiting_time', 'N/A')
#             }
#
#             all_orders_context.append(order_context)
#
#         return render_template('Manager/m_dashboard.html', orders=all_orders_context, overall_total_price=overall_total_price)

# except Exception as e:
#     print(e)
#     flash(f"Error retrieving orders: {e}", "error")
#     return render_template('Manager/m_dashboard.html', orders=None)


@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')

        # Update the order status in the database
        result = orders.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': new_status}})

        if result.modified_count > 0:
            flash('Order status updated successfully.', 'success')
        else:
            flash('Failed to update order status.', 'error')

    except Exception as e:
        print(e)
        flash(f"Error updating order status: {e}", 'error')

    return redirect(url_for('mgrdashboard'))


# =======================Admin============================
@app.route("/admin")
def admindashboard():
    if 'admin' in session:
        user = users.find({})
        manager = Cafes.find({})
        Users = list(user)
        Managers = list(manager)
        # print(Users)
        # print(Managers)

        return render_template('Admin/a_dashboard.html', users=Users, managers=Managers)

    return redirect(url_for('admin_login'))


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = mongo.db.admin
        username = admin.find_one({'username': request.form['user']})
        if username:
            if admin.find_one({'username': request.form['user'], 'password': request.form['pass']}):
                session['admin'] = request.form['user']
                return redirect(url_for('admindashboard'))
            else:
                flash("Invalid username or password", "error")
        else:
            flash("Invalid username or password", "error")
    return render_template("Admin/adminlogin.html")



# @app.route("/addadmin", methods=["GET", "POST"])
# def admin_register():
#     if request.method == "POST":
#         admin = mongo.db.admin
#         existing_user = admin.find_one({'username': request.form['username']})
#
#         if existing_user is None:
#             admin.insert_one({'username': request.form["username"],
#                               'Email': request.form['email'],
#                               'password': request.form['password']
#                               })
#             session['admin'] = request.form['admin']
#             return redirect(url_for('admindashbord'))
#         return "User already exists"
#     return render_template("adminreg.html")


@app.route('/update_profile/<user_type>/<user_id>', methods=['GET', 'POST'])
def update_profile(user_type, user_id):
    print(f"Request method: {request.method}")
    print(f"Form data: {request.form}")

    if user_type == 'user':
        collection = users
    elif user_type == 'manager':
        collection = Cafes
    else:
        return "Invalid user type."

    user_detail = collection.find_one({"_id": ObjectId(user_id)})
    if not user_detail:
        return "User not found."

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_phone = request.form.get('phone')
        new_password = request.form.get('password')

        print(f"new_username: {new_username}")
        print(f"new_email: {new_email}")
        print(f"new_phone: {new_phone}")
        print(f"new_password: {new_password}")

        update_data = {
            "username": new_username,
            "email": new_email,
            "phone": new_phone,
            "password": new_password,
        }

        print(update_data)
        try:
            collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
            flash("Profile updated successfully.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Error updating profile: {e}", "error")

    return render_template('Admin/update_profile.html', user=user_detail)




# ==================Logout=====================
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, host="localhost")
