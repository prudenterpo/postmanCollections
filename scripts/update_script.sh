#!/bin/bash

apis_directory="../apis"

if [ ! -d "$apis_directory" ]; then
    echo "Error: Directory $apis_directory does not exist."
    exit 1
fi

for dir in "$apis_directory"/*; do
    if [ -d "$dir" ]; then
        echo "Navigating to $dir"
        cd "$dir" || { echo "Error: Failed to navigate to $dir"; exit 1; }

        echo "Running git checkout master in $(basename "$dir")"
        git checkout master || { echo "Error: Failed to run git checkout master in $dir"; exit 1; }

        echo "Running git pull in $(basename "$dir")"
        git pull || { echo "Error: Failed to run git pull in $dir"; exit 1; }

        cd - > /dev/null || { echo "Error: Failed to return to previous directory from $dir"; exit 1; }
    else
        echo "Warning: $dir is not a directory, skipping."
    fi
done

python_script="/Users/rodrigooliveira/af_projects/scripts/postmanCollections/src/main.py"

#if [ ! -f "$python_script" ]; then
#    echo "Error: Python script $python_script does not exist."
#    exit 1
#fi

echo "Executing Python script: $python_script"
python3 "$python_script" || { echo "Error: Failed to execute Python script $python_script"; exit 1; }

echo "Script execution completed"
