import time
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import requests

app = Flask(__name__)
app.secret_key = "your_very_secret_key_here"


# Global cache-control headers – applied to every response
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # Make GET request with email and password as query params
            response = requests.get("https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/user", params={'email': email, 'password': password})
            result = response.json()

            if response.status_code == 200:
                # Login successful
                session['username'] = result.get('username')
                # flash('Login successful!', 'success')
                # time.sleep(2)  # optional
                return redirect(url_for('home'))
            elif response.status_code == 401:
                flash('Incorrect password!', 'error')
            elif response.status_code == 404:
                flash('User not found!', 'error')
            else:
                flash('Login failed. Try again later.', 'error')

        except Exception as e:
            print("Login API failed:", e)
            flash('Could not connect to login service.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Prepare payload
        payload = {
            'email': email,
            'username': username,
            'password': password
        }

        try:
            # Send POST request to API Gateway
            response = requests.post('https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/user', json=payload)

            # Handle response
            if response.status_code == 201:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            elif response.status_code == 400:
                flash('Missing fields or invalid request.', 'error')
            elif response.status_code == 409:
                flash('User already exists.', 'error')
            else:
                flash('Something went wrong! Try again.', 'error')
        except Exception as e:
            print('API call failed:', e)
            flash('Could not connect to registration service.', 'error')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the user session
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
