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
    return redirect(url_for('login'))  # Redirect to login page if not logged in

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
    return render_template("user.html")

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name': request.form['name'],
                              'username': request.form['username'],
                              'password': hashpass,
                              'email': request.form['email'],
                              'age': request.form['age']
                            })
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return "User already exists"
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="localhost")
