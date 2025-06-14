#!/bin/bash

# Define the output configuration file name
CONFIG_FILE="ollama_context.cfg"

# Start creating the JSON file with an opening brace
echo "{" > "$CONFIG_FILE"

# Flag to handle commas between JSON entries
FIRST_MODEL=true

# Get a list of all Ollama models and iterate through them
# 'tail -n +2' skips the header line from 'ollama list'
# 'awk '{print $1}' extracts the model name (first column)
ollama list | tail -n +2 | awk '{print $1}' | while read -r model_name; do
    # Check if the model name is not empty
    if [ -n "$model_name" ]; then
        echo "Processing model: $model_name"

        # Run 'ollama show' for the current model
        # 'grep "context length"' finds the line containing the context length
        # 'awk '{print $NF}'' extracts the last field (the numeric value)
        CONTEXT_LENGTH=$(ollama show "$model_name" | grep "context length" | awk '{print $NF}')

        # If a context length was found
        if [ -n "$CONTEXT_LENGTH" ]; then
            # Add a comma before the entry if it's not the first model
            if [ "$FIRST_MODEL" = false ]; then
                echo "," >> "$CONFIG_FILE"
            fi
            # Append the model name and its context length to the JSON file
            echo "  \"$model_name\": $CONTEXT_LENGTH" >> "$CONFIG_FILE"
            # Set flag to false after the first model is written
            FIRST_MODEL=false
        else
            echo "Warning: Could not find context length for model '$model_name' using 'ollama show'. Skipping this model."
        fi
    fi
done

# End the JSON file with a closing brace
echo "}" >> "$CONFIG_FILE"

echo "Successfully generated '$CONFIG_FILE' with Ollama model context lengths."
echo "Please ensure you run 'chmod +x generate_ollama_context.sh' and then './generate_ollama_context.sh' before starting the Python application."

