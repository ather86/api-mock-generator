# app.py
import streamlit as st
import json
import tempfile
import subprocess
import yaml
import sys
import webbrowser  # NEW: to open browser tab

from swagger_parser import load_swagger, extract_endpoints, get_response_schema
from mock_generator import generate_mock_response

st.set_page_config(page_title="API Mock Generator", layout="wide")
st.title("🚀 GenAI-Powered API Mock Generator")

uploaded_file = st.file_uploader("Upload your Swagger/OpenAPI file (.json/.yaml)", type=["json", "yaml", "yml"])

if uploaded_file:
    # Read the uploaded file for future use
    file_content = uploaded_file.read()
    uploaded_file.seek(0)

    # Load and parse Swagger
    spec = load_swagger(uploaded_file)
    endpoints = extract_endpoints(spec)

    selected_endpoint = st.selectbox("Select API Endpoint", endpoints)
    method, path = selected_endpoint.split(" ", 1)

    # Get schema for mock generation
    schema = get_response_schema(spec, path, method)

    if schema:
        mock_response = generate_mock_response(schema)

        st.subheader("📦 Generated Mock Response")
        st.json(mock_response)

        # Download JSON
        st.download_button(
            label="⬇️ Download Mock Response JSON",
            data=json.dumps(mock_response, indent=2),
            file_name="mock_response.json",
            mime="application/json"
        )

        # Generate Postman collection
        def build_postman_collection(endpoint, mock_response):
            method, path = endpoint.split(" ", 1)
            return {
                "info": {
                    "name": "Mock API Collection",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
                },
                "item": [{
                    "name": path,
                    "request": {
                        "method": method,
                        "header": [],
                        "url": {
                            "raw": f"http://localhost:5000{path}",
                            "protocol": "http",
                            "host": ["localhost"],
                            "port": "5000",
                            "path": path.strip("/").split("/")
                        }
                    },
                    "response": [{
                        "name": "Mock Response",
                        "originalRequest": {},
                        "status": "200 OK",
                        "code": 200,
                        "body": json.dumps(mock_response, indent=2)
                    }]
                }]
            }

        collection = build_postman_collection(selected_endpoint, mock_response)
        st.download_button(
            label="📤 Download Postman Collection",
            data=json.dumps(collection, indent=2),
            file_name="postman_collection.json",
            mime="application/json"
        )

        # Launch Mock Server
        st.markdown("---")
        if st.button("🚀 Run Mock API Server"):
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w')
            try:
                decoded = file_content.decode("utf-8")
                tmp_file.write(decoded)
            except:
                tmp_file.write(file_content)
            tmp_file.flush()

            subprocess.Popen([sys.executable, "run_server.py", tmp_file.name])

            # Open the selected endpoint in the browser
            endpoint_url = f"http://localhost:5000{path}"
            webbrowser.open_new_tab(endpoint_url)

            st.success(f"Mock server started and opened: {endpoint_url}")

    else:
        st.warning("No valid response schema found for this endpoint.")
