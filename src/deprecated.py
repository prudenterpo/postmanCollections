import os
import javalang
import json
from datetime import datetime

def find_interfaces(directory):
    interfaces = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java") and not file.endswith("Controller.java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
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
                with open(filepath, 'r') as f:
                    content = f.read()
                    tree = javalang.parse.parse(content)
                    for path, node in tree.filter(javalang.tree.ClassDeclaration):
                        if node.name == class_name:
                            for field in node.fields:
                                for declarator in field.declarators:
                                    class_fields[declarator.name] = field.type.name
    return class_fields

def extract_endpoints(filepath):
    with open(filepath, 'r') as f:
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
            print(f'Checking method: {node.name}')
            for annotation in node.annotations:
                print(f'Annotation found: {annotation.name}')
                if annotation.name in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping', 'RequestMapping']:
                    if annotation.element is not None:
                        elements = annotation.element if isinstance(annotation.element, list) else annotation.element.pair
                        for element in elements:
                            if isinstance(element.value, javalang.tree.Literal):
                                print(f'Element found: {element.name} = {element.value.value}')
                                if element.name == 'method':
                                    endpoint['method'] = element.value.value.upper()
                                if element.name == 'value':
                                    endpoint['url'] = element.value.value.strip('"')
                                elif element.name == 'description':
                                    endpoint['description'] = element.value.value.strip('"')
                            elif isinstance(element.value, javalang.tree.ElementArrayValue):
                                for val in element.value.values:
                                    if isinstance(val, javalang.tree.Literal):
                                        print(f'Element array value found: {val.value}')
                                        if element.name == 'value':
                                            endpoint['url'] = val.value.strip('"')
                                        elif element.name == 'description':
                                            endpoint['description'] = val.value.strip('"')
                            elif isinstance(element.value, javalang.tree.MemberReference):
                                print(f'MemberReference found: {element.value.member}')
                                if element.name == 'method':
                                    endpoint['method'] = element.value.member.upper()
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
        print(f'Endpoints found in {filepath}: {endpoints}')
    return endpoints

def generate_postman_collection(endpoints, output_file, java_directory):
    collection = {
        "info": {
            "name": "Agroforte API Collections",
            "description": "Generated from Java Controllers",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }

    for endpoint in endpoints:
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

        collection['item'].append(item)

    with open(output_file, 'w') as f:
        json.dump(collection, f, indent=2)

# Diretório dos arquivos Java
java_directory = 'C:\\Users\\rodri\\personalProjects\\scripts_python\\api-limit\\src\\main\\java\\br\\com\\meuagroforte'

# Encontrar todas as interfaces
interfaces = find_interfaces(java_directory)
print(f'Interfaces found: {interfaces}')

# Extrair endpoints de todas as interfaces
all_endpoints = []
for interface in interfaces:
    endpoints = extract_endpoints(interface)
    all_endpoints.extend(endpoints)

# Gerar a collection do Postman com timestamp
timestamp = datetime.now().strftime("%Y-%m-%d-H%HM%M")
output_file = f'postman_collection_{timestamp}.json'
generate_postman_collection(all_endpoints, output_file, java_directory)
print(f'Postman collection generated: {output_file}')
