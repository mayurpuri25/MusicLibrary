from flask import Flask, render_template, request, redirect, url_for, make_response, flash

app = Flask(__name__)
app.secret_key = "your_very_secret_key_here"

# Dummy Database for Users
users = {
    'admin@gmail.com': {'username': 'admin', 'password': 'admin'}
}

@app.route('/', methods=['GET'])
def home():
    username = request.cookies.get('session_token')
    if username:
        return render_template('home.html', username=username)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users.get(email)
        if user and user['password'] == password:
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('session_token', user['username'])
            return resp
        else:
            flash('Invalid email or password!', 'error')  # flash error message    

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        if email in users:
            flash('The email already exists!', 'error')  # Flash message
            return redirect(url_for('register'))
        
        users[email] = {'username': username, 'password': password}
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_token', '', expires=0)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
