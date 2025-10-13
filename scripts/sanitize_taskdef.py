#!/usr/bin/env python3
"""
Sanitize ECS task definition JSON by removing optional keys that are None/empty.
Usage: python scripts/sanitize_taskdef.py <input.json> [--set-image IMAGE]
Writes sanitized JSON to stdout.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: sanitize_taskdef.py <input.json> [--set-image IMAGE]", file=sys.stderr)
    sys.exit(2)

p = Path(sys.argv[1])
if not p.exists():
    print(f"File not found: {p}", file=sys.stderr)
    sys.exit(3)

set_image = None
if len(sys.argv) >= 4 and sys.argv[2] == '--set-image':
    set_image = sys.argv[3]

with p.open() as f:
    data = json.load(f)

# Optionally set image for container definitions
if set_image and 'containerDefinitions' in data:
    for c in data['containerDefinitions']:
        c['image'] = set_image

# Remove top-level optional keys if they are None or empty
top_keys = [
    'tags', 'pidMode', 'ipcMode', 'proxyConfiguration', 'inferenceAccelerators',
    'volumes', 'placementConstraints', 'requiresCompatibilities', 'cpu', 'memory'
]
for k in top_keys:
    if k in data and (data[k] is None or data[k] == [] or data[k] == {} or data[k] == ""):
        del data[k]

# Container-level optional keys to remove
container_keys = ['logConfiguration', 'healthCheck', 'linuxParameters', 'resourceRequirements', 'dependsOn', 'secrets']
for c in data.get('containerDefinitions', []):
    for k in container_keys:
        if k in c and (c[k] is None or c[k] == [] or c[k] == {} or c[k] == ""):
            del c[k]

# Print sanitized JSON
json.dump(data, sys.stdout, indent=2)
print()
