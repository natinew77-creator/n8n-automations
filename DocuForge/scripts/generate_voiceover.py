#!/usr/bin/env python3
"""
Voiceover Generator for DocuForge AI
Uses Coqui TTS to generate audio from script text.
Fallbacks to mock audio if TTS is not installed.
"""

import sys
import json
import os
import subprocess
from pathlib import Path

def generate_voiceover(project_data):
    """
    Generate voiceover from project scenes
    """
    project_id = project_data.get('projectId', 'unknown')
    scenes = project_data.get('scenes', [])
    
    if not scenes:
        raise ValueError("No scenes provided")
        
    project_dir = Path(f"/tmp/docuforge/{project_id}")
    project_dir.mkdir(parents=True, exist_ok=True)
    voiceover_path = project_dir / f"{project_id}_voiceover.wav"
    
    # Combine text from all scenes
    full_text = " ".join([scene.get('sceneText', '') for scene in scenes])
    
    try:
        # Try running Coqui TTS command line
        # tts --text "TEXT" --out_path PATH
        print(f"Generating voiceover for: {full_text[:50]}...", file=sys.stderr)
        
        cmd = [
            'tts',
            '--text', full_text,
            '--out_path', str(voiceover_path),
            '--model_name', 'tts_models/en/ljspeech/vits' # Default fast model
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        status = "generated"
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Coqui TTS not found or failed. Creating silence mockup.", file=sys.stderr)
        # Fallback: Create silent WAV file using ffmpeg
        try:
            cmd = [
                'ffmpeg', '-y', '-f', 'lavfi', 
                '-i', 'anullsrc=r=44100:cl=mono', 
                '-t', '10', # 10 seconds silence
                str(voiceover_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            status = "mock_silence"
        except:
             status = "failed_all"
             voiceover_path = None

    return {
        'voiceoverPath': str(voiceover_path) if voiceover_path else None,
        'duration': 0, # Should verify duration
        'status': status,
        'projectId': project_id
    }

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No input data provided"}))
            sys.exit(1)
        
        input_data = json.loads(sys.argv[1])
        result = generate_voiceover(input_data)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
