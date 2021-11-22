import json
import requests
from flask.templating import render_template
from app import app, db, bcrypt, socketio
from flask import request, redirect, url_for, flash, session
from flask_socketio import emit, join_room, leave_room
from MySQLdb._exceptions import IntegrityError

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.errorhandler(404)
@app.route('/404')
def fourofour(error):
    return render_template('error.html', title='404')

@app.route('/app')
def _app():
    if session['loggedIn'] != True or session['loggedIn'] == None:
        return redirect(url_for('login'))
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM essays ORDER BY essaysTimestamp DESC")
    essays = cursor.fetchall()
    lenessays = len(essays)
    print(essays)
    for i in range(len(essays)):
        average = ratings(essays[i][0])
        print('AGG: ' + str(average))
    cursor.execute("SELECT * FROM users WHERE usersId=%s", (session['userId'],))
    userss = cursor.fetchone()
    if essays != None:
        return render_template('app.html', title='App', essays=essays, users=userss)
    return render_template('app.html', title='App', session=session)

@app.route('/submit-essay', methods=['GET', 'POST'])
def submit_essay():
    if session['loggedIn'] != True or session['loggedIn'] == None:
        return redirect(url_for('login'))
    if request.method == 'POST':
        print(request.form)
        essay = request.form['essay']
        category = request.form['dropdown']
        title = request.form['title']
        cursor = db.connection.cursor()
        cursor.execute("INSERT INTO essays (essaysEssay, essaysCategory, essaysTitle,essaysUid, essaysUsername) VALUES (%s, %s, %s, %s, %s)", (essay, category,title, session['userId'],session['username']))
        remove_points(30)
        db.connection.commit()
        return redirect(url_for('_app'))
    return render_template('essayu.html', title="Submit Essay")

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['rpass']
        email = request.form['email']
        if password == confirm_password:
            try:
                cursor = db.connection.cursor()
                password = bcrypt.generate_password_hash(password)
                cursor.execute("""INSERT INTO users (usersName, usersPass, usersEmail, usersPoints) VALUES (%s, %s, %s, %s)""",(username, password, email, 0,))
                db.connection.commit()
                msg = 'User created successfully'
                return redirect(url_for('login'))
            except IntegrityError:
                db.connection.rollback()
                msg = 'Username already exists'
            if msg != None:
                return render_template('register.html', title='Register', msg=msg)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db.connection.cursor()
        cursor.execute("""SELECT * FROM users WHERE usersName = %s""", (username,))
        if cursor.rowcount == 1:
            user = cursor.fetchone()
            print(user)
            print(user[1])
            if bcrypt.check_password_hash(user[1], password):
                session['username'] = username
                session['loggedIn'] = True
                session['userId'] = user[0]
                session['points'] = user[2]
                print(session)
                return redirect(url_for('_app'))
            else:
                msg = 'Invalid password'
        else:
            msg = 'Invalid username'
        if msg != None:
            return render_template('login.html', title='Login', msg=msg)
    return render_template('login.html')

@app.route('/review-essay/<int:essayid>', methods=['GET', 'POST'])
def review_essay(essayid):
    if session['loggedIn'] != True or session['loggedIn'] == None:
        return redirect(url_for('login'))
    else:
        cursor = db.connection.cursor()
        cursor.execute("""SELECT * FROM reviews WHERE reviewsEssayId=%s""", (essayid,))
        reviews = cursor.fetchall()
        print(reviews)
        cursor.execute("""SELECT * FROM essays WHERE essaysId=%s""", (essayid,))
        essay = cursor.fetchone()
        rate = ratings(essayid)
        for i in range(len(reviews)):
            print(reviews[i])
        if rate != 'No ratings yet.':
            average = ratings(essayid)
            return render_template('review-essay.html', title="Review Essay", essayid=essayid, essay=essay, reviews=reviews, average=average)
        else:
            return render_template('review-essay.html', title="Review Essay", essayid=essayid, essay=essay, reviews=reviews, rate="No ratings yet.")

@socketio.on('connection', namespace='/review-essay')
def connect_re(json):
    print('Client Connected: ' + str(json['data']))

@socketio.on('join', namespace='/review-essay')
def join(json):
    session['room'] = json['room']
    print(json['room'])
    join_room(json['room'])
    print('Client joined room: ' + str(json['room']))

@socketio.on('add review', namespace='/review-essay')
def add_review(json):
    print(session)
    print(json)
    join_room(session['room'])
    cursor = db.connection.cursor()
    cursor.execute("""SELECT * FROM reviews WHERE reviewsEssayId=%s AND reviewsUid=%s""", (json['room'], session['userId'],))
    reviews = cursor.fetchall()
    print(reviews)
    if reviews == None or len(reviews) < 1:
        average = ratings(session['room'])
        print('Averaasddsdasdasgee: ' + str(average))
        cursor.execute("""INSERT INTO reviews (reviewsEssayId, reviewsFeedback, reviewsRating, reviewsUid, reviewsUsername) VALUES (%s, %s, %s, %s, %s)""", (json['room'], json['feedback'], json['rating'], session['userId'], session['username']))
        cursor.execute("""UPDATE essays SET essaysAverageR=%s WHERE essaysId=%s""", (average, json['room']))
        add_points(50)
        db.connection.commit()
        rate = ratings(json['room'])
        print('Lsa: ' + str(rate))
        emit('reviewed', {'feedback': json['feedback'], 'rating':json['rating'], 'average': str(rate)}, room=session['room'])
    else:
        pass

def ratings(room):
    cursor = db.connection.cursor()
    cursor.execute("""SELECT reviewsRating FROM reviews WHERE reviewsEssayId = %s""", (room,))
    ratings = cursor.fetchall()
    rates = []
    sum = 0
    if len(ratings) != 0:
        for value in range(len(ratings)):
            for x in ratings[value]:
                rates.append(x)
                sum += x
                print('Rates: ' + str(rates))
        average = sum / len(rates)
        average = round(average, 1)
        print('Average: ' + str(average))
        return average
    else:
        return 'No ratings yet.'

def add_points(amt):
    cursor = db.connection.cursor()
    print(type(amt))
    cursor.execute("""SELECT usersPoints FROM users WHERE usersId = %s""", (session['userId'],))
    users = cursor.fetchone()
    tpe = type(users[0])
    print(tpe)
    newpoints = int(users[0]) + amt
    print(newpoints)
    cursor.execute("""UPDATE users SET usersPoints=%s WHERE usersId=%s""", (newpoints, session['userId']))
    db.connection.commit()
    return newpoints

def remove_points(amt):
    cursor = db.connection.cursor()
    print(type(amt))
    cursor.execute("""SELECT usersPoints FROM users WHERE usersId = %s""", (session['userId'],))
    users = cursor.fetchone()
    tpe = type(users[0])
    print(tpe)
    newpoints = int(users[0]) - amt
    print(newpoints)
    cursor.execute("""UPDATE users SET usersPoints=%s WHERE usersId=%s""", (newpoints, session['userId']))
    db.connection.commit()
    return newpoints

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))