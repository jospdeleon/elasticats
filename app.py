import ast
from flask import Flask, request, render_template, redirect, session, url_for
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
    form_data = request.form.to_dict(flat=False)
    filters = extract_filters(form_data)
    textQuery = request.form.get('inputQuery', '')
    # file = request.files['imageQuery']
    from_ = request.form.get('from_', type=int, default=0)

    print (f'FORM_DATA: {form_data}')
    # print (f'age_list: {age_list}')
    # print (f'breed_list: {breed_list}')

    knn_query = []

    # add text search
    if textQuery:
        search_query = {
            'must': {
                'match': {
                    'summary': textQuery
                }
            }
        }

        # add knn text and image search if there's a description
        knn_query.append({
            'field': 'text_embedding',
            'query_vector': es.get_text_embedding(textQuery),
            'k': 5,
            'num_candidates': 10,
            **filters,
        })

        knn_query.append({
            'field': 'img_embedding',
            'query_vector': es.get_img_embedding(textQuery),
            'k': 5,
            'num_candidates': 10,
            **filters,
        })
    else:
        search_query = {
            'must': {
                'match_all': {}
            }
        }

    # add knn image if there's image
    # if both desc and image, just do desc

    rank = None
    if len(knn_query) > 0:
        rank = {
            'rrf': {}
        }

    search_params = {
        'query': {
            'bool': {
                **search_query,
                **filters
            }
        },
        'knn': knn_query,
        'from_': from_,
        'size': 5
    }

    # Conditionally add the 'rank' parameter
    if rank:
        search_params['rank'] = rank

    print (f'Search query: {search_params['query']}')
    results = es.search(**search_params)
    print(f'Total results: {results['hits']['total']['value']}')

    # Check if the request has the text part
    # if textQuery:
    #     return render_template('index.html', query=textQuery)
    # else:
    #     # Check if the post request has the file part
    #     if 'imageQuery' not in request.files:
    #         return redirect(request.url)
    #     file = request.files['imageQuery']
    #     # If the user does not select a file, the browser submits an empty part without filename
    #     if file.filename == '':
    #         return redirect(request.url)
    #     if file:
    #         filename = file.filename
    #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #         file.save(filepath)
    #         # Process the image as needed
    #         # For demonstration, just display the uploaded image
    #         return redirect(url_for('display_image', filename=filename))
    
    return render_template('index.html', results=results['hits']['hits'],
                           query=textQuery, from_=from_,
                           total=results['hits']['total']['value'],
                           form_data=form_data)

@app.route('/display/<filename>')
def display_image(filename):
    # Display the image by passing the filename to the template
    return render_template('index.html', filename=filename)

@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['name']
    paragraphs = document['_source']['content'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)

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

def extract_filters(form_data):
    filters = []

    for key, val in form_data.items():
        if (key == "imageQuery" or key == "inputQuery" or key == "from_"):
            continue

        if (key != "age" and key != "breed"):
            if (val[0] != ''): #only apply the filter if value is not empty
                filters.append({
                    "term": {
                        f"{key}": {
                            "value": val[0]
                        }
                    },
                })
        else:
            #remove any empty values first
            cleaned_list = [item for item in val if item]

            if (len(cleaned_list) > 0): #only apply the filter if list is not empty
                filters.append({
                    "terms": {
                        f"{key}": cleaned_list
                    },
                })
                
    return {'filter': filters}
