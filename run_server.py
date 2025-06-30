#run_server.py
from flask import Flask, request, jsonify
import yaml
import json
import sys
import time
from jsonschema import validate, ValidationError

app = Flask(__name__)
mock_responses = {}
request_validators = {}
param_validators = {}

# CLI arguments
swagger_file = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
delay_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 0
strict_mode = "--strict" in sys.argv  # Toggle for validation

# Load OpenAPI spec
with open(swagger_file, 'r') as f:
    content = f.read()
    if swagger_file.endswith('.yaml') or swagger_file.endswith('.yml'):
        spec = yaml.safe_load(content)
    else:
        spec = json.loads(content)

# Extract components
components = spec.get("components", {}).get("schemas", {})
paths = spec.get("paths", {})

def resolve_ref(ref):
    if ref.startswith("#/components/schemas/"):
        name = ref.split("/")[-1]
        return components.get(name, {})
    return {}

# Register endpoints
for path, methods in paths.items():
    for method, details in methods.items():
        method_upper = method.upper()
        key = (path, method_upper)

        # --- Response Schema
        responses = details.get("responses", {})
        status_code = "201" if method_upper == "POST" else "200"
        schema = responses.get(status_code, {}).get("content", {}).get("application/json", {}).get("schema", {})
        if "$ref" in schema:
            schema = resolve_ref(schema["$ref"])
        mock_responses[key] = schema if schema else {"message": f"{method_upper} {path} successful"}

        # --- Request Body Schema
        if "requestBody" in details:
            body_schema = details["requestBody"].get("content", {}).get("application/json", {}).get("schema", {})
            if "$ref" in body_schema:
                body_schema = resolve_ref(body_schema["$ref"])
            request_validators[key] = body_schema

        # --- Query/Header Parameters
        param_list = details.get("parameters", [])
        query_params = []
        header_params = []
        for param in param_list:
            if "$ref" in param:
                param = resolve_ref(param["$ref"])
            if param.get("in") == "query":
                query_params.append(param)
            elif param.get("in") == "header":
                header_params.append(param)
        param_validators[key] = {"query": query_params, "header": header_params}

        # --- Endpoint Handler
        def handler(path=path, method=method_upper):
            key = (path, method)

            if delay_ms:
                time.sleep(delay_ms / 1000)

            if strict_mode:
                # --- Query Validation
                for param in param_validators.get(key, {}).get("query", []):
                    name = param["name"]
                    if param.get("required") and name not in request.args:
                        return jsonify({"error": f"Missing required query parameter: {name}"}), 400
                    if "enum" in param:
                        value = request.args.get(name)
                        if value and value not in param["enum"]:
                            return jsonify({"error": f"Invalid value for query param '{name}', must be one of {param['enum']}"}), 400

                # --- Header Validation
                for param in param_validators.get(key, {}).get("header", []):
                    name = param["name"]
                    if param.get("required") and name not in request.headers:
                        return jsonify({"error": f"Missing required header: {name}"}), 400
                    if "enum" in param:
                        value = request.headers.get(name)
                        if value and value not in param["enum"]:
                            return jsonify({"error": f"Invalid value for header '{name}', must be one of {param['enum']}"}), 400

                # --- Body Validation
                if method in ["POST", "PUT"] and key in request_validators:
                    try:
                        data = request.get_json()
                        validate(instance=data, schema=request_validators[key])
                    except ValidationError as e:
                        return jsonify({"error": "Invalid request body", "details": e.message}), 400

            return jsonify(mock_responses[key]), int(status_code)

        route_name = f"{method}_{path}".replace("/", "_").replace("{", "").replace("}", "")
        app.add_url_rule(path, route_name, handler, methods=[method_upper])

# Run server
if __name__ == "__main__":
    app.run(port=port)
