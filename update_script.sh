#!/bin/bash

directories=("src" "repo2" "repo3")

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "Navigating to $dir"
        cd "$dir"

        echo "Running git checkout master"
        git checkout master

        echo "Running git pull"
        git pull

        cd ..
    else
        echo "Directory $dir does not exist"
    fi
done

python_script="src/generate_postman_collection.py"
echo "Executing Python script: $python_script"
python "$python_script"

echo "Script execution completed"
