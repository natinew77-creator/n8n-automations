#!/usr/bin/env python3
"""
CLIP-based video ranking for DocuForge AI
Ranks video thumbnails against scene text using OpenAI CLIP model
"""

import sys
import json
import torch
import clip
from PIL import Image
import requests
from io import BytesIO
import numpy as np

def download_image(url, timeout=10):
    """Download image from URL with error handling"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert('RGB')
    except Exception as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return None

def rank_videos(videos_data):
    """
    Rank videos using CLIP model
    
    Args:
        videos_data: List of video objects with sceneText and thumbnailUrl
        
    Returns:
        List of videos with relevanceScore added
    """
    # Load CLIP model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}", file=sys.stderr)
    
    try:
        model, preprocess = clip.load("ViT-B/32", device=device)
    except Exception as e:
        print(f"Error loading CLIP model: {e}", file=sys.stderr)
        # Return videos with default scores if model fails
        for i, video in enumerate(videos_data):
            video['relevanceScore'] = 100 - (i * 5)
        return videos_data
    
    results = []
    
    for video in videos_data:
        try:
            # Skip videos without required fields
            if not video.get('sceneText') or not video.get('thumbnailUrl'):
                video['relevanceScore'] = 0
                results.append(video)
                continue
            
            # Download and preprocess thumbnail
            image = download_image(video['thumbnailUrl'])
            if image is None:
                video['relevanceScore'] = 0
                results.append(video)
                continue
            
            # Prepare image and text
            image_input = preprocess(image).unsqueeze(0).to(device)
            text_input = clip.tokenize([video['sceneText']]).to(device)
            
            # Calculate similarity
            with torch.no_grad():
                image_features = model.encode_image(image_input)
                text_features = model.encode_text(text_input)
                
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # Calculate cosine similarity (0-100 scale)
                similarity = (100.0 * image_features @ text_features.T).item()
                
            video['relevanceScore'] = round(max(0, min(100, similarity)), 2)
            results.append(video)
            
        except Exception as e:
            print(f"Error processing video {video.get('videoId', 'unknown')}: {e}", file=sys.stderr)
            video['relevanceScore'] = 0
            results.append(video)
    
    return results

def main():
    """Main execution function"""
    try:
        # Read input from command line argument
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No input data provided"}))
            sys.exit(1)
        
        input_data = json.loads(sys.argv[1])
        
        # Handle both list and single object inputs
        if isinstance(input_data, dict):
            videos = [input_data]
        else:
            videos = input_data
        
        # Rank videos
        ranked_videos = rank_videos(videos)
        
        # Output results as JSON
        print(json.dumps(ranked_videos))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
