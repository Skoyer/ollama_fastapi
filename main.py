import os
import requests
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import asyncio
from datetime import datetime

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    usage: Dict[str, Any]
    estimated_cost: Optional[float] = None
    ollama_stats: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None # Added for the summary

class LiteLLMManager:
    def __init__(self, verbose=False):
        self.verbose = verbose
        
        # Load application configuration
        self.app_config = self._load_app_config()
        self.ollama_base_url = self.app_config.get("ollama_base_url", "http://127.0.0.1:11434")
        self.summary_model_name = self.app_config.get("summary_model_name")
        self.default_model = self.app_config.get("default_model")
        
        # Model context limits from external file
        self.ollama_context_limits = {}
        self._load_ollama_context_limits()

        # Default model configurations (will be updated from Ollama)
        self.model_configs = {}
        self._models_loaded = False
        
    def log(self, message):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def _load_app_config(self):
        """Loads application configuration from app_config.json."""
        config_path = "app_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.log(f"Loaded application config from {config_path}")
                    return config
            except json.JSONDecodeError as e:
                self.log(f"Error parsing {config_path}: {e}. Using default config.")
                return {}
        else:
            self.log(f"Config file {config_path} not found. Using default config.")
            return {}

    def _load_ollama_context_limits(self):
        """Loads Ollama model context limits from ollama_context.cfg."""
        config_path = "ollama_context.cfg"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.ollama_context_limits = json.load(f)
                    self.log(f"Loaded Ollama context limits from {config_path}")
            except json.JSONDecodeError as e:
                self.log(f"Error parsing {config_path}: {e}. Context limits will be missing or default to 4096.")
                self.ollama_context_limits = {}
        else:
            self.log(f"Ollama context limits file {config_path} not found. Ensure you run the generation script (generate_ollama_context.sh).")
            self.ollama_context_limits = {}

    async def refresh_ollama_models(self):
        """Fetch available models from Ollama instance and use pre-loaded context limits."""
        # First, ensure context limits are loaded (useful if file was just generated or updated)
        self._load_ollama_context_limits()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"Found {len(data.get('models', []))} models on Ollama")
                        
                        self.model_configs = {}
                        for model_info in data.get("models", []):
                            model_name = model_info["name"]
                            # Get context limit from the loaded config, or use a default fallback
                            context_limit = self.ollama_context_limits.get(model_name, 4096) 
                            
                            self.model_configs[model_name] = {
                                "name": model_name,
                                "size": model_info.get("size"),
                                "context_limit": context_limit
                            }
                        self.log(f"Updated model configs: {list(self.model_configs.keys())}")
                        self._models_loaded = True
                    else:
                        self.log(f"Failed to fetch models: {response.status}")
                        self.model_configs = {} # Clear if fetch fails
                        self._models_loaded = False
        except aiohttp.ClientError as e:
            self.log(f"Ollama connection error: {e}")
            self.model_configs = {}
            self._models_loaded = False
        except Exception as e:
            self.log(f"An unexpected error occurred during model refresh: {e}")
            self.model_configs = {}
            self._models_loaded = False


    async def generate_chat_response(self, model: str, messages: List[Message], temperature: float, max_tokens: Optional[int]):
        """Generate response from Ollama chat endpoint."""
        url = f"{self.ollama_base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        # Prepare messages in the format Ollama expects
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False, # We want the full response for easier handling
            "options": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens # Ollama uses num_predict for max_tokens

        self.log(f"Sending request to Ollama model '{model}' with {len(messages)} messages.")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=300)) as response: # Increased timeout
                if response.status == 200:
                    data = await response.json()
                    
                    full_response_content = data.get("message", {}).get("content", "")
                    
                    # Extract usage and ollama_stats
                    prompt_eval_count = data.get("prompt_eval_count", 0)
                    eval_count = data.get("eval_count", 0)
                    total_tokens = prompt_eval_count + eval_count

                    ollama_stats = {
                        "load_duration": data.get("load_duration"),
                        "prompt_eval_count": prompt_eval_count,
                        "prompt_eval_duration": data.get("prompt_eval_duration"),
                        "eval_count": eval_count,
                        "eval_duration": data.get("eval_duration"),
                        "total_duration": data.get("total_duration")
                    }

                    usage = {"total_tokens": total_tokens}
                    # No direct cost calculation here as Ollama is local, but keeping for compatibility
                    estimated_cost = 0 
                    
                    self.log(f"Received response from '{model}'. Tokens: {total_tokens}")
                    return ChatResponse(
                        content=full_response_content,
                        usage=usage,
                        estimated_cost=estimated_cost,
                        ollama_stats=ollama_stats
                    )
                else:
                    error_text = await response.text()
                    self.log(f"Ollama API error: {response.status} - {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"Ollama API Error: {error_text}")

    async def summarize_text(self, text_to_summarize: str, summary_model: str) -> Optional[str]:
        """Summarizes given text using a specified Ollama model."""
        if not summary_model:
            self.log("No summary model configured. Skipping summarization.")
            return None

        self.log(f"Attempting to summarize text using model: {summary_model}")
        
        url = f"{self.ollama_base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        # Craft a summarization prompt
        summarize_messages = [
            {"role": "system", "content": "You are a concise summarization assistant. Summarize the following text briefly and accurately."},
            {"role": "user", "content": f"Summarize:\n\n{text_to_summarize}"}
        ]

        payload = {
            "model": summary_model,
            "messages": summarize_messages,
            "stream": False,
            "options": {
                "temperature": 0.3, # Lower temperature for less creative summaries
                "num_predict": 150 # Limit summary length for speed/conciseness
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        data = await response.json()
                        summary_content = data.get("message", {}).get("content", "").strip()
                        self.log(f"Summary generated by {summary_model}: {summary_content[:50]}...")
                        return summary_content
                    else:
                        error_text = await response.text()
                        self.log(f"Summarization Ollama API error ({summary_model}): {response.status} - {error_text}")
                        return f"Error summarizing: {response.status} - {error_text}"
        except aiohttp.ClientError as e:
            self.log(f"Summarization Ollama connection error ({summary_model}): {e}")
            return f"Error summarizing: connection issue - {e}"
        except Exception as e:
            self.log(f"An unexpected error occurred during summarization: {e}")
            return f"Error summarizing: unexpected error - {e}"


# FastAPI app setup
app = FastAPI(title="LiteLLM Chat Interface", description="A web interface for interacting with Ollama models.")
manager = LiteLLMManager(verbose=True)

# Mount static files (HTML, CSS, JS) - assuming they are in a 'static' directory if used like this
# However, if index.html, style.css, script.js are in the root, this mount might be for other future assets.
# For the current setup based on provided files, index.html, style.css, script.js are expected in the root.
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Load models from Ollama on startup."""
    await manager.refresh_ollama_models()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    # Assuming index.html is in the same directory as main.py
    with open("static/index.html", "r") as f: 
        return HTMLResponse(content=f.read())

@app.get("/config")
async def get_app_config():
    """Return the application configuration."""
    return manager.app_config

@app.get("/models")
async def get_models():
    """Return available models and their context limits."""
    if not manager._models_loaded:
        await manager.refresh_ollama_models() # Try to refresh if not loaded
    
    models_list = list(manager.model_configs.values())
    
    # Sort models by name
    models_list.sort(key=lambda x: x['name'])

    # If a default model is configured and exists, move it to the top of the list
    if manager.default_model and any(m['name'] == manager.default_model for m in models_list):
        models_list.sort(key=lambda x: x['name'] != manager.default_model)
        
    return models_list

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests, generate LLM response, and optionally summarize."""
    try:
        # Generate the main LLM response
        chat_response = await manager.generate_chat_response(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # --- Summarization Logic ---
        summary_content = None
        if manager.summary_model_name:
            # Check if the summary model exists in the loaded models
            if manager.summary_model_name in manager.model_configs:
                # Use the main response content for summarization
                summary_content = await manager.summarize_text(
                    text_to_summarize=chat_response.content,
                    summary_model=manager.summary_model_name
                )
            else:
                manager.log(f"Configured summary model '{manager.summary_model_name}' not found on Ollama. Skipping summarization.")

        chat_response.summary = summary_content
        # --- End Summarization Logic ---
        
        return chat_response
        
    except HTTPException as e:
        raise e # Re-raise FastAPI HTTP exceptions
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test connection to Ollama
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{manager.ollama_base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                ollama_status = "connected" if response.status == 200 else "error"
    except Exception: # Catch any exception during connection attempt
        ollama_status = "disconnected"
    
    return {
        "status": "healthy", 
        "message": "LiteLLM service is running",
        "ollama_status": ollama_status,
        "ollama_url": manager.ollama_base_url,
        "models_loaded": len(manager.model_configs)
    }

@app.post("/refresh-models")
async def refresh_models():
    """Manually refresh models from Ollama"""
    await manager.refresh_ollama_models()
    return {"message": "Models refreshed", "count": len(manager.model_configs)}

if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: Before running this script, ensure:
    # 1. You have created 'app_config.json' in the same directory.
    # 2. You have run the 'generate_ollama_context.sh' script to create 'ollama_context.cfg'.
    uvicorn.run(app, host="0.0.0.0", port=8000)


