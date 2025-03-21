from __future__ import division, print_function
from flask import Flask, render_template, request,session,logging,flash,url_for,redirect,jsonify,Response
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
import numpy as np
#model
import sys
import os
import glob
# import re
import numpy as np
import tensorflow as tf
import tensorflow as tf


from sqlalchemy.exc import SQLAlchemyError
from flask import session, render_template, request, flash
# from tensorflow.compat.v1 import ConfigProto
# from tensorflow.compat.v1 import InteractiveSession

from tensorflow.keras.applications.resnet50 import preprocess_input
# from tensorflow.keras.models import load_model
from tensorflow import keras
from tensorflow.keras.preprocessing import image
from tensorflow.python.keras.models import load_model
# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

MODEL_PATH = 'blooddisease.h5'
model = keras.models.load_model('blooddisease.h5')  


local_server = True
app = Flask(__name__,template_folder='template')
app.secret_key = 'super-secret-key'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = params['gmail_user']
app.config['MAIL_PASSWORD'] = params['gmail_password']
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Register(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	fname=db.Column(db.String(50),nullable=False)
	lname=db.Column(db.String(50),nullable=False)
	email=db.Column(db.String(50),nullable=False)
	password=db.Column(db.String(50),nullable=False)

class Contact(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    Name=db.Column(db.String(50),nullable=False)
    Email=db.Column(db.String(50),nullable=False)
    Subject =db.Column(db.String(50),nullable=False)
    Message=db.Column(db.String(50),nullable=False)    


@app.route("/register",methods=['GET','POST'])
def register():
	if(request.method=='POST'):
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		email=request.form.get('email')
		password=request.form.get('password')
		entry=Register(fname=fname,lname=lname,email=email,password=password)
		db.session.add(entry)
		db.session.commit()
	return render_template('register.html',params=params)

@app.route("/contact",methods=['GET','POST'])
def contact():
   
    if(request.method=='POST'):
        Name=request.form.get('Name')
        Email=request.form.get('Email')
        Subject =request.form.get('Subject')
        Message=request.form.get('Message')
        entry=Contact(Name=Name,Email=Email,Subject=Subject,Message=Message)
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html',params=params)

	


@app.route("/")
def Home():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'email' in session and session['email']:
            return render_template('bloodcell.html', params=params)
        else:
            return render_template('login.html', params=params)

    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]

        try:
            # Fetch user from the database by email
            login = Register.query.filter_by(email=email).first()

            # Check if user exists and password matches
            if login and login.password == password:
                session['email'] = email
                return render_template('bloodcell.html', params=params)
            else:
                flash("Incorrect email or password", "danger")
        
        except SQLAlchemyError as e:
            flash("Database error occurred. Please try again.", "danger")
            print("Database error:", e)

    return render_template('login.html', params=params)



@app.route("/logout", methods = ['GET','POST'])
def logout():
    session.pop('email')
    return redirect(url_for('Home')) 


   
@app.route("/bloodcell", methods=['GET','POST'])
def bloodcell():
    return render_template('bloodcell.html', params=params)



def model_predict(img_path, model):
    print(f"Processing image: {img_path}")
    
    # Load and preprocess the image
    img = image.load_img(img_path, target_size=(60, 60))
    x = image.img_to_array(img)
    x = x / 255.0  # Correct scaling
    x = np.expand_dims(x, axis=0)

    # Model prediction
    preds = model.predict(x)
    
    if preds is None or len(preds) == 0:
        return "Unknown Disease"  # Handle cases where no prediction is made

    label = np.argmax(preds, axis=1).item()  # Convert to integer

    # Mapping labels to diseases
    disease_dict = {
        0: "Leukemia",
        1: "Sickle Cell Anemia",
        2: "Malaria",
        3: "Myeloma"
    }

    return disease_dict.get(label, "Unknown Disease")  # Default to "Unknown Disease" if label is invalid



@app.route('/predict', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save uploaded file
        basepath = os.path.dirname(__file__)
        upload_folder = os.path.join(basepath, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)  # Ensure directory exists
        file_path = os.path.join(upload_folder, secure_filename(f.filename))
        f.save(file_path)

        # Get prediction
        result = model_predict(file_path, model)

        if not result or result == "Unknown Disease":
            return jsonify({"error": "Prediction failed", "disease": "Unknown Disease"}), 500

        response_data = {"disease": result}
        print("Response:", response_data)  # Debugging log
        return jsonify(response_data)

    except Exception as e:
        print(f"Error during prediction: {e}")  # Debugging log
        return jsonify({"error": "Internal server error"}), 500

@app.route('/services')
def services():
    return render_template('services.html')








app.run(debug=True)    