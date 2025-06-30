# mock_server.py
from flask import Flask, jsonify
from swagger_parser import get_response_schema
from mock_generator import generate_mock_response

def create_app(swagger_spec):
    app = Flask(__name__)
    paths = swagger_spec.get("paths", {})

    for path, methods in paths.items():
        for method in methods.keys():
            route_path = path.replace("{", "<").replace("}", ">")
            schema = get_response_schema(swagger_spec, path, method)

            def make_view(schema=schema):  # capture schema in closure
                def view_func():
                    return jsonify(generate_mock_response(schema))
                return view_func

            app.add_url_rule(route_path, f"{method}_{path}", make_view(), methods=[method.upper()])

    return app
