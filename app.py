from flask import Flask, render_template, request, session, jsonify, url_for, redirect
from flask_session import Session
from werkzeug.utils import secure_filename
import google.generativeai as genai
import os
from gemini_llm import generate_diet_plan, analyze_food_image, analyze_medical_report, image_analysis
import pandas as pd

app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Required for session
app.secret_key =os.getenv("FLASK_SECRET_KEY", "default_secret_key")  # Needed for session management
ADD_DATA_PASSWORD = os.getenv("ADD_DATA_PASSWORD", "default_password")
app.config['UPLOAD_FOLDER'] = './uploads'

# Configuring Flask-Session to use filesystem-based session storage
app.config['SESSION_TYPE'] = 'filesystem'  # You can use 'redis', 'memcached', etc.
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Optional: Adds an additional layer of security
app.config['SESSION_FILE_DIR'] = './.flask_session'  # Directory where session files will be stored
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")  # Secret key for sessions

# Initialize the session extension
Session(app)

########## Dashboard ##########

# Login route for password protection
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADD_DATA_PASSWORD:
            session['authenticated'] = True  # Mark the session as authenticated
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Incorrect password. Please try again.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))


# Path to the CSV file
csv_file = 'fitness exercises.csv'

# Load the CSV data into a DataFrame
df = pd.read_csv(csv_file)

# Route to display the dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    global df

    if request.method == 'POST':
        try:
            data = request.get_json()
            if data['action'] == 'add':
                video_title = data['title']
                video_url = data['url']

                new_row = {'Titles': video_title, 'URL': video_url}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(csv_file, index=False, encoding='cp1252')

                return jsonify({'status': 'success', 'message': 'Video added successfully!'})

            elif data['action'] == 'edit':
                old_title = data['oldTitle']
                new_title = data['newTitle']
                new_url = data['newUrl']

                df.loc[df['Titles'] == old_title, ['Titles', 'URL']] = [new_title, new_url]
                df.to_csv(csv_file, index=False, encoding='cp1252')

                return jsonify({'status': 'success', 'message': 'Video updated successfully!'})

            elif data['action'] == 'delete':
                title_to_delete = data['title']

                df = df[df['Titles'] != title_to_delete]
                df.to_csv(csv_file, index=False, encoding='cp1252')

                return jsonify({'status': 'success', 'message': 'Video deleted successfully!'})

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return render_template('dashboard.html', data=df.to_dict(orient='records'))



# @app.route('/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def home():
    diet_plan = None
    exercise_videos = []
    form_submitted = False  # Flag to track form submission
    user_details = {}  #to avoid the UnboundLocalError

    if request.method == 'POST':
        form_submitted = True
            # Get user inputs for diet plan
        age = int(request.form.get('age'))
        height = float(request.form.get('height'))
        weight = float(request.form.get('weight'))
        days = int(request.form.get('days'))
        diabetes = bool(request.form.get('diabetes'))
        other_conditions = request.form.get('other_conditions', 'No additional conditions provided')

        # Calculate BMI
        bmi = round(weight / ((height / 100) ** 2), 2)

        # Generate diet plan
        diet_plan, exercise_videos = generate_diet_plan(age, height, weight, bmi, days, diabetes, other_conditions)

        # Prepare user details dictionary
        user_details = {
                'age': age,
                'height': height,
                'weight': weight,
                'bmi': bmi,
                'diabetes': diabetes,
                'other_conditions': other_conditions,
            }

        # Store data in the session
        session['diet_plan'] = diet_plan
        session['user_details'] = user_details
        #get data from session :) because user should be known about details
        diet_plan = session.get('diet_plan', diet_plan)
        user_details = session.get('user_details', {})

    return render_template('index.html', diet_plan=diet_plan, exercise_videos=exercise_videos, user_details=user_details, form_submitted=form_submitted)


# Analyzing Medical report
@app.route('/analyze_report', methods=['GET', 'POST'])

def analyze_report():
    if request.method == 'POST' and 'report_image' in request.files:
        try:
            # Save uploaded image
            image = request.files['report_image']
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Analyze the image using the correct function
            report_image_result = analyze_medical_report(filepath)

            # Store image result in session
            session['report_image_result'] = report_image_result

            # Return result as JSON for AJAX
            return jsonify({'result': report_image_result})

        except Exception as e:
            # Handle any exceptions
            return jsonify({'error': f"An error occurred: {str(e)}"}), 500

    # Render the HTML template for GET requests
    return render_template('analyze_report.html')

# Medical Report Chatbot
@app.route('/medical-report-bot', methods=['POST'])
def medical_report_bot():
    data = request.json  # Expect JSON payload
    query = data.get('query')
    report_image_result = session.get('report_image_result')

    # If no analysis result is available in the session
    if not report_image_result:
        return {"error": "No report analysis found. Please upload and analyze the medical reports first."}, 400

    # Create the prompt for the bot, focusing on the medical report analysis
    prompt = f"""
    You are a helpful AI assistant discussing medical report analysis with the user.

    **User's Report Analysis:**
    {report_image_result} 

    **Guidelines for Response:**
    1. Assume the user's query is primarily about the medical report analysis.
    2. Provide insights on the report, such as any abnormalities, health status, and suggested actions.
    3. If the user is asking about specific details of the report, try to explain in simple terms, avoiding overly technical language.
    4. If the query is unclear, kindly ask for clarification to provide the best response.

    **User Query:**
    {query}
    
    Respond with helpful information based on the user's query, focusing on the medical report analysis.
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"response": response.candidates[0].content.parts[0].text}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    




# Image analysis 
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    image_result = None

    if 'food_image' in request.files:
        # Save uploaded image
        image = request.files['food_image']
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Retrieve user details and diet plan from the session
        user_details = session.get('user_details')
        diet_plan = session.get('diet_plan')

        # Check if data is available
        if not user_details or not diet_plan:
            image_result = "User details or diet plan are missing. Please generate a diet plan first."
        else:
            # Analyze the image
            image_result = analyze_food_image(filepath, diet_plan, user_details)

        # Store image result in session
        session['image_result'] = image_result

        # Return the result as JSON
        return jsonify({'result': image_result})

    return jsonify({'error': 'No image uploaded'}), 400


# Chatbot 
@app.route('/ask-bot', methods=['POST'])
def ask_bot():
    data = request.json  # Expect JSON payload
    query = data.get('query')
    user_details = session.get('user_details')
    diet_plan = session.get('diet_plan')
    image_result = session.get('image_result')

    if not (user_details and diet_plan and image_result):
        return {"error": "Missing data. Ensure a diet plan and image analysis result are available."}, 400

    # Create the prompt for the bot
    prompt = f"""
    You are a knowledgeable AI assistant helping the user with diet plans and food analysis.
    
    **1. Food Image Analysis Result:**  
    {image_result}  

    **2. Personalized Diet Plan:**  
    {diet_plan}

    **Guidelines for Response:**  
1. Assume the user's query is primarily about the food image analysis unless explicitly stated otherwise.  
2. If the query is about the image analysis, provide insights on whether the food aligns with their personalized diet plan and health conditions.  
3. If the query is about the diet plan, focus on meal recommendations, health tips, or explanations based on their health profile.  
4. Use a friendly, clear, and professional tone. Avoid overly technical terms unless necessary, and provide actionable advice.  
5. If the user's query is unclear, gently ask for clarification.

    **User Query:**
    {query}
    
    Respond in a friendly and helpful tone, respond precisely. carefully understand user query and answer. 
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"response": response.candidates[0].content.parts[0].text}, 200
    except Exception as e:
        return {"error": str(e)}, 500




@app.route('/features')
def features():
    return render_template('features.html')
@app.route('/faqs')
def faqs():
    return render_template('faqs.html')
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')
@app.route('/howto')
def howto():
    return render_template('howto.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')
# @app.route('/mealanalysis')
# def mealanalysis():
#     return render_template('mealanalysis.html')

  
# Define the route for image analysis with videos recommendation
@app.route('/image_analysis/', methods=['GET', 'POST'])
def image_analysis_route():
    if request.method == 'POST':
        # Get user details from the form
        age = int(request.form.get('age'))
        height = float(request.form.get('height'))
        weight = float(request.form.get('weight'))
        diabetes = request.form.get('diabetes') == 'true'
        other_conditions = request.form.get('other_conditions', 'No additional conditions provided')

        # Calculate BMI
        bmi = round(weight / ((height / 100) ** 2), 2)

        # Save user details in session 
        user_details = {
            'age': age,
            'height': height,
            'weight': weight,
            'bmi': bmi,
            'diabetes': diabetes,
            'other_conditions': other_conditions,
        }
        session['user_details'] = user_details

        # Check if there's an image uploaded
        if 'food_image' in request.files:
            # Save the uploaded image
            image = request.files['food_image']
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Analyze the image and get video recommendations
            analysis_result = image_analysis(
                age, height, weight, bmi, diabetes, other_conditions, filepath
            )

            # Extract results and recommendations
            result = analysis_result.get('analysis', 'Analysis failed')
            exercise_recommendations = analysis_result.get('exercise_recommendations', [])

            # Store the result and recommendations in the session
            session['image_analysis_result'] = result
            session['exercise_recommendations'] = exercise_recommendations

            # Return result and recommendations as JSON
            return jsonify({
                'result': result,
                'exercise_recommendations': [
                    {'title': rec.get('title', 'No Title'), 'url': rec.get('url', '#')}
                    for rec in exercise_recommendations
                ]
            })

        return jsonify({'error': 'No image uploaded'}), 400

    return render_template('image_analysis.html')


# Meal image analysis chatbot
@app.route('/image_analysis_bot', methods=['POST'])
def image_analysis_bot():
    data = request.json  # Expect JSON payload
    query = data.get('query')
    user_details = session.get('user_details')
    image_analysis_result = session.get('image_analysis_result')

    # If no image analysis result or user details are available in the session
    if not (user_details and image_analysis_result):
        return {"error": "No image analysis found. Please upload and analyze an image first."}, 400

    # Create the prompt for the bot, focusing on the image analysis result
    prompt = f"""
    You are a helpful AI assistant discussing image analysis results with the user.
    **User Details:**
    {user_details}

    **Image Analysis Result:**
    {image_analysis_result}

    **Guidelines for Response:**
    1. Assume the user's query is primarily about the image analysis result.
    2. Provide insights based on the analysis, such as what the image represents or how it relates to the user's details.
    3. If the user is asking about specific details from the analysis, explain them in simple terms, avoiding overly technical language.
    4. If the query is unclear, kindly ask for clarification to provide the best response.
    
    **User Query:**
    {query}
    
    Respond with helpful information based on the image analysis result and the user's details.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"response": response.candidates[0].content.parts[0].text}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    
    # Route to clear session data
@app.route('/clear_session')
def clear_session():
    session.clear()  # Clear the entire session
    return jsonify({"status": "success", "message": "Session data cleared!"})
    

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)  # Create the directory for session files
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
