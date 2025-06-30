# mock_server.py
from flask import Flask, jsonify, request
from swagger_parser import get_response_schema
from mock_generator import generate_mock_response

def create_app(swagger_spec):
    app = Flask(__name__)
    paths = swagger_spec.get("paths", {})

    @app.route("/")
    def home():
        return {
            "status": "✅ Mock API Server is running",
            "endpoints": list(paths.keys())
        }

    for path, methods in paths.items():
        for method in methods.keys():
            # Flask needs <variable> instead of {variable}
            route_path = path.replace("{", "<").replace("}", ">")
            schema = get_response_schema(swagger_spec, path, method)

            # Create a closure to capture schema and method
            def make_view(schema=schema, method=method):
                def view_func():
                    # In future: Validate request.body for POST
                    return jsonify(generate_mock_response(schema))
                return view_func

            endpoint_name = f"{method}_{path}".replace("/", "_").replace("{", "").replace("}", "")
            app.add_url_rule(route_path, endpoint_name, make_view(), methods=[method.upper()])

    return app
