# Ollama FastAPI Experiments

This repository contains experiments integrating Ollama with a FastAPI backend and a simple web frontend.
Project home: https://github.com/Skoyer/ollama_fastapi

## Project Structure

```
.
├── app_config.json.example
├── app_config.json          # (created from example, not tracked in git)
├── main.py
├── ollama_context.cfg
├── static
│   ├── index.html
│   ├── script.js
│   └── style.css
└── utils
    ├── generate_ollama_context.sh
    └── ollama_context.cfg
```

## Getting Started

### 1. Prerequisites

- Python 3.8+
- Ollama installed and running on your machine
- (Optional) FastAPI and Uvicorn for serving the backend

### 2. Configuration

1. Copy the example config file:
   ```bash
   cp app_config.json.example app_config.json
   ```

2. Edit `app_config.json` to match your setup:
   - `ollama_base_url`: URL where your Ollama server is running (default: http://127.0.0.1:11434)
   - `default_model`: The Ollama model to use (e.g., "llama2:latest", "codellama:latest")
   - `summary_model_name`: Optional separate model for summaries (null to use default_model)

### 3. Start Ollama

Make sure the Ollama server is running and serving the REST API (default: http://localhost:11434):

```bash
ollama serve
```

You can check if it's running with:

```bash
curl http://localhost:11434
```

### 4. Start the FastAPI App

Install dependencies (if any):

```bash
pip install fastapi uvicorn
```

Run the app:

```bash
uvicorn main:app --reload
```

The app will be available at http://localhost:8000.

### 5. Access the Web Frontend

Open your browser and go to http://localhost:8000/static/index.html.

## File Descriptions

- **main.py**: FastAPI backend server, handles API requests and communication with Ollama.
- **app_config.json.example**: Template configuration file for the application.
- **app_config.json**: Your local configuration file (created from example, not tracked in git).
- **ollama_context.cfg**: Configuration for Ollama context or model parameters.
- **static/**: Contains frontend files (HTML, JS, CSS). See static/README.md.
- **utils/**: Utility scripts and additional configuration. See utils/README.md.

## Notes

- The `app_config.json` file is ignored by git to prevent conflicts between different environments
- Each user should create their own `app_config.json` from the provided example
- Make sure your Ollama server is accessible at the URL specified in your config
