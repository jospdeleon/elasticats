from flask import Flask, request, render_template, redirect, url_for
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    # Check if the request has the text part
    if query:
        return render_template('index.html', query=query)
    else:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process the image as needed
            # For demonstration, just display the uploaded image
            return redirect(url_for('display_image', filename=filename))
    
    return render_template('index.html')

@app.route('/display/<filename>')
def display_image(filename):
    # Display the image by passing the filename to the template
    return render_template('index.html', filename=filename)

if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
