import os
import javalang
import json
import datetime
import logging
from dotenv import load_dotenv
import update_postman_collection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

start_time = datetime.datetime.now()
logging.info(f'Script started at {start_time.strftime("%Y-%m-%d %H:%M:%S")}')


def find_interfaces(directory):
    logging.info(f'Searching for interfaces in directory: {directory}')
    interfaces = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if "controller" in root.lower() and file.endswith(".java") and not file.endswith("Controller.java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        tree = javalang.parse.parse(content)
                        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                            interfaces.append(filepath)
                            logging.info(f'Interface found: {filepath}')
                    except javalang.parser.JavaSyntaxError:
                        logging.warning(f'Error parsing file: {filepath}')
    return interfaces


def find_class_fields(directory, class_name, processed_classes=None):
    logging.info(f'Searching for fields in class: {class_name}')

    if processed_classes is None:
        processed_classes = set()

    basic_types = {'String', 'Integer', 'Long', 'Boolean', 'BigDecimal', 'Double', 'Float', 'LocalDate', 'Date'}

    if class_name in processed_classes or class_name in basic_types:
        return {}

    processed_classes.add(class_name)

    class_fields = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        tree = javalang.parse.parse(content)
                        for path, node in tree.filter(javalang.tree.ClassDeclaration):
                            if node.name == class_name:
                                logging.info(f'Class found: {class_name} in file {filepath}')
                                for field in node.fields:
                                    for declarator in field.declarators:
                                        field_type = field.type.name
                                        if isinstance(field.type, javalang.tree.ReferenceType) and field.type.arguments:
                                            field_type = field.type.name + '<' + ','.join([arg.type.name for arg in field.type.arguments]) + '>'

                                        if field.type.name in ['List', 'Set']:
                                            element_type = field.type.arguments[0].type.name
                                            class_fields[declarator.name] = [find_class_fields(directory, element_type, processed_classes)]
                                        elif field.type.name == 'Map':
                                            class_fields[declarator.name] = {}
                                        else:
                                            class_fields[declarator.name] = find_class_fields(directory, field.type.name, processed_classes)

                                        if not class_fields[declarator.name]:
                                            class_fields[declarator.name] = field_type
                    except javalang.parser.JavaSyntaxError:
                        logging.warning(f'Error parsing file: {filepath}')
    return class_fields


def extract_endpoints(filepath):
    logging.info(f'Extracting endpoints from file: {filepath}')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
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
                            elements = annotation.element if isinstance(annotation.element, list) else annotation.element.pair
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
                    logging.info(f'Endpoint found: {endpoint["method"]} {endpoint["url"]}')
                    endpoints.append(endpoint)
        except javalang.parser.JavaSyntaxError:
            logging.warning(f'Error parsing file: {filepath}')
    return endpoints


def generate_postman_collection(endpoints, output_file):
    logging.info(f'GENERATING POSTMAN COLLECTION IN FILE: {output_file}')
    collection = {
        "info": {
            "name": "MAIN - test 4 main.py",
            "description": "Generated from Java Controllers",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }

    def get_default_value(field_type):
        if field_type in ['String']:
            return ""
        elif field_type in ['BigDecimal', 'Double', 'Float']:
            return 0.0
        elif field_type in ['Integer', 'Long']:
            return 0
        elif field_type in ['Boolean']:
            return False
        elif field_type in ['LocalDate', 'Date']:
            return "1970-01-01"
        else:
            return {}

    def generate_body_content(class_fields):
        body_content = {}
        for field, value in class_fields.items():
            if isinstance(value, list):
                body_content[field] = [generate_body_content(value[0])]
            elif isinstance(value, dict):
                body_content[field] = generate_body_content(value)
            else:
                body_content[field] = get_default_value(value)
        return body_content

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
                    body_content = generate_body_content(class_fields)
                    item['request']['body']['raw'] = json.dumps(body_content, indent=2)

            folder['item'].append(item)
        collection['item'].append(folder)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2)
    logging.info(f'Postman collection successfully generated: {output_file}')


java_directory = os.getenv('JAVA_DIRECTORY')
postman_collections_base_path = os.getenv('POSTMAN_COLLECTIONS_OUTPUT_PATH')

subfolders = [f.path for f in os.scandir(java_directory) if f.is_dir()]

all_endpoints = {}

for subfolder in subfolders:
    api_name = os.path.basename(subfolder)
    interfaces = find_interfaces(subfolder)

    api_endpoints = []
    for interface in interfaces:
        endpoints = extract_endpoints(interface)
        api_endpoints.extend(endpoints)

    all_endpoints[api_name] = api_endpoints

timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
output_file = os.path.join(postman_collections_base_path, f'postman_collection_{timestamp}.json')

generate_postman_collection(all_endpoints, output_file)

logging.info(f'Starting Postman collection update')
update_postman_collection.update_postman_collection(output_file)

end_time = datetime.datetime.now()
elapsed_time = end_time - start_time
logging.info(f'Script finished at {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
logging.info(f'Total execution time: {elapsed_time}')

