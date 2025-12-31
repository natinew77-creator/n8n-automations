import json
import uuid

# Configuration
PROJECT_NAME = "DocuForge AI (Docker Final v2)"
BRIDGE_HOST = "http://host.docker.internal:5001"

# Helper to create nodes
def create_node(id, name, type_name, position, parameters=None, credentials=None):
    return {
        "id": id,
        "name": name,
        "type": type_name,
        "typeVersion": 1, 
        "position": position,
        "parameters": parameters or {},
        "credentials": credentials
    }

def create_connection(source_node, target_node, source_index=0, target_index=0):
    return {
        "source": source_node,
        "target": target_node,
        "source_index": source_index,
        "target_index": target_index
    }

nodes = []
connections_map = {}

# 1. Webhook
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Webhook - Script Input",
    type_name="n8n-nodes-base.webhook",
    position=[200, 300],
    parameters={"path": "docuforge-webhook", "responseMode": "lastNode", "options": {}}
))

# 2. Analyze Script (Code)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Analyze Script",
    type_name="n8n-nodes-base.code",
    position=[400, 300],
    parameters={
        "jsCode": """
const script = $input.item.json.body?.script || $input.item.json.query?.script;
if (!script || script.length < 10) throw new Error("Script too short");
const sentences = script.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 5);
const scenes = sentences.map((s, i) => ({
    sceneId: i + 1,
    text: s,
    keywords: s.split(' ').slice(0, 5).join(' '),
    duration: Math.ceil(s.split(' ').length / 2)
}));
return { json: { projectId: `proj_${Date.now()}`, scenes, totalScenes: scenes.length } };
"""
    }
))

# 3. Split Scenes (Code -> SplitInBatches)
# We actually need to 'Set' the scenes then 'Split'.
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Split Into Scenes",
    type_name="n8n-nodes-base.code",
    position=[600, 300],
    parameters={
        "jsCode": "return $input.item.json.scenes.map(scene => ({ json: scene }));"
    }
))

# 4. Search Pexels (HTTP)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Search Pexels",
    type_name="n8n-nodes-base.httpRequest",
    position=[800, 300],
    parameters={
        "url": "https://api.pexels.com/videos/search",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendQuery": True,
        "queryParameters": {"parameters": [{"name": "query", "value": "={{ $json.keywords }}"}]},
    },
    credentials={"httpHeaderAuth": {"id": "pexels-key", "name": "Pexels API"}}
))

# 5. Process Pexels (Code)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Process Pexels",
    type_name="n8n-nodes-base.code",
    position=[1000, 300],
    parameters={
        "jsCode": """
const videos = $input.item.json.videos || [];
if (videos.length === 0) return { json: { error: "No videos" } };
return { json: { 
    videoUrl: videos[0].video_files[0].link,
    thumbnail: videos[0].image,
    sceneId: $('Split Into Scenes').item.json.sceneId
}};
"""
    }
))

# 6. Rank Clips (Bridge HTTP)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Rank Clips (Bridge)",
    type_name="n8n-nodes-base.httpRequest",
    position=[1200, 300],
    parameters={
        "method": "POST",
        "url": f"{BRIDGE_HOST}/rank",
        "sendBody": True,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "={{ $input.all() }}"
    }
))

# 7. Generate Voiceover (Bridge HTTP)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Generate Voiceover",
    type_name="n8n-nodes-base.httpRequest",
    position=[1400, 300],
    parameters={
        "method": "POST",
        "url": f"{BRIDGE_HOST}/voiceover",
        "sendBody": True,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "={{ $json }}"
    }
))

# 8. Assemble Video (Bridge HTTP)
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Assemble Video",
    type_name="n8n-nodes-base.httpRequest",
    position=[1600, 300],
    parameters={
        "method": "POST",
        "url": f"{BRIDGE_HOST}/assemble",
        "sendBody": True,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "={{ $json }}"
    }
))

# 9. Respond to Webhook
nodes.append(create_node(
    id=str(uuid.uuid4()),
    name="Respond to Webhook",
    type_name="n8n-nodes-base.respondToWebhook",
    position=[1800, 300],
    parameters={
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify({ status: 'done', video: $json.outputPath }) }}"
    }
))

# Define Connections (Source -> Targets)
connections_list = [
    ("Webhook - Script Input", ["Analyze Script"]),
    ("Analyze Script", ["Split Into Scenes"]),
    ("Split Into Scenes", ["Search Pexels"]),
    ("Search Pexels", ["Process Pexels"]),
    ("Process Pexels", ["Rank Clips (Bridge)"]),
    ("Rank Clips (Bridge)", ["Generate Voiceover"]),
    ("Generate Voiceover", ["Assemble Video"]),
    ("Assemble Video", ["Respond to Webhook"])
]

# Build n8n connections object
final_connections = {}
for source, targets in connections_list:
    if source not in final_connections:
        final_connections[source] = {"main": []}
    
    # Each target is a separate output wire, effectively
    # Actually n8n structure is "main": [ [ {node: target, ...} ] ]
    # We put them all in index 0 for linear flow
    target_nodes = []
    for t in targets:
        target_nodes.append({"node": t, "type": "main", "index": 0})
    
    final_connections[source]["main"].append(target_nodes)

# Build final JSON
workflow = {
    "name": PROJECT_NAME,
    "nodes": nodes,
    "connections": final_connections,
    "settings": {},
    "staticData": None
}

with open("docuforge_workflow.json", "w") as f:
    json.dump(workflow, f, indent=2)

print("✅ Safe Workflow Generated")
