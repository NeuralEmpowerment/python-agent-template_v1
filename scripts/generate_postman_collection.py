#!/usr/bin/env python
"""
Script to generate a Postman collection from the FastAPI OpenAPI documentation.

This script requires the openapi-to-postman Python package:
pip install openapi-to-postman

Usage:
    python scripts/generate_postman_collection.py

The script will:
1. Start the FastAPI application (if it's not already running)
2. Fetch the OpenAPI JSON schema
3. Convert it to a Postman collection
4. Save the collection to a file
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Constants
API_URL = "http://localhost:8000"
OPENAPI_URL = f"{API_URL}/openapi.json"
OUTPUT_DIR = "docs"
COLLECTION_FILE = os.path.join(OUTPUT_DIR, "postman_collection.json")


def start_api_server():
    """Start the FastAPI server in a subprocess."""
    print("Starting FastAPI server...")
    process = subprocess.Popen(
        ["uvicorn", "apps.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    time.sleep(2)
    return process


def stop_api_server(process):
    """Stop the FastAPI server subprocess."""
    if process:
        print("Stopping FastAPI server...")
        process.terminate()
        process.wait()


def check_server_running():
    """Check if the API server is already running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_openapi_schema():
    """Fetch the OpenAPI schema from the running server."""
    print(f"Fetching OpenAPI schema from {OPENAPI_URL}...")
    response = requests.get(OPENAPI_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch OpenAPI schema: {response.text}")

    return response.json()


def convert_to_postman(openapi_schema):
    """Convert the OpenAPI schema to a Postman collection."""
    try:
        from openapi2postmanv2 import convert
    except ImportError:
        print("Error: openapi-to-postman package not found.")
        print("Please install it with: pip install openapi-to-postman")
        sys.exit(1)

    print("Converting OpenAPI schema to Postman collection...")

    # Write the schema to a temporary file
    with open("temp_openapi.json", "w") as f:
        json.dump(openapi_schema, f)

    # Convert to Postman collection
    result = convert.convert_from_file("temp_openapi.json")

    # Clean up temporary file
    os.remove("temp_openapi.json")

    if result.get("result") != "success":
        raise Exception(f"Failed to convert OpenAPI schema: {result.get('reason')}")

    return result.get("output")


def save_collection(collection):
    """Save the Postman collection to a file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Saving Postman collection to {COLLECTION_FILE}...")
    with open(COLLECTION_FILE, "w") as f:
        json.dump(collection, f, indent=2)

    print("Postman collection saved successfully.")


def main():
    process = None
    try:
        # Check if server is already running
        server_running = check_server_running()

        # If not running, start it
        if not server_running:
            process = start_api_server()

        # Fetch the OpenAPI schema
        openapi_schema = fetch_openapi_schema()

        # Convert to Postman collection
        collection = convert_to_postman(openapi_schema)

        # Save the collection
        save_collection(collection)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    finally:
        # Stop the server if we started it
        if process:
            stop_api_server(process)


if __name__ == "__main__":
    main()
