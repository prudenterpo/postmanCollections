import os
import javalang
import json
import requests


def find_controllers(directory):
    controllers = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    tree = javalang.parse.parse(content)
                    for path, node in tree.filter(javalang.tree.Annotation):
                        if node.name == 'RestController' or node.name == 'Controller':
                            controllers.append(filepath)
    return controllers


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
            for annotation in node.annotations:
                if annotation.name in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping', 'RequestMapping']:
                    endpoint['method'] = annotation.name.replace('Mapping', '').upper()
                    if annotation.element is not None:
                        for element in annotation.element.pair:
                            if element.name == 'value':
                                endpoint['url'] = element.value.value
                            elif element.name == 'description':
                                endpoint['description'] = element.value.value
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

    for endpoint in endpoints:
        item = {
            "name": endpoint['description'],
            "request": {
                "method": endpoint['method'],
                "header": [],
                "url": {
                    "raw": f"{{{{base_url}}}}{endpoint['url']}",
                    "host": ["{{base_url}}"],
                    "path": endpoint['url'].strip('/').split('/')
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
                item['request']['url']['variable'] = [{
                    "key": param['name'],
                    "value": "",
                    "description": param['type']
                }]
            elif 'RequestParam' in param['annotations']:
                item['request']['url']['query'] = [{
                    "key": param['name'],
                    "value": "",
                    "description": param['type']
                }]
            elif 'RequestHeader' in param['annotations']:
                item['request']['header'].append({
                    "key": param['name'],
                    "value": "",
                    "description": param['type']
                })

        collection['item'].append(item)

    with open(output_file, 'w') as f:
        json.dump(collection, f, indent=2)


# def update_postman_collection(api_key, collection_uid, postman_collection):
#     url = f"https://api.getpostman.com/collections/{collection_uid}"
#     headers = {
#         'X-Api-Key': api_key,
#         'Content-Type': 'application/json'
#     }
#     data = json.dumps({"collection": postman_collection})
#     response = requests.put(url, headers=headers, data=data)
#     return response.json()

java_directory = 'C:\\Users\\rodri\\personalProjects\\scripts_python\\api-limit\\src\\main\\java\\br\\com\\meuagroforte\\limit\\controller'
# api_key = 'sua_api_key_do_postman'
# collection_uid = 'uid_da_sua_collection'

controllers = find_controllers(java_directory)

all_endpoints = []
for controller in controllers:
    endpoints = extract_endpoints(controller)
    all_endpoints.extend(endpoints)

output_file = 'postman_collection.json'
generate_postman_collection(all_endpoints, output_file)
print(f'Postman collection generated: {output_file}')

# Atualizar Collection no Postman
# with open(output_file, 'r') as f:
#     postman_collection = json.load(f)
# response = update_postman_collection(api_key, collection_uid, postman_collection)
# print(response)
