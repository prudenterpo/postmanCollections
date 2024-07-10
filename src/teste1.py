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
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        for annotation in node.annotations:
            if annotation.name in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping', 'RequestMapping']:
                method = annotation.name.replace('Mapping', '').upper()
                if method == 'REQUEST':  # Special case for RequestMapping
                    method = 'GET'  # Default to GET, or change as necessary
                for element in annotation.element:
                    if element.name == 'value':
                        endpoint_url = element.value.value
                        print(f"Found endpoint in {file_path}: {method} {endpoint_url}")  # Depuração
                        endpoints.append({
                            'method': method,
                            'url': endpoint_url
                        })
    return endpoints

def find_class_fields(directory, class_name):
    class_fields = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = javalang.parse.parse(content)
                    for path, node in tree.filter(javalang.tree.ClassDeclaration):
                        if node.name == class_name:
                            for field in node.fields:
                                for declarator in field.declarators:
                                    class_fields[declarator.name] = field.type.name
    return class_fields

def generate_body_from_class_fields(class_fields):
    body = {}
    for field, field_type in class_fields.items():
        if field_type == 'String':
            body[field] = ""
        elif field_type == 'int' or field_type == 'Integer':
            body[field] = 0
        elif field_type == 'boolean' or field_type == 'Boolean':
            body[field] = False
        else:
            body[field] = None
    return json.dumps(body, indent=4)

def process_directory(directory):
    all_endpoints = defaultdict(list)

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                project_name = os.path.basename(os.path.dirname(os.path.dirname(file_path)))  # Capturando o nome da API corretamente
                print(f"Parsing file: {file_path}")  # Depuração
                endpoints = extract_endpoints_from_file(file_path)
                if endpoints:
                    print(f"Found endpoints in {file_path}: {endpoints}")  # Depuração
                    all_endpoints[project_name].extend(endpoints)

    return all_endpoints

def generate_postman_collection(endpoints, output_file, root_directory):
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
            url_parts = endpoint['url'].strip('/').split('/')
            class_name = url_parts[-1].capitalize()  # Assumindo que a última parte da URL é o nome da classe
            class_fields = find_class_fields(root_directory, class_name)
            body = generate_body_from_class_fields(class_fields)
            item = {
                'name': endpoint['url'],
                'request': {
                    'method': endpoint['method'],
                    'header': [],
                    'body': {
                        'mode': 'raw',
                        'raw': body
                    },
                    'url': {
                        'raw': '{{base_url}}' + endpoint['url'],
                        'host': ['{{base_url}}'],
                        'path': url_parts,
                        'query': [],
                        'variable': [
                            {
                                'key': part.strip('{}'),
                                'value': '',
                                'description': 'UUID'
                            } for part in url_parts if part.startswith('{') and part.endswith('}')
                        ]
                    },
                    'description': ''
                },
                'response': []
            }
            folder['item'].append(item)
        postman_collection['item'].append(folder)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(postman_collection, file, indent=4)

if __name__ == '__main__':
    root_directory = 'C:\\Users\\rodri\\personalProjects\\scripts_python\\apis'
    output_file = f'C:\\Users\\rodri\\personalProjects\\scripts_python\\postmanCollections\\output\\postmanTestao_collection_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json'

    all_endpoints = process_directory(root_directory)
    print(f"All endpoints: {all_endpoints}")  # Depuração final
    generate_postman_collection(all_endpoints, output_file, root_directory)
    print(f"Postman collection generated at {output_file}")  # Confirmação final
