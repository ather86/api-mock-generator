# swagger_parser.py
import yaml
import json

def load_swagger(file):
    if file.name.endswith('.yaml') or file.name.endswith('.yml'):
        spec = yaml.safe_load(file)
    else:
        spec = json.load(file)
    return spec

def extract_endpoints(spec):
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method in methods.keys():
            endpoints.append(f"{method.upper()} {path}")
    return endpoints

def get_response_schema(spec, path, method):
    try:
        return spec["paths"][path][method.lower()]["responses"]["200"]["content"]["application/json"]["schema"]
    except KeyError:
        return {}
