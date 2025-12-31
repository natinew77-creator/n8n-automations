import json
import os

WORKFLOW_PATH = "docuforge_workflow.json"
NEW_WORKFLOW_PATH = "docuforge_docker_workflow.json"

def migrate_workflow():
    if not os.path.exists(WORKFLOW_PATH):
        print(f"Error: {WORKFLOW_PATH} not found.")
        return

    with open(WORKFLOW_PATH, 'r') as f:
        workflow = json.load(f)

    nodes = workflow.get('nodes', [])
    updated = 0

    for node in nodes:
        node_type = node.get('type')
        node_name = node.get('name')
        
        if node_type == 'n8n-nodes-base.executeCommand':
            # Identify which script it is calling
            command = node.get('parameters', {}).get('command', '')
            
            endpoint = None
            body_expression = None
            
            if 'clip_ranker.py' in command:
                endpoint = 'rank'
                # Extract input expression: '={{ JSON.stringify($input.all()) }}' -> '={{ $input.all() }}'
                # Actually, HTTP Request sends JSON automatically if we set Send Body = True.
                # We want to send the exact data the script expected.
                # The script expected JSON string command line arg.
                # The Bridge expects JSON body.
                # If command was: ...script.py '={{ JSON.stringify($input.all()) }}'
                # Body should be: ={{ $input.all() }}
                body_expression = "={{ $input.all() }}"
                
            elif 'generate_voiceover.py' in command:
                endpoint = 'voiceover'
                # Was: ...script.py '={{ JSON.stringify($json) }}'
                body_expression = "={{ $json }}"
                
            elif 'assemble_video.py' in command:
                endpoint = 'assemble'
                # Was: ...script.py '={{ JSON.stringify($('Parse Voiceover Result').item.json) }}'
                # Wait, 'assemble_video.py' usually takes specific input.
                # In previous step: '={{ JSON.stringify($('Parse Voiceover Result').item.json) }}'
                # So we use that same expression.
                # Note: access to previous nodes works same way.
                body_expression = "={{ $('Parse Voiceover Result').item.json }}"
            
            if endpoint:
                print(f"Migrating Node: {node_name} -> HTTP POST /{endpoint}")
                
                # Change type (preserving ID and Position)
                node['type'] = 'n8n-nodes-base.httpRequest'
                node['typeVersion'] = 4.2
                
                # New parameters
                node['parameters'] = {
                    "method": "POST",
                    "url": f"http://host.docker.internal:5001/{endpoint}",
                    "sendBody": True,
                    "contentType": "json",
                    "bodyParameters": {
                        "parameters": [
                            # We need to send the raw JSON data, not key-value pairs?
                            # n8n HTTP Request manual-ish setup: 
                            # Specify Content Type: JSON
                            # JSON/RAW Body: True
                        ]
                    },
                    "options": {
                        "timeout": 300000 # 5 minutes for video processing
                    }
                }
                
                # n8n JSON Structure for "Specify Body"
                # To send a raw expression as the body:
                node['parameters']['specifyBody'] = "json"
                node['parameters']['jsonBody'] = body_expression
                
                updated += 1

    workflow['name'] = "DocuForge AI (Docker Edition)"
    
    with open(NEW_WORKFLOW_PATH, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"Migration complete. {updated} nodes updated. Saved to {NEW_WORKFLOW_PATH}")

if __name__ == "__main__":
    migrate_workflow()
