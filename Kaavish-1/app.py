#from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '55fc588fcd7ef7e247fa6db7953d398f16520b1aeacabd74'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.secret_key = 'your_secret_key'
with app.app_context():
    db.create_all()

# File to store user data
USER_DATA_FILE = 'user_data.json'
# SUGAR_ACTUAL_FILE = 'data/sugar_province_actual.csv'
SUGAR_ACTUAL_FILE = 'data/final_sugar_province_actual.csv'
# SUGAR_PRED_FILE = 'data/sugar_province_pred.csv'
SUGAR_PRED_FILE = 'data/final_sugar_province_pred_formatted.csv'
MAIZE_ACTUAL_FILE = 'data/maize_actual.csv'
MAIZE_PRED_FILE = 'data/maize_pred.csv'

COTTON_ACTUAL_FILE = 'data/cotton_actual.csv'
COTTON_PRED_FILE = 'data/cotton_pred.csv'

# Initialize the user data file
try:
    with open(USER_DATA_FILE, 'r') as file:
        user_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(user_data, file)

# @app.route('/')
# def index():
#     return render_template('index.html')

# #signup

# #email verification
# EMAIL_VERIFICATION_API_KEY = '72f935f4798841c19d6d8fec794816c1'

# # Flask-Mail configuration
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'sidraaamir122019@gmail.com'  # Replace with your email
# app.config['MAIL_PASSWORD'] = 'azma juwr nkof ejtw'  # Replace with your email password
# mail = Mail(app)

# # Temporary storage for verification codes
# verification_data = {}
# @app.route('/signup', methods=['POST'])
# def signup():
#     fullname = request.form['fullname']
#     username = request.form['username']
#     city = request.form['city']
#     email = request.form['email']
#     phone = request.form['phone']
#     password = request.form['password']
#     confirm_password = request.form['confirm-password']
    
#     # Validate email with Abstract API
#     api_url = f"https://emailvalidation.abstractapi.com/v1/?api_key={EMAIL_VERIFICATION_API_KEY}&email={email}"
#     response = requests.get(api_url)
#     email_data = response.json()
#     if not email_data['is_valid_format']['value'] or not email_data['deliverability'] == "DELIVERABLE":
#         flash('Invalid or unregistered email address. Please use a valid email.', 'danger')
#         return render_template('index.html', email=email)  # Return to the signup page
    
#     # Validate username
#     import re
#     username_criteria = re.compile(r'^[a-zA-Z0-9._]{3,15}$')
#     if not username_criteria.match(username):
#         flash('Username must be 3-15 characters long, can include letters, numbers, underscores, and periods. It must not start or end with a special character or contain consecutive special characters.', 'danger')
#         return render_template('index.html', username=username)  # Return to the signup page
    
#     if ".." in username or "__" in username or "._" in username or "_. " in username:
#         flash('Username must not contain consecutive special characters.', 'danger')
#         return render_template('index.html', username=username)  # Return to the signup page
    
#     # Validate password complexity
#     password_criteria = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+={}[\]:;"<>,.?/\\|~-])[A-Za-z\d!@#$%^&*()_+={}[\]:;"<>,.?/\\|`~-]{8,}$')
#     if not password_criteria.match(password):
#         flash('Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.', 'danger')
#         return render_template('index.html', username=username, email=email)  # Return to the signup page
        
#     if password != confirm_password:
#         flash('Passwords do not match!', 'danger')
#         return render_template('index.html', username=username, email=email)  # Return to the signup page

#     # Check if username already exists
#     if username in user_data:
#         flash('Username already exists. Please choose a different one.', 'danger')
#         return render_template('index.html', username=username, email=email)  # Return to the signup page
    
#     # Check if user exists in the database
#     existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
#     if existing_user:
#         flash('Username or email already exists!', 'danger')
#         return render_template('index.html', username=username, email=email)  # Return to the signup page

#     # If all checks pass, proceed to send email for verification
#     verification_code = str(random.randint(100000, 999999))
#     verification_data[email] = {
#         'code': verification_code,
#         'expiry': datetime.now() + timedelta(minutes=1),
#         'username': username,
#         'password': password
#     }
#     session['signup_data'] = {
#         'username': username,
#         'email': email,
#         'password': password,
#         'city': city,
#         'fullname': fullname,
#         'phone': phone
#     }

#     # Send verification email
#     msg = Message('Your Verification Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
#     msg.body = f'Your verification code is {verification_code}. It will expire in 1 minute.'
#     mail.send(msg)

#     flash('A verification code has been sent to your email.', 'info')
#     return redirect(url_for('verify', email=email))

# @app.route('/verify/<email>', methods=['GET', 'POST'])
# def verify(email):
#     if request.method == 'POST':
#         # Get the verification code entered by the user
#         entered_code = request.form['verification_code']

#         # Check if the email is in the verification data
#         if email in verification_data:
#             data = verification_data[email]
#             if datetime.now() > data['expiry']:
#                 flash('Verification code expired. Please sign up again.', 'danger')
#                 return redirect(url_for('index'))
#             elif entered_code == data['code']:
#                 # Code is valid, complete signup
#                 del verification_data[email]  # Clear temporary data

#                 # Retrieve user details from session
#                 signup_data = session.pop('signup_data', None)
#                 if not signup_data:
#                     flash('Session expired. Please sign up again.', 'danger')
#                     return redirect(url_for('index'))
                
#                 username = signup_data['username']
#                 password = signup_data['password']

#                 # Hash password and create new user
#                 hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
#                 new_user = User(username=username, email=email, password=hashed_password)
#                 db.session.add(new_user)
#                 db.session.commit()

#               #  flash('Signup successful! Please log in.', 'success')
#                 return redirect(url_for('index'))
#             else:
#                 flash('Invalid verification code. Please try again.', 'danger')
#                 return redirect(url_for('verify', email=email))
#         else:
#             flash('No verification data found. Please sign up again.', 'danger')
#             return redirect(url_for('index'))
    
#     return render_template('verify.html', email=email)


# @app.route('/login', methods=['POST'])
# def login():
#     if request.method == 'POST':
#             # Get form data
#             username = request.form['username']
#             password = request.form['password']
            
#             # Find user
#             user = User.query.filter_by(username=username).first()
#             if user and check_password_hash(user.password, password):
#                 # Login successful
#                 session['user_id'] = user.id
#                 session['username'] = user.username
#                 flash('Logged in successfully!', 'success')
#                 return redirect(url_for('home'))
#             else:
#                 flash('Invalid username or password!', 'danger')
#                 return redirect(url_for('index'))
        
#     return render_template('index.html')

# @app.route('/home')
# def home():
#     return render_template('home.html')

# # Add dashboard route
# @app.route('/dashboard')
# def dashboard():
#     return render_template('dashboard.html')

# @app.route('/help-centre')
# def help_centre():
#     return render_template('help_centre.html')

# @app.route('/get_sugar_data', methods=['GET'])
# def get_sugar_data():
#     crop = request.args.get('crop')
#     by_product = request.args.get('by_product')  # Fetch by_product parameter
#     regions = request.args.get('regions').split(',')

#     if crop == 'Sugar':
#         actual_file = SUGAR_ACTUAL_FILE
#         pred_file = SUGAR_PRED_FILE
#     elif crop == 'Maize':
#         actual_file = MAIZE_ACTUAL_FILE
#         pred_file = MAIZE_PRED_FILE
#     elif crop == 'Cotton':  # Handle Cotton
#         actual_file = COTTON_ACTUAL_FILE
#         pred_file = COTTON_PRED_FILE
#     else:
#         return jsonify({'error': 'Invalid crop selected.'}), 400

#     # Read the actual and predicted prices data
#     actual_data = pd.read_csv(actual_file)
#     pred_data = pd.read_csv(pred_file)

#     # Filter by by_product if specified
#     if by_product:
#         actual_data = actual_data[actual_data['by_product'] == int(by_product)]
#         pred_data = pred_data[pred_data['by_product'] == int(by_product)]

#     # Filter and prepare data for each region
#     result = []
#     colors_actual = ['rgba(76, 175, 80, 1)', 'rgba(255, 87, 34, 1)', 'rgba(33, 150, 243, 1)']
#     colors_predicted = ['rgba(76, 175, 80, 0.5)', 'rgba(255, 87, 34, 0.5)', 'rgba(33, 150, 243, 0.5)']

#     for i, region in enumerate(regions):
#         region_actual = actual_data[actual_data['province'] == region].copy()
#         region_pred = pred_data[pred_data['province'] == region].copy()

#         if region_actual.empty or region_pred.empty:
#             continue

#         # Standardize dates to ISO 8601 format
#         region_actual['date'] = pd.to_datetime(region_actual['date'], errors='coerce').dt.strftime('%Y-%m-%d')
#         region_pred['date'] = pd.to_datetime(region_pred['date'], errors='coerce').dt.strftime('%Y-%m-%d')

#         dates_actual = region_actual['date'].tolist()
#         dates_predicted = region_pred['date'].tolist()

#         actual_prices = region_actual['price'].tolist()
#         predicted_prices = region_pred['price'].tolist()

#         result.append({
#             'region': region,
#             'dates_actual': dates_actual,
#             'actual_prices': actual_prices,
#             'dates_predicted': dates_predicted,
#             'predicted_prices': predicted_prices,
#             'color_actual': colors_actual[i % len(colors_actual)],
#             'color_predicted': colors_predicted[i % len(colors_predicted)],
#         })

#     return jsonify(result)






# if __name__ == '__main__':
#     app.run(debug=True)

#email verification
EMAIL_VERIFICATION_API_KEY = '72f935f4798841c19d6d8fec794816c1'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sidraaamir122019@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'azma juwr nkof ejtw'  # Replace with your email password
mail = Mail(app)

# Temporary storage for verification codes
verification_data = {}
@app.route('/signup', methods=['POST'])
def signup():
    fullname = request.form['fullname']
    username = request.form['username']
    city = request.form['city']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    confirm_password = request.form['confirm-password']
    
    # Validate email with Abstract API
    api_url = f"https://emailvalidation.abstractapi.com/v1/?api_key={EMAIL_VERIFICATION_API_KEY}&email={email}"
    response = requests.get(api_url)
    email_data = response.json()
    if not email_data['is_valid_format']['value'] or not email_data['deliverability'] == "DELIVERABLE":
        flash('Invalid or unregistered email address. Please use a valid email.', 'danger')
        return render_template('index.html', email=email)  # Return to the signup page
    
    # Validate username
    import re
    username_criteria = re.compile(r'^[a-zA-Z0-9._]{3,15}$')
    if not username_criteria.match(username):
        flash('Username must be 3-15 characters long, can include letters, numbers, underscores, and periods. It must not start or end with a special character or contain consecutive special characters.', 'danger')
        return render_template('index.html', username=username)  # Return to the signup page
    
    if ".." in username or "__" in username or "._" in username or "_. " in username:
        flash('Username must not contain consecutive special characters.', 'danger')
        return render_template('index.html', username=username)  # Return to the signup page
    
    # Validate password complexity
    password_criteria = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+={}[\]:;"<>,.?/\\|~-])[A-Za-z\d!@#$%^&*()_+={}[\]:;"<>,.?/\\|`~-]{8,}$')
    if not password_criteria.match(password):
        flash('Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.', 'danger')
        return render_template('index.html', username=username, email=email)  # Return to the signup page
        
    if password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return render_template('index.html', username=username, email=email)  # Return to the signup page

    # Check if username already exists
    if username in user_data:
        flash('Username already exists. Please choose a different one.', 'danger')
        return render_template('index.html', username=username, email=email)  # Return to the signup page
    
    # Check if user exists in the database
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash('Username or email already exists!', 'danger')
        return render_template('index.html', username=username, email=email)  # Return to the signup page

    # If all checks pass, proceed to send email for verification
    verification_code = str(random.randint(100000, 999999))
    verification_data[email] = {
        'code': verification_code,
        'expiry': datetime.now() + timedelta(minutes=1),
        'username': username,
        'password': password
    }
    session['signup_data'] = {
        'username': username,
        'email': email,
        'password': password,
        'city': city,
        'fullname': fullname,
        'phone': phone
    }

    # Send verification email
    msg = Message('Your Verification Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f'Your verification code is {verification_code}. It will expire in 1 minute.'
    mail.send(msg)

    flash('A verification code has been sent to your email.', 'info')
    return redirect(url_for('verify', email=email))

@app.route('/verify/<email>', methods=['GET', 'POST'])
def verify(email):
    if request.method == 'POST':
        # Get the verification code entered by the user
        entered_code = request.form['verification_code']

        # Check if the email is in the verification data
        if email in verification_data:
            data = verification_data[email]
            if datetime.now() > data['expiry']:
                flash('Verification code expired. Please sign up again.', 'danger')
                return redirect(url_for('index'))
            elif entered_code == data['code']:
                # Code is valid, complete signup
                del verification_data[email]  # Clear temporary data

                # Retrieve user details from session
                signup_data = session.pop('signup_data', None)
                if not signup_data:
                    flash('Session expired. Please sign up again.', 'danger')
                    return redirect(url_for('index'))
                
                username = signup_data['username']
                password = signup_data['password']

                # Hash password and create new user
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

              #  flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid verification code. Please try again.', 'danger')
                return redirect(url_for('verify', email=email))
        else:
            flash('No verification data found. Please sign up again.', 'danger')
            return redirect(url_for('index'))
    
    return render_template('verify.html', email=email)


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
            # Get form data
            username = request.form['username']
            password = request.form['password']
            
            # Find user
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                # Login successful
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password!', 'danger')
                return redirect(url_for('index'))
        
    return render_template('index.html')


@app.route('/ur')
def ur_index():
    return redirect('/ur/home')  # Redirect to the Urdu home page

@app.route('/ur/home')
def ur_home():
    return render_template('ur_home.html')  # Urdu home page


@app.route('/')
def index():
    return render_template('index.html')  # Redirect to the English home page

@app.route('/en/home')
def en_home():
    return render_template('home.html')  # English home page




@app.route('/home')
def home():
    return render_template('home.html')

# Add dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/help-centre')
def help_centre():
    return render_template('help_centre.html')






@app.route('/ur/verify')
def ur_verify():
    return render_template('ur_verify.html')  # Urdu verification page

@app.route('/ur/dashboard')
def ur_dashboard():
    return render_template('ur_dashboard.html')  # Urdu dashboard

@app.route('/ur/help-centre')
def ur_help_center():
    return render_template('ur_help_centre.html')  # Urdu Help Centre template




@app.route('/get_sugar_data', methods=['GET'])
def get_sugar_data():
    crop = request.args.get('crop')
    by_product = request.args.get('by_product')  # Fetch by_product parameter
    regions = request.args.get('regions').split(',')

    if crop == 'Sugar':
        actual_file = SUGAR_ACTUAL_FILE
        pred_file = SUGAR_PRED_FILE
    elif crop == 'Maize':
        actual_file = MAIZE_ACTUAL_FILE
        pred_file = MAIZE_PRED_FILE
    elif crop == 'Cotton':  # Handle Cotton
        actual_file = COTTON_ACTUAL_FILE
        pred_file = COTTON_PRED_FILE
    else:
        return jsonify({'error': 'Invalid crop selected.'}), 400

    # Read the actual and predicted prices data
    actual_data = pd.read_csv(actual_file)
    pred_data = pd.read_csv(pred_file)

    # Filter by by_product if specified
    if by_product:
        actual_data = actual_data[actual_data['by_product'] == int(by_product)]
        pred_data = pred_data[pred_data['by_product'] == int(by_product)]

    # Filter and prepare data for each region
    result = []
    colors_actual = ['rgba(76, 175, 80, 1)', 'rgba(255, 87, 34, 1)', 'rgba(33, 150, 243, 1)']
    colors_predicted = ['rgba(76, 175, 80, 0.5)', 'rgba(255, 87, 34, 0.5)', 'rgba(33, 150, 243, 0.5)']

    for i, region in enumerate(regions):
        region_actual = actual_data[actual_data['province'] == region].copy()
        region_pred = pred_data[pred_data['province'] == region].copy()

        if region_actual.empty or region_pred.empty:
            continue

        # Standardize dates to ISO 8601 format
        region_actual['date'] = pd.to_datetime(region_actual['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        region_pred['date'] = pd.to_datetime(region_pred['date'], errors='coerce').dt.strftime('%Y-%m-%d')

        dates_actual = region_actual['date'].tolist()
        dates_predicted = region_pred['date'].tolist()

        actual_prices = region_actual['price'].tolist()
        predicted_prices = region_pred['price'].tolist()

        result.append({
            'region': region,
            'dates_actual': dates_actual,
            'actual_prices': actual_prices,
            'dates_predicted': dates_predicted,
            'predicted_prices': predicted_prices,
            'color_actual': colors_actual[i % len(colors_actual)],
            'color_predicted': colors_predicted[i % len(colors_predicted)],
        })

    return jsonify(result)






if __name__ == '__main__':
    app.run(debug=True)