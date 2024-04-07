from flask import Flask, render_template, request, session, redirect, url_for
from flask_pymongo import PyMongo
import bcrypt

app = Flask(__name__)
app.secret_key = "mysecretkey"
app.config['MONGO_DBNAME'] = 'loginex'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/loginex'

mongo = PyMongo(app)


@app.route("/index")
def index():
    if 'username' in session:
        return "You are logged in as " + session['username']
    return redirect(url_for('login'))


@app.route("/admin")
def mgrdashbord():
    if 'm_user' in session:
        return "You are logged in as " + session['m_user']
    return redirect(url_for('manager_login'))


@app.route("/admin")
def admindashbord():
    if 'm_user' in session:
        return "You are logged in as " + session['m_user']
    return redirect(url_for(''))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = mongo.db.users
        username = users.find_one({'username': request.form['username']})
        if username:
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), username['password']):
                session['username'] = request.form['username']
                return redirect(url_for('index'))
        return "Invalid username or password"
    return render_template("adminlogin.html")


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['m_pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name': request.form['c_name'],
                              'username': request.form['m_username'],
                              'password': hashpass,
                              'email': request.form['m_email']
                              })
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return "User already exists"
    return render_template("addadmin.html")


@app.route("/manager_login", methods=["GET", "POST"])
def manager_login():
    if request.method == "POST":
        manager = mongo.db.manager
        username = manager.find_one({'m_user': request.form['m_user']})
        if username:
            if bcrypt.checkpw(request.form['m_password'].encode('utf-8'), username['m_password']):
                session['m_user'] = request.form['m_user']
                return redirect(url_for('mgrdashbord'))
        return "Invalid username or password"
    return render_template("Manager//mgrlogin.html")


@app.route("/manager_register", methods=["GET", "POST"])
def manager_register():
    if request.method == "POST":
        manager = mongo.db.manager
        existing_user = manager.find_one({'m_user': request.form['m_user']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['m_pass'].encode('utf-8'), bcrypt.gensalt())
            manager.insert_one({'c_name': request.form['c_name'],
                                'm_user': request.form['m_user'],
                                'm_password': hashpass,
                                'm_email': request.form['m_email'],
                                })
            session['m_user'] = request.form['m_user']
            return redirect(url_for('mgrdashbord'))
        return "User already exists"
    return render_template("Manager//mgrregister.html")


@app.route("/manager_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = mongo.db.admin
        username = admin.find_one({'m_user': request.form['m_user']})
        if username:
            if bcrypt.checkpw(request.form['m_password'].encode('utf-8'), username['m_password']):
                session['m_user'] = request.form['m_user']
                return redirect(url_for('mgrdashbord'))
        return "Invalid username or password"
    return render_template("Admin//adminlogin.html")


@app.route("/manager_register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        admin = mongo.db.admin
        existing_user = admin.find_one({'admin': request.form['admin']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['a_pass'].encode('utf-8'), bcrypt.gensalt())
            admin.insert_one({'c_name': request.form['a_name'],
                              'admin': request.form['admin'],
                              'a_password': hashpass,
                              'a_email': request.form['a_email'],
                              })
            session['admin'] = request.form['admin']
            return redirect(url_for('admindashbord'))
        return "User already exists"
    return render_template("Admin//addadmin.html")


if __name__ == "__main__":
    app.run(debug=True, host="localhost")
