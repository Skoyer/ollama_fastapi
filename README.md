# Ollama FastAPI Experiments

This repository contains experiments integrating [Ollama](https://ollama.com/) with a FastAPI backend and a simple web frontend.  
Project home: [https://github.com/Skoyer/ollama_fastapi](https://github.com/Skoyer/ollama_fastapi)

## Project Structure

```
.
├── app_config.json
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
- [Ollama](https://ollama.com/) installed and running on your machine
- (Optional) [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/) for serving the backend

### 2. Start Ollama

Make sure the Ollama server is running and serving the REST API (default: `http://localhost:11434`):

```bash
ollama serve
```

You can check if it's running with:

```bash
curl http://localhost:11434
```

### 3. Start the FastAPI App

Install dependencies (if any):

```bash
pip install fastapi uvicorn
```

Run the app:

```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`.

### 4. Access the Web Frontend

Open your browser and go to `http://localhost:8000/static/index.html`.

---

## File Descriptions

- **main.py**: FastAPI backend server, handles API requests and communication with Ollama.
- **app_config.json**: Configuration file for the application (API keys, settings, etc.).
- **ollama_context.cfg**: Configuration for Ollama context or model parameters.
- **static/**: Contains frontend files (HTML, JS, CSS). See [`static/README.md`](static/README.md).
- **utils/**: Utility scripts and additional configuration. See [`utils/README.md`](utils/README.md).

---

## License & Usage

You are welcome to use, modify, and share this code. Attribution is appreciated but not required.

---

## Reference

- [Ollama FastAPI GitHub Repository](https://github.com/Skoyer/ollama_fastapi)

---

## Recommendations

If you use this code, consider starring the repository and sharing feedback or improvements via pull requests or issues. Contributions are welcome!
