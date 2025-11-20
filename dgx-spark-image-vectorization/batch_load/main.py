#!/usr/bin/env python3
"""
Image Vector Batch Loader

Recursively processes images in a folder structure, generates embeddings,
and stores vectors in ChromaDB with folder names as topics.
"""

import sys
import os
import base64
import requests
import uuid
from pathlib import Path


def clear_vector_database():
    """Clear all vectors from the vector database."""
    try:
        response = requests.delete("http://doc:8200/v1/vectors")
        response.raise_for_status()
        print(f"Vector database cleared - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error clearing vector database: {e}")
        sys.exit(1)


def encode_image_to_base64(image_path):
    """Read an image file and encode it to base64 string."""
    try:
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            return image_base64
    except IOError as e:
        print(f"Error reading image file {image_path}: {e}")
        sys.exit(1)


def get_embedding(image_base64):
    """Call the embedding service to get a vector for an image."""
    try:
        payload = {
            "image_base64": [image_base64],
            "image_urls": []
        }
        response = requests.post("http://doc:8100/v1/embeddings", json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "embeddings" not in data or not data["embeddings"]:
            print(f"Invalid response from embedding service: {data}")
            sys.exit(1)
        
        return data["embeddings"][0], response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error calling embedding service: {e}")
        sys.exit(1)
    except (KeyError, IndexError) as e:
        print(f"Error parsing embedding response: {e}")
        sys.exit(1)


def store_vector(vector, topic, image_name):
    """Store a vector in the vector database."""
    try:
        vector_id = str(uuid.uuid4())
        payload = {
            "vectors": [
                {
                    "id": vector_id,
                    "vector": vector,
                    "metadata": {
                        "topic": topic,
                        "image_name": image_name
                    }
                }
            ]
        }
        response = requests.post("http://doc:8200/v1/vectors", json=payload)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error storing vector: {e}")
        sys.exit(1)


def find_image_files(folder_path):
    """Find image files (jpg, jpg, png) in a single folder."""
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = []
    
    try:
        folder = Path(folder_path)
        if not folder.is_dir():
            return image_files
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
    except OSError as e:
        print(f"Error accessing folder {folder_path}: {e}")
        sys.exit(1)
    
    return image_files


def main():
    """Main application entry point."""
    # Parse command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <folder_path>")
        sys.exit(1)
    
    starting_folder = sys.argv[1]
    
    # Validate folder exists
    if not os.path.isdir(starting_folder):
        print(f"Error: Folder '{starting_folder}' does not exist")
        sys.exit(1)
    
    # Clear vector database
    print("Clearing vector database...")
    clear_vector_database()
    
    # Process each subfolder
    starting_path = Path(starting_folder)
    
    try:
        # Iterate over each subfolder within the starting folder
        for folder_path in starting_path.iterdir():
            if not folder_path.is_dir():
                continue
            
            topic = folder_path.name
            image_files = find_image_files(folder_path)
            
            # Process each image in the folder
            for image_path in image_files:
                image_name = image_path.name
                
                # Encode image to base64
                image_base64 = encode_image_to_base64(image_path)
                
                # Get embedding
                vector, embedding_status = get_embedding(image_base64)
                
                # Store vector
                vector_status = store_vector(vector, topic, image_name)
                
                # Print progress
                print(f"Processing: {topic}/{image_name} - Embedding: {embedding_status} - Vector Store: {vector_status}")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    print("Processing complete!")


if __name__ == "__main__":
    main()

