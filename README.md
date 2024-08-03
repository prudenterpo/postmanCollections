# Postman Collections Generator 

## Overview
This project automates the generation of Postman collections searching through all Java controller files among Agroforte API's. It parses endpoint information and organizes this data into a Postman collection structure. 

## Python Version
Make sure you have Python 3.x installed. This project has been tested with Python 3.x, and using other versions may cause compatibility issues.

## Environment Setup
To run this project, set up the environment variables by creating a `.env` file in the project root directory. Use the template below to create your `.env` file:

```plaintext
JAVA_DIRECTORY=C:\\Path\\To\\Your\\Java\\Source
POSTMAN_COLLECTIONS_OUTPUT_PATH=C:\\Path\\To\\Your\\Output\\Directory
POSTMAN_API_KEY=Your_Postman_Api_Key
POSTMAN_COLLECTION_UID=Your_Postman_Collection_Uid
```

## Activating the Virtual Environment
Activate the virtual environment using the appropriate command for your operating system:

Windows:
```bash
venv\Scripts\activate
```

macOS and Linux:
```bash
source venv/bin/activate
```


## Installing Dependencies
With the virtual environment activated, install the project dependencies by executing:
```bash
pip install -r requirements.txt
```

## Running the Update Script

The `update_script.sh` script automates the process of updating multiple Git repositories and executing the Python script to generate Postman collections.

### Prerequisites
Make sure you have Git Bash installed on Windows, or use the default terminal on macOS/Linux.

### Script Permissions

Before running the script, ensure it has the appropriate execution permissions. You can set the permissions by running the following command in the terminal:

```bash
chmod +x scripts/update_script.sh
```

### Running the Script
To run the script, navigate to the postman_collections directory and execute the following command:
```bash
./scripts/update_script.sh
```

