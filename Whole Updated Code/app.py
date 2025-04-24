#from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from models import db, User, NewsletterPost
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from flask_cors import CORS
import google.generativeai as genai
from googletrans import Translator
from deep_translator import GoogleTranslator
import requests
import random
import base64
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import folium
from folium import Map, CircleMarker, Marker, Tooltip, Icon
from folium.plugins import HeatMap
import pandas as pd
import branca
import json
from flask import jsonify
    

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '55fc588fcd7ef7e247fa6db7953d398f16520b1aeacabd74'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.secret_key = 'your_secret_key'
with app.app_context():
    db.create_all()




# Configure the Gemini API key
genai.configure(api_key="AIzaSyATFqI_3BL0y78m9R3XTwKcHLMiCURbMcI")

# Whisper API configuration
WHISPER_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
WHISPER_HEADERS = {"Authorization": "Bearer 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"}

# WeatherAPI configuration
WEATHER_API_KEY = "c0363e5d2fde46e098f134021252001"
WEATHER_BASE_URL = "http://api.weatherapi.com/v1/forecast.json"

# Initialize the translator
translator = Translator()

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

#email verification
EMAIL_VERIFICATION_API_KEY = '72f935f4798841c19d6d8fec794816c1'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'agriverseofficial@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'adaj ools figk iduh'  # Replace with your email password
mail = Mail(app)

# Update the UPLOAD_FOLDER to be an absolute path

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get the logged-in user information from your session or database
    #user = User.query.get(session['username'])
    posts = NewsletterPost.query.order_by(NewsletterPost.created_at.desc()).all()
    return render_template('admin/admin_dashboard.html', posts=posts)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

print(f"Upload folder path: {UPLOAD_FOLDER}")  # Debug print
@app.route('/admin/create_post', methods=['GET', 'POST'])
@admin_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('create_post'))
        
        image_url = None
        video_url = None
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    # Create a unique filename to avoid conflicts
                    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    # Save the file
                    file.save(file_path)
                    # Set the URL to be relative to the static folder
                    image_url = f'/static/uploads/{unique_filename}'
                    
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    flash(f'Error uploading image: {str(e)}', 'danger')
                    return redirect(url_for('create_post'))
        
        # Handle video upload (similar changes)
        if 'video' in request.files:
            file = request.files['video']
            if file and file.filename and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    file.save(file_path)
                    video_url = f'/static/uploads/{unique_filename}'
                    
                except Exception as e:
                    print(f"Error saving video: {str(e)}")
                    flash(f'Error uploading video: {str(e)}', 'danger')
                    return redirect(url_for('create_post'))
        
        try:
            post = NewsletterPost(
                title=title,
                content=content,
                image_url=image_url,
                video_url=video_url,
                author_id=session['user_id']
            )
            
            db.session.add(post)
            db.session.commit()
            
            flash('Post created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating post: {str(e)}', 'danger')
            return redirect(url_for('create_post'))
    
    return render_template('admin/create_post.html')

# Add a route to serve static files during development
@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory('static', filename)
    except Exception as e:
        print(f"Error serving static file: {str(e)}")
        return "File not found", 404

@app.route('/newsletter')
def newsletter():
    posts = NewsletterPost.query.order_by(NewsletterPost.created_at.desc()).all()
    return render_template('newsletter.html', posts=posts)
@app.route('/external')
def external():
    try:
        # Read crop production data
        wheat_df = pd.read_csv('external_factor_data/wheat_production.csv')
        cotton_df = pd.read_csv('external_factor_data/cotton_production.csv')
        sugar_df = pd.read_csv('external_factor_data/sugar_production.csv')
        maize_df = pd.read_csv('external_factor_data/maize_production.csv')
        export_df = pd.read_csv('external_factor_data/export_trends_fake_data.csv')
        rainfall_df = pd.read_csv('external_factor_data/rainfall_crop_prices_2010_2025.csv')

        # Get list of years
        years = wheat_df['YEAR'].unique().tolist()
        
        # Get initial data (latest year)
        latest_year = years[-1]  # Get the last year from the list
        
        # Convert data to lists for initial charts
        initial_wheat_data = [
            float(wheat_df[wheat_df['YEAR'] == latest_year]['Punjab'].iloc[0]),
            float(wheat_df[wheat_df['YEAR'] == latest_year]['Sindh'].iloc[0]),
            float(wheat_df[wheat_df['YEAR'] == latest_year]['KPK'].iloc[0]),
            float(wheat_df[wheat_df['YEAR'] == latest_year]['Balochistan'].iloc[0])
        ]
        
        initial_cotton_data = [
            float(cotton_df[cotton_df['YEAR'] == latest_year]['Punjab'].iloc[0]),
            float(cotton_df[cotton_df['YEAR'] == latest_year]['Sindh'].iloc[0]),
            float(cotton_df[cotton_df['YEAR'] == latest_year]['KPK'].iloc[0]),
            float(cotton_df[cotton_df['YEAR'] == latest_year]['Balochistan'].iloc[0])
        ]
        
        initial_sugar_data = [
            float(sugar_df[sugar_df['YEAR'] == latest_year]['Punjab'].iloc[0]),
            float(sugar_df[sugar_df['YEAR'] == latest_year]['Sindh'].iloc[0]),
            float(sugar_df[sugar_df['YEAR'] == latest_year]['KPK'].iloc[0]),
            float(sugar_df[sugar_df['YEAR'] == latest_year]['Balochistan'].iloc[0])
        ]
        
        initial_maize_data = [
            float(maize_df[maize_df['YEAR'] == latest_year]['Punjab'].iloc[0]),
            float(maize_df[maize_df['YEAR'] == latest_year]['Sindh'].iloc[0]),
            float(maize_df[maize_df['YEAR'] == latest_year]['KPK'].iloc[0]),
            float(maize_df[maize_df['YEAR'] == latest_year]['Balochistan'].iloc[0])
        ]

        # Process export trends data
        export_dates = (export_df['Year'].astype(str) + '-' + 
                       export_df['Month'].astype(str).str.zfill(2)).tolist()
        export_index = export_df['Export_Index'].tolist()
        export_prices = export_df['Price'].tolist()

        # Process rainfall and crop price data
        rainfall_years = rainfall_df['Year'].tolist()
        rainfall_data = rainfall_df['Rainfall (mm)'].tolist()
        crop_prices = rainfall_df['Crop Price (USD/ton)'].tolist()

    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'danger')
        return redirect(url_for('index'))

    # Previous data for other charts
    petrol_df = pd.read_csv('external_factor_data/Petrol Prices.csv')
    petrol_dates = petrol_df['date'].tolist()
    petrol_prices = petrol_df['price'].tolist()

    inflation_df = pd.read_csv('external_factor_data/pakistan-inflation-rate-cpi.csv')
    inflation_dates = inflation_df['date'].tolist()
    inflation_rates = inflation_df['per_Capita'].tolist()

    return render_template('external.html',
        years=years,
        initial_wheat_data=initial_wheat_data,
        initial_cotton_data=initial_cotton_data,
        initial_sugar_data=initial_sugar_data,
        initial_maize_data=initial_maize_data,
        petrol_dates=json.dumps(petrol_dates),
        petrol_prices=json.dumps(petrol_prices),
        inflation_dates=json.dumps(inflation_dates),
        inflation_rates=json.dumps(inflation_rates),
        export_dates=json.dumps(export_dates),
        export_index=json.dumps(export_index),
        export_prices=json.dumps(export_prices),
        rainfall_years=json.dumps(rainfall_years),
        rainfall_data=json.dumps(rainfall_data),
        crop_prices=json.dumps(crop_prices),
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
@app.route('/get_crop_production_data/<int:year>')
def get_crop_production_data(year):
    # Read crop data
    wheat_df = pd.read_csv('external_factor_data/wheat_production.csv')
    cotton_df = pd.read_csv('external_factor_data/cotton_production.csv')
    sugar_df = pd.read_csv('external_factor_data/sugar_production.csv')
    maize_df = pd.read_csv('external_factor_data/maize_production.csv')

    # Get data for the selected year
    return jsonify({
        'wheat': get_province_data(wheat_df, year),
        'cotton': get_province_data(cotton_df, year),
        'sugar': get_province_data(sugar_df, year),
        'maize': get_province_data(maize_df, year)
    })

def get_province_data(df, year):
    # Get row for the specified year
    year_data = df[df['YEAR'] == year].iloc[0]
    
    # Return province-wise data
    return {
        'Punjab': year_data['Punjab'],
        'Sindh': year_data['Sindh'],
        'KPK': year_data['KPK'],
        'Balochistan': year_data['Balochistan']
    }


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
                session['username'] = username  # Store username in session
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
           
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('index'))
    
    return render_template('index.html')


# @app.route('/ur')
# def ur_index():
#     return redirect('/ur/home')  # Redirect to the Urdu home page

# @app.route('/ur/home')
# def ur_home():
#     return render_template('ur_home.html')  # Urdu home page

# @app.route('/newsletter')
# def newsletter():
#     return render_template('newsletter.html')  # newsletter page


@app.route('/')
def index():
    return render_template('index.html')  # Redirect to the English home page

@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # Redirect to the index page

# @app.route('/en/home')
# def en_home():
#     return render_template('home.html')  # English home page


# @app.route('/dashboard')
# def home():
#     return render_template('dashboard.html')

# Add dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Add FAQs route
@app.route('/faqs')
def faqs():
    return render_template('faqs.html')
# Add CHATBOT route
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# @app.route('/ur/verify')
# def ur_verify():
#     return render_template('ur_verify.html')  # Urdu verification page

# @app.route('/ur/dashboard')
# def ur_dashboard():
#     return render_template('ur_dashboard.html')  # Urdu dashboard

# @app.route('/ur/help-centre')
# def ur_help_center():
#     return render_template('ur_help_centre.html')  # Urdu Help Centre template

# @app.route('/ur/faqs')
# def ur_faqs():
#     return render_template('ur_faqs.html')  # Urdu FAQs page

#chatbot code#

def transcribe_audio(audio_data):
    try:
        response = requests.post(WHISPER_API_URL, headers=WHISPER_HEADERS, data=audio_data)
        output = response.json()
        return output.get("text", "Error in transcription")
    except Exception as e:
        return f"Error in transcription: {str(e)}"

def translate_roman_urdu(text):
    translated = translator.translate(text, src='auto', dest='en')
    return translated.text

def get_weather_data(location):
    try:
        params = {"key": WEATHER_API_KEY, "q": location, "days": 1}
        response = requests.get(WEATHER_BASE_URL, params=params)
        data = response.json()

        if "error" in data:
            return f"Could not fetch weather data for '{location}'. Please try again."

        location_name = data["location"]["name"]
        region = data["location"]["region"]
        country = data["location"]["country"]
        current = data["current"]
        condition = current["condition"]["text"]
        temp_c = current["temp_c"]
        chance_of_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]

        return (f"Weather in {location_name}, {region}, {country}:\n"
                f"- Condition: {condition}\n"
                f"- Temperature: {temp_c}°C\n"
                f"- Chance of Rain: {chance_of_rain}%")
    except Exception as e:
        return f"Error fetching weather data: {e}"

def extract_location_with_gemini(query):
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-002')
    prompt = f"""
    Extract the location from the following user query. If no location is mentioned, return 'None'.
    Query: {query}
    Location:
    """
    response = gemini_model.generate_content(prompt)
    location = response.text.strip()
    return location if location.lower() != "none" else None

def generate_gemini_answer(conversation_history):
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-002')
    response = gemini_model.generate_content([f"""
    You are a helpful and knowledgeable agricultural chatbot. Assist with crop-related and weather-related queries.
    Use the provided weather information if applicable. If not, reply based on your general knowledge.

    ## Conversation History:
    {conversation_history}

    ## Current User Query:
    {conversation_history.splitlines()[-1]}

    ## Answer:
    """])
    return response.text

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        input_type = data.get('type', 'text')
        
        if input_type == 'audio':
            # Handle audio input
            audio_data = base64.b64decode(data['audio'].split(',')[1])
            user_message = transcribe_audio(audio_data)
            # Translate transcribed text to Urdu for display
            translated_output = GoogleTranslator(source="auto", target="ur").translate(user_message)
        else:
            # Handle text input
            user_message = data.get('message', '')
            
        # Translate to English for processing
        translated_question = translate_roman_urdu(user_message)
        conversation_history = f"User: {translated_question}\n"
        
        # Check for weather-related queries
        if "weather" in translated_question.lower() or "rain" in translated_question.lower():
            location = extract_location_with_gemini(translated_question)
            if not location:
                location = "Pakistan"
            weather_response = get_weather_data(location)
            conversation_history += f"Weather Info: {weather_response}\n"
        
        # Generate Gemini AI response
        response = generate_gemini_answer(conversation_history)
        
        return jsonify({
            'response': response,
            'translated_question': translated_question,
            'urdu_translation': translated_output if input_type == 'audio' else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
@app.route('/get_crop_data', methods=['GET'])
def get_crop_data():
    province = request.args.get('province')
    crops = request.args.get('crops').split(',')

    if not province or not crops:
        return jsonify({'error': 'Invalid input. Please select a province and at least one crop.'}), 400

    crop_files = {
        'Sugar': (SUGAR_ACTUAL_FILE, SUGAR_PRED_FILE),
        'Maize': (MAIZE_ACTUAL_FILE, MAIZE_PRED_FILE),
        'Cotton-1': (COTTON_ACTUAL_FILE, COTTON_PRED_FILE),
        'Cotton-2': (COTTON_ACTUAL_FILE, COTTON_PRED_FILE)
    }

    result = []
    colors_actual = ['rgba(76, 175, 80, 1)', 'rgba(255, 87, 34, 1)', 'rgba(33, 150, 243, 1)', 'rgba(156, 39, 176, 1)']
    colors_predicted = ['rgba(76, 175, 80, 0.5)', 'rgba(255, 87, 34, 0.5)', 'rgba(33, 150, 243, 0.5)', 'rgba(156, 39, 176, 0.5)']

    for i, crop in enumerate(crops):
        if crop not in crop_files:
            continue

        actual_file, pred_file = crop_files[crop]
        actual_data = pd.read_csv(actual_file)
        pred_data = pd.read_csv(pred_file)

        # Handle Cotton by-products
        if crop.startswith('Cotton-'):
            by_product = int(crop.split('-')[1])
            actual_data = actual_data[actual_data['by_product'] == by_product]
            pred_data = pred_data[pred_data['by_product'] == by_product]

        region_actual = actual_data[actual_data['province'] == province].copy()
        region_pred = pred_data[pred_data['province'] == province].copy()

        if region_actual.empty or region_pred.empty:
            continue

        # Standardize dates
        region_actual['date'] = pd.to_datetime(region_actual['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        region_pred['date'] = pd.to_datetime(region_pred['date'], errors='coerce').dt.strftime('%Y-%m-%d')

        dates_actual = region_actual['date'].tolist()
        dates_predicted = region_pred['date'].tolist()

        actual_prices = region_actual['price'].tolist()
        predicted_prices = region_pred['price'].tolist()

        result.append({
            'crop': crop,
            'dates_actual': dates_actual,
            'actual_prices': actual_prices,
            'dates_predicted': dates_predicted,
            'predicted_prices': predicted_prices,
            'color_actual': colors_actual[i % len(colors_actual)],
            'color_predicted': colors_predicted[i % len(colors_predicted)],
        })

    return jsonify(result)

# @app.route('/get_heatmap_data')
# def get_heatmap_data():
#     try:
#         # Read and process the data
#         df = pd.read_csv("new_data/CottonMaster.csv")
#         df['province'] = df['province'].str.strip()
#         df['price'] = (df['minimum'] + df['maximum']) / 2
        
#         df = df[['date', 'station_id', 'by_product_id', 'province', 'Lat', 'Long', 'price']]
#         df['date'] = pd.to_datetime(df['date'])
#         df = df.drop_duplicates()
#         df['Lat'] = pd.to_numeric(df['Lat'], errors='coerce')
#         df['Long'] = pd.to_numeric(df['Long'], errors='coerce')
        
#         # Filter DataFrame
#         df = df[(df['date'] == '2020-12-31') & (df['by_product_id'] == 7)]
        
#         # Prepare heatmap data
#         heat_data = df[['Lat', 'Long', 'price']].values.tolist()
        
#         # Return data needed for rendering
#         return jsonify({
#             'heat_data': heat_data,
#             'min_price': float(df['price'].min()),
#             'max_price': float(df['price'].max())
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


from folium import Map
from folium.plugins import HeatMap
import pandas as pd
import branca
import json
from flask import jsonify

# Mapping crop names to CSV file paths
CROP_CSV_MAPPING = {
    "cotton": "new_data/CottonMaster.csv",
    "sugar": "new_data/SugarMaster.csv",
    "wheat": "new_data/WheatMaster.csv",
    "maize": "new_data/MaizeMaster.csv"
}

@app.route('/get_heatmap_data')
def get_heatmap_data():
    try:
        # Get parameters from the request
        crop = request.args.get('crop', '').strip().lower()
        print(f"Received crop: {crop}")
        by_product = request.args.get('by_product', '')

        # Ensure a valid crop is selected
        if crop not in CROP_CSV_MAPPING:
            return jsonify({'error': 'Invalid or missing crop selection'}), 400

        # Load CSV based on selected crop
        csv_path = CROP_CSV_MAPPING[crop]
        print(f"Loading CSV: {csv_path}")
        df = pd.read_csv(csv_path)

        # Debug: Check if data loaded correctly
        print(f"DataFrame Shape before filtering: {df.shape}")
        print("Column Names:", df.columns)
        print(df.head())

        # Data Cleaning & Processing
        df.columns = df.columns.str.lower()  # Standardize column names
        df['province'] = df['province'].str.strip()
        df['price'] = (df['minimum'] + df['maximum']) / 2
        if crop == "wheat":
            df = df[['date', 'station_id', 'province', 'lat', 'long', 'maximum','price']]
            df['date'] = pd.to_datetime(df['date'])
            df = df.drop_duplicates()
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['long'] = pd.to_numeric(df['long'], errors='coerce')
        else:
            df = df[['date', 'station_id', 'by_product_id', 'province', 'lat', 'long', 'price']]
            df['date'] = pd.to_datetime(df['date'])
            df = df.drop_duplicates()
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['long'] = pd.to_numeric(df['long'], errors='coerce')

        # Debug: Check unique dates before filtering
        print("Available Dates before filtering:", df['date'].unique())
        # Apply by_product filter if provided
        if by_product:
            try:
                by_product_id = int(by_product)
                print("by product value",by_product_id)
                print(f"Filtering for by_product_id: {by_product_id}")
                print("Available by_product_id values:", df['by_product_id'].unique())
                df = df[df['by_product_id'] == by_product_id]
                print(f"Rows after filtering by by_product_id: {len(df)}")
            except ValueError:
                return jsonify({'error': 'Invalid by-product ID'}), 400
        if df.empty:
            return jsonify({'error': 'No data available for the selected filters'}), 404
        # Apply date filter
        latest_date = df['date'].max()
    # Convert to datetime object
        latest_date = pd.to_datetime(latest_date)

    # Format it to 'YYYY-MM-DD' (remove the time part)
        target_date = latest_date.strftime('%Y-%m-%d')
        df = df[df['date'] == target_date]
        print(f"Rows after filtering by date {target_date}: {len(df)}")
        # Ensure data is available
        

                # Create Folium Map
                        
                
        # Ensure lat/lon are numeric
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['long'] = pd.to_numeric(df['long'], errors='coerce')

        # Create the map with an initial view
        m = Map(
            location=[30.0, 70.0],  # Default center (Pakistan)
            zoom_start=4,  # Initial zoom
            max_bounds=True,
            tiles="CartoDB positron",
            width="100%",
            height="350px"
        )

        # Add the heatmap
        heat_data = list(zip(df['lat'], df['long'], df['price']))  # Assuming price influences intensity
        HeatMap(heat_data).add_to(m)

        # **Fit map to the data points**
        if not df.empty:
            sw = [df['lat'].min(), df['long'].min()]  # Southwest corner
            ne = [df['lat'].max(), df['long'].max()]  # Northeast corner
            m.fit_bounds([sw, ne])  # Auto-zoom based on bounds

        # Prepare heatmap data
        heat_data = df[['lat', 'long', 'price']].dropna().values.tolist()

        # Add HeatMap layer
        HeatMap(
            heat_data,
            name="Heatmap",
            min_opacity=0.2,
            radius=20,
            blur=15,
            max_zoom=4,
        ).add_to(m)

        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['long']],
                radius=5,  # Smallest possible size
                color="transparent",  # No border color
                fill=True,
                fill_color="transparent",  # Fully transparent fill
                fill_opacity=0,  # 0 opacity to ensure invisibility
                tooltip=f"Price: {row['price']:.2f} PKR"
            ).add_to(m)
        # Add color scale legend
        colormap = branca.colormap.LinearColormap(
            colors=['blue', 'green', 'yellow', 'red'],
            vmin=df['price'].min(),
            vmax=df['price'].max(),
            caption="Price Intensity"
        ).to_step(n=5)

        colormap.add_to(m)
        m.fit_bounds([[23, 60], [38, 77]])

        # Convert map to HTML
        map_html = m._repr_html_()

        return jsonify({
            'map_html': map_html,
            'min_price': float(df['price'].min()),
            'max_price': float(df['price'].max())
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)