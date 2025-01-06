import os
from dotenv import load_dotenv
import google.generativeai as genai
from exercise_videos import load_video_data

# Load environment variables
load_dotenv()

# Initialize Gemini client
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate_diet_plan(age: int, height: float, weight: float, bmi: float, days: int, diabetes: bool, other_conditions: str) -> str:

    # Load exercise video data
    video_data = load_video_data()
    
    # Logic for exercise video recommendations based on health conditions
    exercise_recommendations = []
    
    if diabetes:
        exercise_recommendations += video_data['diabetes']
    if 'heart' in other_conditions.lower():
        exercise_recommendations += video_data['heart_health']
    if 'obesity' in other_conditions.lower():
        exercise_recommendations += video_data['obesity']
    if 'joint' in other_conditions.lower():
        exercise_recommendations += video_data['joint_mobility']
    
    # Fallback for general fitness if no specific condition matches
    if not exercise_recommendations:
        exercise_recommendations = video_data['general_fitness']
    
    # Create the prompt
    prompt = f"""
    You are a professional dietician acting with the precision and care of a doctor. Your task is to create a personalized diet plan in a structured format, analyzing the patient's details to best fit their health needs.

**Health Note:**
Based on the user's health condition, the following diet plan has been carefully designed to meet their nutritional requirements and ensure they achieve their health goals. Please review the health conditions and the recommended diet carefully.

**Patient Details:**
- Age: {age}
- Height: {height} cm
- Weight: {weight} kg
- BMI: {bmi}
- Duration of diet plan requested: {days} days
- Diabetes: {'Yes' if diabetes else 'No'}
- Other Health Conditions: {other_conditions}

Instructions:
1. Carefully review the patient information above and use it to design a personalized diet plan for each day.
2. Create the plan in a professional, doctor-like tone with clear instructions.

 Use a structured, organized format that includes a heading for each day, followed by sections for each meal type.
3. **Format each day's diet plan as follows** (note: use HTML styling for formatting, but **do not show the HTML tags in the response**; treat them as instructions for formatting, like making headings bold as `<h1>` would, but show the result as plain text):
   - Day X (e.g., Day 1, Day 2, etc.)
   - Breakfast: List items for breakfast in a simple, readable manner.
   - Lunch: List items for lunch.
   - Dinner: List items for dinner.
   - Snacks: List items for snacks.
   - Health Notes (if applicable): Any specific instructions or health-related notes for that day.

    **Example Format (with HTML tags formating):**
    ```
    Day 1
    Breakfast:
    - items here 

    Lunch:
    - items here 

    Dinner:
    - items here

    Snacks:
    - items here

    Health Notes: Aim to reduce sodium intake. Choose low-sodium foods and limit added salt.
    ```

    **Generate a response in this clear and organized format for the requested number of days.**
    """
    try:
        # Use Gemini's text generation functionality
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
        )

        # Extract the text from the response
        diet_plan=  response.candidates[0].content.parts[0].text
        return diet_plan, exercise_recommendations

    except Exception as e:
        raise RuntimeError(f"An error occurred while generating the diet plan: {e}")
    




# Analyze Medical Report image
def analyze_medical_report(report_image_path: str) -> str:
    try:
        # Upload the medical report image to Gemini
        uploaded_file = genai.upload_file(report_image_path)

        # Create a professional prompt for medical report analysis
        prompt = f"""
        You are an expert doctor with years of experience in analyzing medical reports. 
        A patient has uploaded their medical report in the form of an image. 
        Your task is to analyze the report thoroughly and provide detailed insights.

        **Analysis Instructions:**
        1. Extract all relevant details from the report, such as test names, values, and reference ranges.
        2. Identify any abnormalities or deviations from normal values.
        3. Provide a summary of the patient's health status based on the report.
        4. Suggest possible actions, if necessary, for the patient (e.g., consult a specialist, lifestyle changes, etc.).

        **Important Notes:**
        - Be professional and concise in your explanation.
        - Ensure accuracy while interpreting the data.
        - Highlight any critical findings prominently.

        Analyze the medical report attached below:
        """

        # Use Gemini model to analyze the medical report image
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([uploaded_file, "\n\n", prompt])

        # Return the actual response
        return response.candidates[0].content.parts[0].text

    except Exception as e:
        # Return a detailed error message
        return f"An error occurred while analyzing the medical report: {str(e)}"


# Food Image section 
def analyze_food_image(image_path: str, diet_plan: str, user_details: dict) -> str:
    try:
        # Upload image to Gemini
        myfile = genai.upload_file(image_path)

        # Create a prompt combining diet plan and user details
        prompt = f"""
        Based on the user's health details and diet plan, analyze the image to determine if the food shown is healthy for the user.

        **User Details:**
        Age: {user_details['age']}
        Height: {user_details['height']} cm
        Weight: {user_details['weight']} kg
        BMI: {user_details['bmi']}
        Diabetes: {'Yes' if user_details['diabetes'] else 'No'}
        Other Health Conditions: {user_details['other_conditions']}

        **Diet Plan:**
        {diet_plan}

        **Image Analysis Request:**
        Check if the food in this image is healthy or unhealthy based on the above details. tell the user concisely. 
        """

        # Use Gemini model to analyze the image
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([myfile, "\n\n", prompt])

        # Extract and return the analysis
        return response.candidates[0].content.parts[0].text

    except Exception as e:
        return f"An error occurred while analyzing the image: {e}"



# Meal  Image analysis based on user details
def image_analysis(age: int, height: float, weight: float, bmi: float, diabetes: bool, other_conditions: str, image_path: str) -> dict:
    # Load exercise video data
    video_data = load_video_data()

    # Logic for exercise video recommendations based on health conditions
    exercise_recommendations = []
    if diabetes:
        exercise_recommendations += video_data.get('diabetes', [])
    if 'heart' in other_conditions.lower():
        exercise_recommendations += video_data.get('heart_health', [])
    if 'obesity' in other_conditions.lower():
        exercise_recommendations += video_data.get('obesity', [])
    if 'joint' in other_conditions.lower():
        exercise_recommendations += video_data.get('joint_mobility', [])
    if not exercise_recommendations:
        exercise_recommendations = video_data.get('general_fitness', [])

    # Upload image and create prompt
    myfile = genai.upload_file(image_path)
    prompt = f"""
    Based on the user's health details analyze the image to determine if the food shown is healthy for the user.
    **User Details:**
    - Age: {age}
    - Height: {height} cm
    - Weight: {weight} kg
    - BMI: {bmi}
    - Diabetes: {'Yes' if diabetes else 'No'}
    - Other Health Conditions: {other_conditions}

    First mention the name of food in the image and then write analysis. Check if the food is healthy or unhealthy based on the above details.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([myfile, "\n\n", prompt])

        return {
            'analysis': response.candidates[0].content.parts[0].text,
            'exercise_recommendations': exercise_recommendations,
        }
    except Exception as e:
        return {'analysis': f"An error occurred: {e}", 'exercise_recommendations': []}
         