from flask import Flask, request, render_template, make_response,session
from flask_session import Session
import sqlite3
from sqlite3 import Error
import requests
s = requests.Session()
global email
# Flask constructor
app = Flask(__name__)
app.secret_key = "any random string"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


import openai

def openAI(userinp):
    openai.api_key = "" #Had to delete the API key
    model_engine = "text-davinci-003"

    prompt = "here is a situation that I am in right now: " + userinp + ". return only a 1 if this should be reported to the police or only a 0 if it shouldn't"

    completion = openai.Completion.create(
        engine = model_engine,
        prompt = prompt,
        max_tokens = 1024,
        n = 1,
        stop = None,
        temperature = 0.5,
    )

    rating = completion.choices[0].text #0 and 1 crap

    return int(rating)


from twilio.rest import Client

def twillioTOADMIN(userinp, rating):
    accountSID = "AC0828dfa24008998a6a4eaa3bc63369f6"
    authTOKEN  = "3112b9026301a6b8efb7e5993396c68e"

    client = Client(accountSID, authTOKEN)

    if "0" in rating: #not urgent (rating by chatGPT)
        ret = "A student has posted the following message: " + userinp + ". We have flagged this message as NOT URGENT."
    elif "1" in rating: #urgent (rating by chatGPT)
        ret = "ALERT: A student has posted the following message: " + userinp + ". We have flagged this message as URGENT. Please log into WASP."

    message = client.messages.create(body=ret + "", from_="+18884921334", to="+16692220280") #twillio number, faculty phone number


def twillioTOALL(ret):
    accountSID = "AC0828dfa24008998a6a4eaa3bc63369f6"
    authTOKEN  = "3112b9026301a6b8efb7e5993396c68e"

    client = Client(accountSID, authTOKEN)

    #array of all the student's phone numbers
    numbers = ["+16692220280", "+16692946744", "+16692876793"]
    for i in range(len(numbers)) :
        message = client.messages.create(body=ret + "", from_="+18884921334", to=numbers[i]) #twillio number, all student phone numbers

@app.route('/')
def yes():
   return render_template('home.html')
if __name__ == 'main':
   app.run()

@app.route('/feed')
def feed():
    con = sqlite3.connect("using.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    email = session['email']
    school = session['school']
    personnel = session['personnel']
    print(personnel);
    if (personnel == "Administrator"):
        sql2 = "SELECT title, content FROM posts WHERE schoolname = ? AND (visible = 'Everyone' OR visible = 'Administrators')"
        cur.execute(sql2, (school,))
        rows = cur.fetchall()
        return render_template("feed.html", rows=rows)
    elif (personnel == "Student"):
        sql2 = "SELECT title, content FROM posts WHERE schoolname = ? AND (visible = 'Everyone' OR visible = 'Students')"
        cur.execute(sql2, (school,))
        rows = cur.fetchall()
        return render_template("feed.html", rows=rows)
    elif (personnel == "Teacher"):
        sql2 = "SELECT title, content FROM posts WHERE schoolname = ? AND (visible = 'Everyone' OR visible = 'Teachers')"
        cur.execute(sql2, (school,))
        rows = cur.fetchall()
        return render_template("feed.html", rows=rows)
    else:
        return render_template("feed.html")





@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/post')
def post():
    return render_template('post.html')

@app.route('/security')
def security():
    return render_template('security.html')


@app.route('/home')
def home():
    return render_template('home.html');

@app.route('/profile')
def profile():
    con = sqlite3.connect("using.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    school = session['school']
    email = session['email']
    fname = session['fname']
    lname = session['lname']
    schoolID = session['sclID']
    schoolname = session['school']
    type = session['personnel']
    sql2 = "SELECT title, content FROM posts WHERE schoolname = ? AND email = ?"
    cur.execute(sql2, (school,email))
    rows = cur.fetchall()
    con.commit()
    return render_template("profile.html", rows=rows, email=email, fname=fname, lname=lname, sclID=schoolID, school=schoolname)



@app.route('/posting', methods=['POST', 'GET'])
def posting():

    if request.method == 'POST':
        print("hi");
        # getting input with name = fname in HTML form
        global title
        title = request.form["title"]
        # getting input with name = lname in HTML form
        global content
        content = request.form["content"]
        global visible
        visible = request.form["visible"]

        school = session['school']
        flagged = openAI(content)

        email = session['email']
        connection = sqlite3.connect('using.db')
        print("hi")

        if(flagged == 1):
            print("hi")
            visible = "administrators"
        else:
            print(flagged)


        with connection:
            # create a new project
            project = (title, content, visible, school, flagged,email);
            sql = " INSERT INTO posts(title, content, visible, schoolname, flagged, email) VALUES(?,?,?,?,?,?) "

            cur = connection.cursor()
            cur.execute(sql, project)
            connection.commit()


        return render_template('post.html')




@app.route('/signup', methods=['POST', 'GET'])
def signup():

    if request.method == 'POST':
        connection = sqlite3.connect('using.db')
        print("hi");
        # getting input with name = fname in HTML form

        first = request.form["fname"]
        session['fname'] = first
        # getting input with name = lname in HTML form

        last = request.form["lname"]
        session['lname'] = last
        email = request.form["email"]
        session['email'] = email

        schoolid = request.form["sclID"]
        session['sclID'] = schoolid

        school = request.form["scln"]
        session['school'] = school

        personnel = request.form["psnl"]
        session['personnel'] = personnel

        password = request.form["pwd"]

        project = (first, last, email, schoolid, school, personnel, password)

        sql = ''' INSERT INTO users(firstname,lastname, email, schoolID, schoolname, type, password)
                      VALUES(?,?,?,?,?,?, ?) '''
        cur = connection.cursor()

        cur.execute(sql, project)
        connection.commit()

        return feed()


@app.route('/log', methods=['POST', 'GET'])
def log():
    if request.method == 'POST':
        print("hi");
        email = request.form["email"]
        password = request.form["psw"]
        resp = make_response(render_template('index.html'))
        resp.set_cookie('emailID', email)
        return resp

@app.route('/showcomments', methods=['POST', 'GET'])
def showcomments():
    if request.method == 'POST':
        con = sqlite3.connect("using.db")
        postname = request.form["fname"]
        session['postname'] = postname
        con.row_factory = sqlite3.Row

        cur = con.cursor()

        sql = "SELECT title, content FROM comments WHERE postName = ?";
        cur.execute(sql, (postname,))

        rows = cur.fetchall()
        con.commit()

    return render_template('comments.html', rows=rows)

@app.route('/addcomments', methods=['POST', 'GET'])
def addcomments():
    if request.method == 'POST':
        title = request.form["fname"]
        content = request.form["lname"]
        con = sqlite3.connect("using.db")
        postname = session['postname']
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = " INSERT INTO comments(title, content, postname) VALUES(?,?,?)"
        project = (title, content, postname)
        cur = con.cursor()
        cur.execute(sql, project)
        con.commit()
    return render_template('feed.html')




@app.route('/searching', methods=['POST', 'GET'])
def searching():
    if request.method == 'POST':
        searchterm = request.form["fname"]

        con = sqlite3.connect("using.db")
        con.row_factory = sqlite3.Row

        cur = con.cursor()

        sql = "SELECT email, title, content, INSTR(title,?) x FROM posts WHERE x>0";
        cur.execute(sql, (searchterm,))

        rows = cur.fetchall()
        return render_template('search.html', rows=rows)

