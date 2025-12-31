import os
import json
import logging
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = "python3"  # Assumes running in venv

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "DocuForge AI Bridge is running"})

@app.route('/rank', methods=['POST'])
def rank_video():
    """Wraps clip_ranker.py"""
    try:
        data = request.json
        # Convert list of inputs to JSON string argument expected by script
        input_json = json.dumps(data)
        
        script_path = os.path.join(SCRIPTS_DIR, "clip_ranker.py")
        result = subprocess.run(
            [PYTHON_EXEC, script_path, input_json],
            capture_output=True,
            text=True,
            check=False  # Don't throw immediately, handle stderr
        )
        
        if result.returncode != 0:
            return jsonify({"error": "Script failed", "stderr": result.stderr}), 500
            
        # The script outputs JSON to stdout
        try:
            output_data = json.loads(result.stdout)
            return jsonify(output_data)
        except json.JSONDecodeError:
            # Fallback if script printed extra stuff (should be handled in script, but just in case)
            logging.error(f"Failed to parse script output: {result.stdout}")
            return jsonify({"error": "Invalid JSON output from script", "raw": result.stdout}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/voiceover', methods=['POST'])
def generate_voiceover():
    """Wraps generate_voiceover.py"""
    try:
        data = request.json
        # Input: The full JSON object expected by the script
        input_json = json.dumps(data)
        
        script_path = os.path.join(SCRIPTS_DIR, "generate_voiceover.py")
        result = subprocess.run(
            [PYTHON_EXEC, script_path, input_json],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({"error": "Script failed", "stderr": result.stderr}), 500
            
        output_data = json.loads(result.stdout)
        return jsonify(output_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/assemble', methods=['POST'])
def assemble_video():
    """Wraps assemble_video.py"""
    try:
        data = request.json
        input_json = json.dumps(data)
        
        script_path = os.path.join(SCRIPTS_DIR, "assemble_video.py")
        result = subprocess.run(
            [PYTHON_EXEC, script_path, input_json],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({"error": "Script failed", "stderr": result.stderr}), 500
            
        output_data = json.loads(result.stdout)
        return jsonify(output_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 DocuForge AI Bridge starting on port 5001...")
    app.run(host='0.0.0.0', port=5001)
