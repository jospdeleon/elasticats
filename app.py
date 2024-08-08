from flask import Flask, request, render_template, redirect, url_for
from PIL import Image
import os
from search import Search
import click

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

es = Search()

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

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print (response)
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds.')

@app.cli.command()
@click.argument("query")
def test_embed(query):
    """Test embeddings."""
    response = es.test_get_embeddings(query)
    flattened_array = response['img'].flatten()
    print("Img embedding: ", end="\n")
    print(', '.join(map(str, flattened_array)), end="\n")
    print("Text embedding: ", end="\n")
    flattened_array = response['text'].flatten()
    print(', '.join(map(str, flattened_array)))
