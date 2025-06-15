#!/bin/bash

# This is run from root of project

# Security Fix Script for Ollama FastAPI Project
# This script sets proper permissions for a Python web application

echo "🔒 Fixing file permissions for security..."

# Set proper permissions for Python files (readable, not executable)
echo "📝 Setting Python file permissions..."
find . -name "*.py" -type f -exec chmod 644 {} \;

# Set proper permissions for web static files
echo "🌐 Setting web file permissions..."
find ./static -name "*.html" -type f -exec chmod 644 {} \;
find ./static -name "*.css" -type f -exec chmod 644 {} \;
find ./static -name "*.js" -type f -exec chmod 644 {} \;

# Set proper directory permissions
echo "📁 Setting directory permissions..."
find ./static -type d -exec chmod 755 {} \;

# Set proper permissions for configuration files
echo "⚙️  Setting config file permissions..."
find . -name "*.json" -type f -exec chmod 644 {} \;
find . -name "*.cfg" -type f -exec chmod 644 {} \;

# Keep shell scripts executable
echo "🔧 Ensuring shell scripts are executable..."
find . -name "*.sh" -type f -exec chmod 755 {} \;

# Set restrictive permissions for sensitive files
echo "🔐 Securing sensitive files..."
if [ -f "./app_config.json" ]; then
    chmod 600 ./app_config.json  # Only owner can read/write
    echo "   ✓ app_config.json secured (600)"
fi

# Set proper permissions for documentation
echo "📚 Setting documentation permissions..."
find . -name "*.md" -type f -exec chmod 644 {} \;
find . -name "README*" -type f -exec chmod 644 {} \;

# Ensure project root has proper permissions
chmod 755 .

echo ""
echo "✅ Security fixes applied!"
echo ""
echo "📋 Summary of changes:"
echo "   • Python files: 644 (read-write owner, read-only others)"
echo "   • Web files: 644 (read-write owner, read-only others)"
echo "   • Directories: 755 (full owner, read-execute others)"
echo "   • Config files: 600 (owner only)"
echo "   • Shell scripts: 755 (executable)"
echo ""
echo "🔍 To verify changes, run: ls -la"
echo ""
