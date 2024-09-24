import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from PIL import Image

load_dotenv()

class Search:
    index=os.getenv("ES_INDEX", "my-cats")

    def __init__(self):        
        self.img_model = SentenceTransformer('clip-ViT-B-32')
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.es = Elasticsearch(cloud_id="rema-test-deployment:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJDFhOWEyYTkyYzkwOTQ1ZTM5YTQwMzE1YmYzZmFlYjMxJDcwMDExNTFiMjM3YzRmZThhNTEwNDFjMmIzYjdiYWRj",
                                api_key="R25oRnVKRUJCWkIzNlZFQzBHcmI6aUk1dmU2VmRTNU8xRG9Tc0pCNjhoZw==")
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        pprint(client_info.body)

    def create_index(self):
        self.es.indices.delete(index=self.index, ignore_unavailable=True)
        self.es.indices.create(
            index=self.index,
            mappings= {
                "properties": {
                    "img_embedding": {
                        "type": "dense_vector",
                        "dims": 512,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "photo": {
                        "type": "keyword"
                    },
                    "cat_id": {
                        "type": "keyword"
                    },
                    "name": {
                        "type" : "text"
                    },
                    "url" : {
                        "type" : "keyword"
                    },
                    "summary" : {
                        "type" : "text"
                    },
                    "text_embedding": {
                        "type": "dense_vector",
                        "dims": 384
                    },
                    "age": {
                        "type": "keyword"
                    },
                    "gender": {
                        "type": "keyword"
                    },
                    "size": {
                        "type": "keyword"
                    },
                    "coat": {
                        "type": "keyword"
                    },
                    "breed": {
                        "type": "keyword",
                        "copy_to": "tags"
                    },
                    "tags": {
                        "type": "keyword"
                   }

                }
            }
        )

    def get_img_embedding(self, text='', image_path=''):
        if text:
            print(f'Encoding text: {text}')
            return self.img_model.encode(text)
        else:
            print(f'Encoding image: {image_path}')
            temp_image = Image.open(image_path)
            return self.img_model.encode(temp_image)

    def get_text_embedding(self, text):
        return self.text_model.encode(text)

    def insert_document(self, document):
        return self.es.index(index=self.index, document={
            **document,
            'img_embedding': self.get_img_embedding(image_path="static/"+document['photo']),
            'text_embedding': self.get_text_embedding(document['summary'])
        })

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': self.index}})
            operations.append({
                **document,
                'img_embedding': self.get_img_embedding(image_path="static/"+document['photo']),
                'text_embedding': self.get_text_embedding(document['summary'])
            })
        return self.es.bulk(operations=operations)

    def reindex(self):
        self.create_index()
        with open('data.json', 'rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)
    
    def test_get_embeddings(self, query):
        img_emb = self.img_model.encode(
            [query]
        )

        text_emb = self.text_model.encode(
            [query]
        )
        return {'img': img_emb, 'text': text_emb}

    def search(self, **query_args):
        return self.es.search(index=self.index, **query_args)

        # sub_searches is not currently supported in the client, so we send
        # search requests using the body argument
        # if "from_" in query_args:
        #     query_args["from"] = query_args["from_"]
        #     del query_args["from_"]
        # print ("SEARCH")
        # print(query_args["query"])
        # return self.es.search(
        #     index="my_documents",
        #     body=json.dumps(query_args),
        # )

    def retrieve_document(self, id):
        return self.es.get(index=self.index, id=id)
