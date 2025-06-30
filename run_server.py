# run_server.py
import sys
import yaml
import json
from mock_server import create_app

swagger_path = sys.argv[1]

with open(swagger_path, 'r') as f:
    if swagger_path.endswith(".json"):
        spec = json.load(f)
    else:
        spec = yaml.safe_load(f)

app = create_app(spec)
app.run(debug=True)
