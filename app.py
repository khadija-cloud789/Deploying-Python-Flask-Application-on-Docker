import pymysql
pymysql.install_as_MySQLdb()
from jira import JIRA
from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors # <-- Needed for DictCursor to fix the TypeError
from datetime import date
import time as t

app = Flask(__name__)
app.secret_key = 'd9a3b73d0a94ce2ca266372cccc03b9b1567c69f227b3cc7'

# Database Configuration
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'YOUR_MYSQL_USER'
app.config['MYSQL_PASSWORD'] = 'YOUR_MYSQL_PASS'
app.config['MYSQL_DB'] = 'alnafi'

mysql = MySQL(app)

@app.route('/')
def get_home():
    return render_template('index.html')

@app.route('/trainer')
def trainer():
    return render_template('trainer_form.html')

@app.route('/trainer_create', methods=['POST', 'GET'])
def trainer_create():
    if request.method == 'POST':
        fname_data = request.form['fname']
        lname_data = request.form['lname']
        design_data = request.form['design']
        course_data = request.form['course']
        cdate = date.today()
        
        cursor = mysql.connection.cursor()
        sql = "INSERT INTO trainer_details (fname, lname, design, course, datetime) VALUES (%s, %s, %s, %s, %s)"
        val = (fname_data, lname_data, design_data, course_data, cdate)
        cursor.execute(sql, val)
        mysql.connection.commit()
        cursor.close()
        return "DONE, Data has been stored. <a href='/trainer'>Go Back</a>"

@app.route('/trainer_data', methods=['POST', 'GET'])
def trainer_data():
    cursor = mysql.connection.cursor()
    sql = "SELECT * FROM trainer_details"
    cursor.execute(sql)
    row = cursor.fetchall()
    return render_template('trainer_report.html', output_data=row)

@app.route('/trainer_filter', methods=['POST', 'GET'])
def trainer_filter():
    if request.method == 'POST':
        course_search = request.form['course']
        cursor = mysql.connection.cursor()
        
        if course_search == "All":
            sql = "SELECT * FROM trainer_details"
        else:
            # Look at the single quotes carefully: course='" + course_search + "'
            sql = "SELECT * FROM trainer_details WHERE course='" + course_search + "'"
            
        cursor.execute(sql)
        row = cursor.fetchall()
        return render_template('trainer_report.html', output_data=row)
    
    # This runs if you just refresh the page or type the URL manually
    else:
        cursor = mysql.connection.cursor()
        sql = "SELECT * FROM trainer_details"
        cursor.execute(sql)
        row = cursor.fetchall()
        return render_template('trainer_report.html', output_data=row)
# 1. Route to display the Jira form
@app.route('/jira')
def jira():
    return render_template('jira_page.html')

# 2. Route to handle the form submission and create the Jira ticket
@app.route('/jira_create', methods=['POST', 'GET'])
def jira_create():
    if request.method == 'POST':
        # Get form data
        project_data = request.form['project']
        issuetype_data = request.form['issuetype']
        summary_data = request.form['summary']
        desc_data = request.form['desc']
        priority_data = request.form['priority']

        # --- YOUR SPECIFIC JIRA DETAILS ---
        server = "YOUR_JIRA_SERVER"
        user = "YOUR_JIRA_USER" # <-- MAKE SURE THIS IS YOUR EMAIL
        apitoken = "YOUR_API_HERE"

        # Authenticate with Jira
        jira = JIRA(server=server, basic_auth=(user, apitoken))

        try:
            # Create the issue (REPORTER REMOVED)
            issue = jira.create_issue(
                project=project_data,
                summary=summary_data,
                description=desc_data,
                issuetype={'name': issuetype_data},
                priority={'name': priority_data}
            )
            
            print(f"Ticket Created: {issue.key}")
            return f"Success! Ticket {issue.key} created. <a href='/jira'>Go Back</a>"
            
        except Exception as e:
            print(f"Error: {e}")
            return f"Failed to create ticket: {e} <a href='/jira'>Go Back</a>"

    return render_template('jira_page.html')
# 1. Route to display the login form
@app.route('/login_page')
def login_page():
    return render_template('login.html')

# 2. Route to process login
@app.route('/login', methods=['POST', 'GET'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # --- FIXING THE TypeError: Using DictCursor ---
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        
        if account:
            # Create session data
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return render_template('index.html', username=session['username'])
        else:
            msg = 'Incorrect Username/password!!!'
            
    return render_template('login.html', msg=msg)

# 3. Route for Logout
@app.route('/logout')
def logout():
    # Remove session data
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login_page'))

# 4. Route to display Registration form
@app.route('/register')
def register():
    return render_template('register.html')

# 5. Route to process Registration
@app.route('/create_account', methods=['POST', 'GET'])
def create_account():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Username already registered!!!'
            return render_template('register.html', msg=msg)
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            
    return render_template('login.html', msg=msg)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
