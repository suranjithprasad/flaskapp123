from flask import Flask, render_template, request, redirect, session
import os
import mysql.connector

app = Flask(__name__)
app.debug = True

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'b512e6a78dbcb7'
app.config['MYSQL_DATABASE_PASSWORD'] = 'b429118c'
app.config['MYSQL_DATABASE_DB'] = 'heroku_a1e2684e12fa937'
app.config['MYSQL_DATABASE_HOST'] = 'us-cdbr-east-06.cleardb.net'

# Set the secret key for session management
app.secret_key = 'your_secret_key'

# Create a connection to the MySQL database
mydb = mysql.connector.connect(
    host=app.config['MYSQL_DATABASE_HOST'],
    user=app.config['MYSQL_DATABASE_USER'],
    password=app.config['MYSQL_DATABASE_PASSWORD'],
    database=app.config['MYSQL_DATABASE_DB']
)


@app.route('/')
def index():
    mytable = mydb.cursor()
    mytable.execute("SELECT * FROM register")
    myresult = mytable.fetchall()
    return render_template('index.html', myresult=myresult)

@app.route('/login')
def login_page():
   return render_template('login.html')

@app.route('/register')
def register_page():
   return render_template('register.html')


@app.route('/registerdone', methods=['GET', 'POST'])
def registerdone():
    if request.method == 'POST':
        # Get form data
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if email already exists in database
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM register WHERE email = %s", (email,))
        user = mycursor.fetchone()

        if user:
            return 'Email address already registered'

        # Insert user data into database
        sql = "INSERT INTO register (name, email, password) VALUES (%s, %s, %s)"
        val = (name, email, password)
        mycursor.execute(sql, val)
        mydb.commit()

        # Redirect to the home page
        return render_template('registerdone.html', name=name)

    # If the request method is GET, render the register page
    return render_template('/')

@app.route('/logindone', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']

        # Check if email and password match database record
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM register WHERE email = %s AND password = %s", (email, password))
        user = mycursor.fetchone()

        if user:
            # Create session for logged in user
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]

            return redirect('/dashboard')
        else:
            return 'Invalid email or password'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor = mydb.cursor()

        # Check if table exists, create it if not
        cursor.execute(f"SHOW TABLES LIKE '{user_id}_web_orders'")
        result = cursor.fetchone()
        if not result:
            cursor.execute(f"CREATE TABLE {user_id}_web_orders (id INT AUTO_INCREMENT PRIMARY KEY, web_count INT, topic VARCHAR(255), order_date DATE, status VARCHAR(255))")
        
        cursor.execute(f'SELECT id, web_count, topic, order_date, status FROM {user_id}_web_orders')
        web_orders = cursor.fetchall()
        
        return render_template('dashboard.html', user_name=session['user_name'], user_email=session['user_email'], user_id=session['user_id'], web_orders=web_orders)
    else:
        return redirect('/login')



@app.route('/order_webs', methods=['POST'])
def order_webs():
    if 'user_id' in session:
        user_id = session['user_id']
        quantity = request.form['web_count']
        topic = request.form['topic']

        cursor = mydb.cursor()

        # Check if table exists, create it if not
        cursor.execute(f"SHOW TABLES LIKE '{user_id}_web_orders'")
        result = cursor.fetchone()
        if not result:
            cursor.execute(f"CREATE TABLE {user_id}_web_orders (id INT AUTO_INCREMENT PRIMARY KEY, web_count INT, topic VARCHAR, order_date DATE, status VARCHAR)")

        # Insert new web order into table
        cursor.execute(f"INSERT INTO {user_id}_web_orders (web_count, topic, order_date, status) VALUES (%s, %s, NOW(), 'processing')", (quantity, topic))
        mydb.commit()
        return redirect('/dashboard')
    else:
        return redirect('/login')



@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    if 'user_id' not in session:
        # Redirect the user to the login page if they are not logged in
        return redirect('/login')
    
    user_id = session['user_id']
    order_id = request.form.get('order_id')
    
    if not order_id:
        # Return an error message if the order ID is missing from the form data
        return "Order ID is missing"
    
    cursor = mydb.cursor()
    
    try:
        # Check if the order belongs to the user
        cursor.execute(f"SELECT * FROM {user_id}_web_orders WHERE id=%s", (order_id,))
        result = cursor.fetchone()
        if not result:
            # Return an error message if the order ID does not match any orders for the user
            return "Invalid order ID"
        
        # Delete the order from the table
        cursor.execute(f"DELETE FROM {user_id}_web_orders WHERE id=%s", (order_id,))
        mydb.commit()
        
        # Redirect the user to the dashboard page after cancelling the order
        return redirect('/dashboard')
    except Exception as e:
        # Return an error message if any other errors occur during the database operation
        return f"Error cancelling order: {str(e)}"
    finally:
        # Close the database cursor to free up resources
        cursor.close()





@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run()