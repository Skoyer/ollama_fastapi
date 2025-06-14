let messages = [];

function addMessage(role, content, usage = null, cost = null, ollamaStats = null) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    // Convert markdown content to HTML
    let processedContent = marked.parse(content);
    let messageHtml = `<div>${processedContent}</div>`;
    
    if (usage) {
        let infoText = `Tokens: ${usage.total_tokens}`;
        if (cost !== null && cost > 0) {
            infoText += ` | Cost: $${cost.toFixed(6)}`;
        }
        if (ollamaStats && ollamaStats.total_duration) {
            const seconds = (ollamaStats.total_duration / 1000000000).toFixed(2);
            infoText += ` | Time: ${seconds}s`;
            if (ollamaStats.eval_count > 0) {
                const tokensPerSec = (ollamaStats.eval_count / (ollamaStats.eval_duration / 1000000000)).toFixed(1);
                infoText += ` | Speed: ${tokensPerSec} tok/s`;
            }
        }
        messageHtml += `<div class="message-info">${infoText}</div>`;
    }
    
    messageDiv.innerHTML = messageHtml;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showError(message) {
    const messagesDiv = document.getElementById('messages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    messagesDiv.appendChild(errorDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showSuccess(message) {
    const messagesDiv = document.getElementById('messages');
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    messagesDiv.appendChild(successDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function loadModels() {
    try {
        const response = await fetch('/models');
        const models = await response.json();
        
        const select = document.getElementById('model-select');
        select.innerHTML = '';
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">No models available</option>';
            return;
        }
        
        let defaultModelName = null;
        // Fetch app configuration to get the default model
        try {
            const configResponse = await fetch('/config'); // New endpoint to fetch app config
            if (configResponse.ok) {
                const appConfig = await configResponse.json();
                defaultModelName = appConfig.default_model;
            } else {
                console.warn(`Could not load app config: HTTP ${configResponse.status}`);
            }
        } catch (configError) {
            console.warn("Could not load app config for default model:", configError);
        }

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            const sizeText = model.size ? ` (${(model.size / 1024 / 1024 / 1024).toFixed(1)}GB)` : '';
            option.textContent = `${model.name}${sizeText} - ${model.context_limit} ctx`;
            select.appendChild(option);
        });

        // Set the default model if it exists in the fetched models
        // Otherwise, fallback to the first model in the list
        if (defaultModelName && models.some(m => m.name === defaultModelName)) {
            select.value = defaultModelName;
        } else if (models.length > 0) {
            select.value = models[0].name;
        }
        
        showSuccess(`🍂 Loaded ${models.length} models from Ollama`);
        
    } catch (error) {
        console.error('Failed to load models:', error);
        showError('Failed to load models from Ollama');
    }
}

// NEW FUNCTION: Displays debug information in a modal
function showDebugPopup(title, content) {
    // Create modal background
    const modalBackground = document.createElement('div');
    modalBackground.className = 'modal-backdrop'; // Use class for styling

    // Create modal content box
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content'; // Use class for styling

    // Close button
    const closeButton = document.createElement('span');
    closeButton.innerHTML = '&times;'; // 'x' character
    closeButton.className = 'modal-close-button'; // Use class for styling
    closeButton.onclick = () => document.body.removeChild(modalBackground);

    // Title
    const modalTitle = document.createElement('h3');
    modalTitle.textContent = title;
    modalTitle.className = 'modal-title'; // Use class for styling

    // Preformatted content area
    const contentPre = document.createElement('pre');
    contentPre.textContent = content;
    contentPre.className = 'modal-pre'; // Use class for styling

    modalContent.appendChild(closeButton);
    modalContent.appendChild(modalTitle);
    modalContent.appendChild(contentPre);
    modalBackground.appendChild(modalContent);
    document.body.appendChild(modalBackground);

    // Close on background click
    modalBackground.addEventListener('click', (e) => {
        if (e.target === modalBackground) {
            document.body.removeChild(modalBackground);
        }
    });
}


async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    const model = document.getElementById('model-select').value;
    if (!model) {
        showError('Please select a model first');
        return;
    }
    
    const temperature = parseFloat(document.getElementById('temperature').value);
    const maxTokens = document.getElementById('max-tokens').value;
    
    // Add user message to display
    addMessage('user', message);
    messages.push({role: 'user', content: message});
    
    // Clear input and disable send button
    input.value = '';
    const sendButton = document.getElementById('send-button');
    sendButton.disabled = true;
    document.getElementById('loading').style.display = 'block';
    
    try {
        const requestBody = {
            model: model,
            messages: messages,
            temperature: temperature,
            max_tokens: maxTokens ? parseInt(maxTokens) : null
        };
        
        // ** DEBUG STEP: Capture and display the payload **
        const payloadString = JSON.stringify(requestBody, null, 2); // Pretty print JSON
        const debugInfo = `
Request URL: /chat
Request Method: POST
Content-Type: application/json

Request Payload:
${payloadString}
        `;
        showDebugPopup("Ollama API Request Debug Info", debugInfo);
        // ** END DEBUG STEP **

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: payloadString // Use the pretty-printed string for sending
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        // Add assistant message to display
        addMessage('assistant', data.content, data.usage, data.estimated_cost, data.ollama_stats);
        messages.push({role: 'assistant', content: data.content});

        // --- NEW: Display Summary if available ---
        if (data.summary) {
            addMessage('summary', `**Summary (by smaller LLM):** ${data.summary}`);
        }
        // --- END NEW ---
        
    } catch (error) {
        console.error('Error:', error);
        showError(`Error: ${error.message}`);
    } finally {
        sendButton.disabled = false;
        document.getElementById('loading').style.display = 'none';
        input.focus();
    }
}

function clearChat() {
    messages = [];
    document.getElementById('messages').innerHTML = '';
    document.getElementById('message-input').focus();
}

function handleKeyDown(event) {
    if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('clear-button').addEventListener('click', clearChat);
    document.getElementById('refresh-models').addEventListener('click', loadModels);
    document.getElementById('message-input').addEventListener('keydown', handleKeyDown);
    
    document.getElementById('message-input').focus();
    loadModels();
});

