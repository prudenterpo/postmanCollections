import os
import json
import javalang
import datetime
from collections import defaultdict

def extract_endpoints_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        try:
            tree = javalang.parse.parse(content)
        except javalang.parser.JavaSyntaxError as e:
            print(f"Failed to parse {file_path}: {e}")
            return []

    endpoints = []
    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        if node.annotations:
            for annotation in node.annotations:
                if annotation.name in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping', 'RequestMapping']:
                    method = annotation.name.replace('Mapping', '').upper()
                    if method == 'REQUEST':  # Special case for RequestMapping
                        for element in annotation.element:
                            if element.name == 'method':
                                method = element.value.value if hasattr(element.value, 'value') else element.value.member
                    for element in annotation.element:
                        if element.name == 'value':
                            endpoint_url = element.value.value if hasattr(element.value, 'value') else element.value.member
                            endpoints.append({
                                'method': method,
                                'url': endpoint_url
                            })
    return endpoints

def process_directory(directory):
    all_endpoints = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                project_name = file_path.split(os.sep)[-3]  # Ajuste para obter o nome correto da API
                print(f"Parsing file: {file_path}")
                endpoints = extract_endpoints_from_file(file_path)
                if endpoints:
                    print(f"Found endpoints in {file_path}: {endpoints}")
                    all_endpoints[project_name].extend(endpoints)
    return all_endpoints

def generate_postman_collection(endpoints, output_file):
    postman_collection = {
        'info': {
            'name': 'Agroforte API Collections',
            'description': 'Generated from Java Controllers',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        },
        'item': []
    }

    for project_name, project_endpoints in endpoints.items():
        folder = {
            'name': project_name,
            'item': []
        }
        for endpoint in project_endpoints:
            item = {
                'name': endpoint['url'],
                'request': {
                    'method': endpoint['method'],
                    'header': [],
                    'body': {
                        'mode': 'raw',
                        'raw': ''
                    },
                    'url': {
                        'raw': '{{base_url}}' + endpoint['url'],
                        'host': ['{{base_url}}'],
                        'path': endpoint['url'].strip('/').split('/')
                    },
                    'description': ''
                }
            }
            folder['item'].append(item)
        postman_collection['item'].append(folder)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(postman_collection, file, indent=4)

if __name__ == '__main__':
    root_directory = 'C:\\Users\\rodri\\personalProjects\\scripts_python\\apis'
    output_file = f'C:\\Users\\rodri\\personalProjects\\scripts_python\\postmanCollections\\output\\postman_collection_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json'

    all_endpoints = process_directory(root_directory)
    print(f"All endpoints: {all_endpoints}")
    generate_postman_collection(all_endpoints, output_file)
    print(f"Postman collection generated at {output_file}")
