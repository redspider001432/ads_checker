from flask import Flask, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import joblib
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
import pandas as pd
import re
import skillNer
from transformers import pipeline
UPLOAD_FOLDER = './src/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MODEL_PATH = './src/name_model.joblib'
DATASET_PATH = './src/names_dataset.csv'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_model():
    """Initialize or load the classification model"""
    if os.path.exists(MODEL_PATH):
        vectorizer, model = joblib.load(MODEL_PATH)
    else:
        # Initialize with dummy data for two classes
        vectorizer = HashingVectorizer(n_features=2**18, alternate_sign=False)
        model = PassiveAggressiveClassifier()
        
        # Initial training data with valid/invalid examples
        X = vectorizer.fit_transform([
            "John Doe",     # Valid name (class 1)
            "XXinvalidXX"   # Invalid pattern (class 0)
        ])
        y = [1, 0]  # 1=valid, 0=invalid
        
        model.fit(X, y)
        joblib.dump((vectorizer, model), MODEL_PATH)
    
    return vectorizer, model

def update_model(first_name, last_name):
    """Update model with new name data"""
    # Save to dataset
    new_entry = pd.DataFrame([[first_name, last_name]], 
                           columns=['first_name', 'last_name'])
    if os.path.exists(DATASET_PATH):
        new_entry.to_csv(DATASET_PATH, mode='a', header=False, index=False)
    else:
        new_entry.to_csv(DATASET_PATH, index=False)
    
    # Prepare training data
    vectorizer, model = get_model()
    valid_name = f"{first_name} {last_name}"
    invalid_name = f"xxx{first_name}xxx"  # Synthetic invalid pattern
    
    X = vectorizer.transform([valid_name, invalid_name])
    y = [1, 0]  # 1=valid, 0=invalid
    
    # Update model incrementally
    model.partial_fit(X, y, classes=[0, 1])
    joblib.dump((vectorizer, model), MODEL_PATH)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        if not first_name or not last_name:
            return "Both names are required", 400

        file = request.files['file']
        if file and allowed_file(file.filename):
            # Generate safe filename
            ext = secure_filename(file.filename).split('.')[-1]
            base_name = f"{secure_filename(first_name)}_{secure_filename(last_name)}"
            filename = f"{base_name}.{ext}"
            
            # Handle duplicates
            counter = 1
            while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                filename = f"{base_name}_{counter}.{ext}"
                counter += 1
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Train model with new data
            update_model(first_name, last_name)
            
            return redirect(url_for('uploaded_file', filename=filename))

    return '''
        <!doctype html>
        <title>Upload File</title>
        <h1>Upload Resume</h1>
        <form method=post enctype=multipart/form-data>
            First Name: <input type=text name=first_name required><br>
            Last Name: <input type=text name=last_name required><br>
            File: <input type=file name=file accept=".pdf,.docx" required><br>
            <input type=submit value=Upload>
        </form>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if filename.endswith('.pdf'):
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
            print(text)
            
            # Email detection
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if emails:
                print(f"Found emails: {', '.join(emails)}")
    
    return f"File {filename} processed successfully! Names added to training data."

def extract_skills(text):
    skill_extractor = pipeline(
    "token-classification",
    model="michiyasunaga/BioLinkBERT-base-skill-extraction",
    aggregation_strategy="simple"
    )
    text = text
    skills = [x['word'] for x in skill_extractor(text) if x['entity_group'] == 'SKILL']
    print(skills)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)