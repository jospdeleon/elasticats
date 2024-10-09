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
    from_ = request.form.get('from_', type=int, default=0)
    imageSearch = False;
    filename = '';

    if 'imageQuery' in request.files:
        file = request.files['imageQuery']

        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Process the image as needed
            file.save(filepath)
            imageSearch = True;


    print (f'FORM_DATA: {form_data}')

    knn_query = []

    # add text search
    # if both desc and image, just do desc
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
            'field': 'summary_embedding',
            'query_vector': es.get_text_embedding(textQuery),
            'k': 5,
            'num_candidates': 15,
            **filters,
        })

        knn_query.append({
            'field': 'img_embedding',
            'query_vector': es.get_img_embedding(textQuery),
            'k': 5,
            'num_candidates': 15,
            **filters,
        })
    elif imageSearch:
        search_query = None
        # add knn image if there's image
        knn_query.append({
            'field': 'img_embedding',
            'query_vector': es.get_img_embedding(image_path=filepath),
            'k': 5,
            'num_candidates': 15,
            **filters,
        })
    else:
        search_query = {
            'must': {
                'match_all': {}
            }
        }

    rank = None
    if len(knn_query) > 0 and search_query:
        rank = {
            'rrf': {}
        }

    search_params = {
        'knn': knn_query,
        'from_': from_,
        'size': 5
    }
    print (f'# KNN queries: {len(knn_query)}')
    print (f'KNN QUERIES: {knn_query}')

    if search_query:
        search_params['query'] = {
            'bool': {
                **search_query,
                **filters
            }
        }
        print (f'Search query: {search_params['query']}')

    # Conditionally add the 'rank' parameter
    if rank:
        search_params['rank'] = rank

    results = es.search(**search_params)
    print(f'Total results: {results['hits']['total']['value']}')
    
    return render_template('index.html', results=results['hits']['hits'],
                           query=textQuery, from_=from_,
                           total=results['hits']['total']['value'],
                           form_data=form_data,
                           filename=filename)

@app.route('/display/<filename>')
def display_image(filename):
    # Display the image by passing the filename to the template
    return render_template('index.html', filename=filename)

@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['name']
    paragraphs = document['_source']['summary'].split('\n')
    document = document['_source']
    return render_template('document.html', title=title, paragraphs=paragraphs,
                           document=document)

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
