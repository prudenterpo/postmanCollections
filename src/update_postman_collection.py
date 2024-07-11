import requests
import json
import os
from dotenv import load_dotenv


def update_postman_collection(collection_json_path):

    load_dotenv()
    api_key = os.getenv('POSTMAN_API_KEY')
    collection_uid = os.getenv('POSTMAN_COLLECTION_UID')

    with open(collection_json_path, 'r') as file:
        updated_collection_data = json.load(file)

    api_details = {
        'url': f'https://api.getpostman.com/collections/{collection_uid}',
        'headers': {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        },
        'payload': {
            'collection': updated_collection_data
        }
    }

    response = requests.put(api_details['url'], headers=api_details['headers'], data=json.dumps(api_details['payload']))

    if response.status_code == 200:
        print('Success updating Postman Collection!')
    else:
        print(f'ERROR updating Postman Collection: {response.status_code}')
        print(response.text)
