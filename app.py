from io import BytesIO
import time
import boto3
from flask import Flask, render_template, request, redirect, send_file, url_for, flash, session, make_response,  jsonify
import requests

app = Flask(__name__)
app.secret_key = "your_very_secret_key_here" 


# Configure AWS client
s3_client = boto3.client(
    's3',
    aws_access_key_id='ASIAQHF47EC3GQVJ5LVX',
    aws_secret_access_key='Ma8ypf2TOJVzW6eCJpOtibFBbJyfJjkuabs7OsTO',
    region_name='us-east-1'
)


# Global cache-control headers – applied to every response
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def home():
    if 'username' in session and 'email' in session:
        return render_template('home.html', username=session['username'], email=session['email'])
    else:
        return redirect(url_for('login'))
    
@app.route('/unsubscribe_song', methods=['POST'])
def unsubscribe_song():
    data = request.json
    try:
        res = requests.post("https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/unsubscribe", json=data)
        res.raise_for_status()
        return jsonify({"message": "Unsubscribed successfully"}), 200
    except Exception as e:
        print("Unsubscribe error:", e)
        return jsonify({"error": "Unsubscribe failed"}), 500



@app.route('/song_image/<path:image_key>')
def song_image(image_key):
    bucket_name = 's4067635-music-images'
    try:
        # Fetch object from S3
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=image_key)
        file_stream = BytesIO(s3_response['Body'].read())

        # Serve as an image response
        return send_file(file_stream, mimetype='image/jpeg')

    except Exception as e:
        print("Error fetching image:", e)
        return jsonify({'error': 'Image could not be retrieved'}), 404


@app.route('/subscribe_song', methods=['POST'])
def subscribe_song():
    subscription_data = request.json

    required_fields = ['email', 'title', 'artist', 'album', 'year', 'img_url']
    if not all(field in subscription_data for field in required_fields):
        return jsonify({'message': 'Missing required subscription data'}), 400

    subscribe_api_url = 'https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/subscribe'

    try:
        response = requests.post(subscribe_api_url, json=subscription_data)
        response.raise_for_status()
        return jsonify({'message': 'Subscribed successfully!'}), 200
    except requests.exceptions.RequestException as e:
        print('Subscription API error:', e)
        return jsonify({'message': 'Subscription failed'}), 500
    except Exception as e:
        print('Internal error in /subscribe_song:', e)
        return jsonify({'message': 'Internal server error'}), 500



@app.route('/songs', methods=['GET'])
def get_songs():
    artist = request.args.get('artist', '')
    album = request.args.get('album', '')
    title = request.args.get('title', '')
    year = request.args.get('year', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    api_url = "https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/song"

    # Build query
    params = {}
    if artist: params['artist'] = artist
    if album: params['album'] = album
    if title: params['title'] = title
    if year: params['year'] = year

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Apply pagination manually
        results = data.get("results", [])
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated = results[start:end]

        return jsonify({
            "results": paginated,
            "total": total,
            "page": page,
            "limit": limit
        })

    except Exception as e:
        print("API call failed:", e)
        return jsonify({"results": [], "total": 0, "page": page, "limit": limit}), 500



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # Make GET request with email and password as query params
            response = requests.get("https://oipqedkg7h.execute-api.us-east-1.amazonaws.com/prod/user",
                                    params={'email': email, 'password': password})
            result = response.json()

            if response.status_code == 200:
                # Login successful: store username and email in session
                username = result.get('username')
                session['username'] = username
                session['email'] = email

                # delay 
                time.sleep(1)

                # Create response, set cookies for username and email, then redirect to home
                resp = make_response(redirect(url_for('home')))
                resp.set_cookie('username', username)
                resp.set_cookie('email', email)
                return resp

            elif response.status_code == 401:
                flash('email or password is invalid', 'error')
            elif response.status_code == 404:
                flash('email or password is invalid', 'error')
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
                flash('The email already exists', 'error')
            else:
                flash('Something went wrong! Try again.', 'error')
        except Exception as e:
            print('API call failed:', e)
            flash('Could not connect to registration service.', 'error')

    return render_template('register.html')

@app.route('/logout')
def logout():
    # Remove session keys for username and email
    session.pop('username', None)
    session.pop('email', None)
    
    # Create response for redirection and delete cookies
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('username')
    resp.delete_cookie('email')
    return resp

if __name__ == "__main__":
    app.run(debug=True)
