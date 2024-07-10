import os
import javalang
import json
import datetime
from dotenv import load_dotenv

load_dotenv()


def find_interfaces(directory):
    interfaces = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java") and not file.endswith("Controller.java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = javalang.parse.parse(content)
                    for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                        interfaces.append(filepath)
    return interfaces


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


def extract_endpoints(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        tree = javalang.parse.parse(content)
        endpoints = []
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            endpoint = {
                'method': '',
                'url': '',
                'description': '',
                'parameters': []
            }
            method = ''
            for annotation in node.annotations:
                if annotation.name in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping', 'RequestMapping']:
                    method = annotation.name.replace('Mapping', '').upper()
                    if method == 'REQUEST':
                        method = 'GET'
                    if annotation.element is not None:
                        elements = annotation.element if isinstance(annotation.element,
                                                                    list) else annotation.element.pair
                        for element in elements:
                            if isinstance(element.value, javalang.tree.Literal):
                                if element.name == 'value':
                                    endpoint['url'] = element.value.value.strip('"')
                                elif element.name == 'method':
                                    endpoint['method'] = element.value.value.strip('"').upper()
                            elif isinstance(element.value, javalang.tree.MemberReference):
                                if element.name == 'value':
                                    endpoint['url'] = element.value.member
                                elif element.name == 'method':
                                    endpoint['method'] = element.value.member.upper()
            if not endpoint['method']:
                endpoint['method'] = method

            for param in node.parameters:
                param_info = {
                    'name': param.name,
                    'type': param.type.name,
                    'annotations': []
                }
                for annotation in param.annotations:
                    param_info['annotations'].append(annotation.name)
                endpoint['parameters'].append(param_info)
            if endpoint['method'] and endpoint['url']:
                endpoints.append(endpoint)
    return endpoints


def generate_postman_collection(endpoints, output_file):
    collection = {
        "info": {
            "name": "Agroforte API Collections",
            "description": "Generated from Java Controllers",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }

    for api_name, api_endpoints in endpoints.items():
        folder = {
            "name": api_name,
            "item": []
        }
        for endpoint in api_endpoints:
            name = endpoint['description'] if endpoint['description'] else endpoint['url']
            item = {
                "name": name,
                "request": {
                    "method": endpoint['method'],
                    "header": [],
                    "url": {
                        "raw": f"{{{{base_url}}}}{endpoint['url']}",
                        "host": ["{{base_url}}"],
                        "path": endpoint['url'].strip('/').split('/'),
                        "query": [],
                        "variable": []
                    },
                    "body": {
                        "mode": "raw",
                        "raw": ""
                    }
                },
                "response": []
            }

            for param in endpoint['parameters']:
                if 'PathVariable' in param['annotations']:
                    item['request']['url']['variable'].append({
                        "key": param['name'],
                        "value": "",
                        "description": param['type']
                    })
                elif 'RequestParam' in param['annotations']:
                    item['request']['url']['query'].append({
                        "key": param['name'],
                        "value": "",
                        "description": param['type']
                    })
                elif 'RequestHeader' in param['annotations']:
                    item['request']['header'].append({
                        "key": param['name'],
                        "value": "",
                        "description": param['type']
                    })
                elif 'RequestBody' in param['annotations']:
                    class_fields = find_class_fields(java_directory, param['type'])
                    body_content = {field: "" for field in class_fields.keys()}
                    item['request']['body']['raw'] = json.dumps(body_content, indent=2)

            folder['item'].append(item)
        collection['item'].append(folder)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2)


java_directory = os.getenv('JAVA_DIRECTORY')

postman_collections_base_path = os.getenv('POSTMAN_COLLECTIONS_OUTPUT_PATH')

subfolders = [f.path for f in os.scandir(java_directory) if f.is_dir()]

all_endpoints = {}

for subfolder in subfolders:
    api_name = os.path.basename(subfolder)
    interfaces = find_interfaces(subfolder)
    print(f'Interfaces found in {api_name}: {interfaces}')

    api_endpoints = []
    for interface in interfaces:
        endpoints = extract_endpoints(interface)
        api_endpoints.extend(endpoints)

    all_endpoints[api_name] = api_endpoints

timestamp = datetime.datetime.now().strftime("%Y-%m-%d-H%HM%M")

output_file = f'{postman_collections_base_path}\\postman_collection_{timestamp}.json'

generate_postman_collection(all_endpoints, output_file)

print(f'Postman collection generated: {postman_collections_base_path}')
