# Elasticats! Demonstrating the Power of Elasticsearch

This is a simple Python web app that showcases different types of search that can be implemented in Elastic:
1. Lexical search
2. Vector search on text and image embeddings
3. Hybrid search by combining lexical and vector search

This project is based on the search labs tutorial found [here](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome)

## Prerequisites:

Make sure you have Python3 installed:
* Python
```
$> python -V
Python 3.12.4 // you need at least version 3
```
* Either an Elastic Cloud or self-hosted Elastic deployment. This project was tested in Elastic Cloud v8.14.3.

## Building and Running locally

**Note:** There is a `.env-template` file at the root of the project directory. Create a copy, name it `.env` and fill out the required variables. In a production environment, it is not recommended to check this in version control as it may contain sensitive information.

To build the app, execute the following commands:
```
$> python3 -m venv .venv
$> source .venv/bin/activate
(.venv) $> pip install -r requirements.txt
```
Before you can run the app, you need to index the documents in `data.json` first:
```
(.venv) $> flask reindex
Index with 15 documents created 
```
You can now run and test the app:
```
(.venv) $> flask run
```
1. Visit http://127.0.0.1:5000/. Click "Submit" and it will show you paginated results (15 cats total).
2. You can select any of the filters, combine them with any text in the `description` field or upload a similar image of the cats.
**Note:** Currently, there is a pagination issue where upon doing a subsequent search (after a search), the results don't start from the first page. As a workaround, use the "Reset" button for every search you'd like to test.

![alt text](Search%20flowchart.png)

To stop the app:
```
Press Ctrl-C
(.venv) $> deactivate
```

## Test Scenarios

Given the flowchart above, the scenarios you can test are as follows:
1. Simplest (no filters, no text, no image) - will do a "match all" query
2. Filters only - will do a "bool filter" query
3. Text query (w/o filters) - text search (summary) + vector search (summary) + vector search (image)
4. Image query (w/o filters) - vector search (image)
5. Text query (w/ filters) - filters applied to all text search (summary) + vector search (summary) + vector search (image)
6. Image query (w/ filters) - filters applied to vector search (image)

Here are some sample tests you can use for the description:
1. `sisters` vs `siblings`
2. tuxedo
3. `black cats` with `American shorthair` filter
4. `white`

For the image, you can try these images stored in the images/`<breed>` folder:
1. Abyssinian
- 72245105_3 (Dahlia)
2. American shorthair
- 64635658_2 (Uni)
- 72157682_4 (Sugarplum)
3. Persian
- 72528240_2 (Sugar)

Some interesting cases:
1. Persian
- 72378135_2 (Garth) - multiple cats in the pic
2. Siamese
- 72066684_2 (Gabriel) - he shows up second in the list
3. American shorthair
- 72157682_2 (Sugarplum) - NO MATCH but if I add filters ‘kitten’ and ‘American shorthair’ she shows up as 2nd on the list
