#swagger_parser.py
import yaml
import json

def load_swagger(file, filetype=None):
    content = file.read()
    file.seek(0)
    if filetype is None:
        filetype = "yaml"  # default
    if filetype in ('yaml', 'yml'):
        spec = yaml.safe_load(content.decode("utf-8"))
    else:
        spec = json.loads(content.decode("utf-8"))
    return spec

def extract_endpoints(spec):
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method in methods.keys():
            endpoints.append(f"{method.upper()} {path}")
    return endpoints

def get_response_schema(spec, path, method):
    method_obj = spec["paths"].get(path, {}).get(method.lower(), {})

    # Try standard response schema
    try:
        return method_obj["responses"]["200"]["content"]["application/json"]["schema"]
    except KeyError:
        pass

    try:
        return method_obj["responses"]["201"]["content"]["application/json"]["schema"]
    except KeyError:
        pass

    # Fallback to requestBody schema if no response schema found
    try:
        return method_obj["requestBody"]["content"]["application/json"]["schema"]
    except KeyError:
        return {}