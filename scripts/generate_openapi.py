import json
import sys
import os
import importlib.util

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    # Try to import the FastAPI app
    from app.main import app
    print("Successfully imported app from app.main")
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Current sys.path:", sys.path)
    print("Checking for app directory structure...")
    
    # List directories to help debug
    print(f"Contents of {project_root}:", os.listdir(project_root))
    
    # Check if app directory exists
    app_dir = os.path.join(project_root, 'app')
    if os.path.exists(app_dir):
        print(f"App directory exists at {app_dir}")
        print(f"Contents of app directory:", os.listdir(app_dir))
    else:
        print(f"App directory does not exist at {app_dir}")
        
    # Try alternative import approaches
    print("Trying alternative import approaches...")
    
    # Create output directory if it doesn't exist
    os.makedirs('build', exist_ok=True)
    
    # Create a basic OpenAPI schema as fallback
    basic_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "ServiceMesh API",
            "version": "1.0.0",
            "description": "API for monitoring and managing your homelab infrastructure"
        },
        "paths": {}
    }
    
    with open('build/openapi.json', 'w') as f:
        json.dump(basic_schema, f, indent=2)
    
    print("Created basic OpenAPI schema as fallback")
    sys.exit(1)

# Get the OpenAPI schema
openapi_schema = app.openapi()

# Create output directory if it doesn't exist
os.makedirs('build', exist_ok=True)

# Write the schema to a file
with open('build/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI schema generated successfully at build/openapi.json")