from flask import Flask
from flask import Response, jsonify, request, redirect, url_for

import shelve

import socket
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

    # basic OCR packages 
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract

UPLOAD_FOLDER = './src/uploads'
ALLOWED_EXTENSIONS = set(['pdf', 'docx'])


    #configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
        #print 'upload file'
    try:
        os.stat(app.config['UPLOAD_FOLDER'])
    except:
        os.mkdir(app.config['UPLOAD_FOLDER'])
    if request.method == 'POST':
        file = request.files['file']
            #print 'filename: ' + file.filename

        if file and allowed_file(file.filename):
                #print 'allowing file'
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',filename=filename))
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file>
        <input type=submit value=Upload>
        </form>
        '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if filename.rsplit('.', 1)[1] == "pdf":
        with open(file_path, 'rb') as f:
            check_pdf(f)
        
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def check_pdf(filename):
    text = ""
    file = fitz.open(filename=filename)
    for page in file:
        text += page.get_text()
    print("Extracted text:\n", text)

if __name__ == '__main__':

    app.run(host='0.0.0.0')