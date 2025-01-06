# exercise_videos.py
import pandas as pd

def load_video_data():
    # Load dataset from a CSV file
    df = pd.read_csv(r'D:\AI Projects\fitness-ai-app\fitness exercises.csv')  # Assuming the CSV file is in the same folder
    
    # Convert to a dictionary for easy access
    video_data = {
        'diabetes': [],
        'heart_health': [],
        'general_fitness': [],
        'joint_mobility': [],
        'obesity': []
    }
    
    # Categorize videos based on title
    for index, row in df.iterrows():
        if 'diabetes' in row['Titles'].lower():
            video_data['diabetes'].append({"title": row['Titles'], "url": row['URL']})
        if 'heart' in row['Titles'].lower():
            video_data['heart_health'].append({"title": row['Titles'], "url": row['URL']})
        if 'fitness' in row['Titles'].lower() or 'exercise' in row['Titles'].lower():
            video_data['general_fitness'].append({"title": row['Titles'], "url": row['URL']})
        if 'joint' in row['Titles'].lower():
            video_data['joint_mobility'].append({"title": row['Titles'], "url": row['URL']})
        if 'obesity' in row['Titles'].lower():
            video_data['obesity'].append({"title": row['Titles'], "url": row['URL']})

    return video_data
