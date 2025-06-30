#app.py
import streamlit as st
import json
import tempfile
import subprocess
import yaml
import sys
import webbrowser

from swagger_parser import load_swagger, extract_endpoints, get_response_schema
from mock_generator import generate_mock_response
from swagger_enhancer import enhance_swagger_with_samples

# Custom CSS for polished UI + wide tabs + single-line header
st.markdown(
    """
    <style>
    /* Header styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #0a47a1;
        margin-bottom: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-top: -8px;
        margin-bottom: 30px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* File uploader styling */
    .stFileUploader>div>div {
        border-radius: 10px;
        border: 2px dashed #0a47a1;
        padding: 20px 15px;
        background-color: #f8faff;
    }
    /* Button styling */
    .stButton>button {
        background-color: #0a47a1;
        color: white;
        border-radius: 8px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 1rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        transition: background-color 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        background-color: #073b82;
        cursor: pointer;
    }
    /* Text area for YAML */
    textarea {
        font-family: monospace !important;
        font-size: 0.9rem !important;
        line-height: 1.4rem !important;
    }

    /* Tabs container - wide and no wrap */
    .css-1v0mbdj.e16nr0p31 {
        max-width: 100% !important;
        overflow-x: auto;
    }
    .css-1v0mbdj.e16nr0p31 > div {
        white-space: nowrap !important;
        flex-wrap: nowrap !important;
    }
    .css-1v0mbdj.e16nr0p31 button {
        min-width: 160px;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<h1 class="main-header">GenAI-Powered API Mock Generator</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload Swagger files and generate enhanced mocks effortlessly.</div>', unsafe_allow_html=True)

# Tabs
tabs = st.tabs([
    "Upload Swagger File",
    "Generate Mock Response",
    "Export to Postman",
    "Swagger-to-Swagger (Enhanced Spec)",
    "Run Mock Server"
])

# Shared session state
if "spec" not in st.session_state:
    st.session_state.spec = None
    st.session_state.endpoints = []
    st.session_state.selected_endpoint = None
    st.session_state.mock_response = {}
    st.session_state.raw_content = None
    st.session_state.enhanced_spec = None

# --- Tab 1: Upload Swagger ---
with tabs[0]:
    uploaded_file = st.file_uploader(
        "Upload your Swagger/OpenAPI file",
        type=["json", "yaml", "yml"],
        help="Drag & drop or browse to upload your Swagger spec file (JSON/YAML)."
    )
    st.session_state.auto_start = st.checkbox("Auto-start mock server after upload")

    if uploaded_file:
        file_content = uploaded_file.read()
        uploaded_file.seek(0)
        st.session_state.raw_content = file_content
        st.session_state.spec = load_swagger(uploaded_file)
        st.session_state.endpoints = extract_endpoints(st.session_state.spec)
        st.success("Swagger file loaded successfully.")
        st.session_state.auto_start_trigger = st.session_state.auto_start

# --- Tab 2: Generate Mock Response ---
with tabs[1]:
    if st.session_state.spec:
        selected = st.selectbox("Select an API endpoint", st.session_state.endpoints)
        method, path = selected.split(" ", 1)
        st.session_state.selected_endpoint = selected
        schema = get_response_schema(st.session_state.spec, path, method)

        if schema:
            mock_response = generate_mock_response(schema)
            st.session_state.mock_response = mock_response
            st.subheader("Generated Mock Response")
            st.json(mock_response)
            st.download_button(
                "Download Mock JSON",
                data=json.dumps(mock_response, indent=2),
                file_name="mock_response.json",
                mime="application/json"
            )
        else:                                                            
            st.warning("No response schema found.")

# --- Tab 3: Export to Postman ---
with tabs[2]:
    if st.session_state.mock_response and st.session_state.selected_endpoint:
        method, path = st.session_state.selected_endpoint.split(" ", 1)
        status_code = 201 if method == "POST" else 200

        def build_postman_collection(endpoint, mock_response, method, path):
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
                        "status": f"{status_code} OK",
                        "code": status_code,
                        "body": json.dumps(mock_response, indent=2, ensure_ascii=False),
                        "header": [{"key": "Content-Type", "value": "application/json"}]
                    }]
                }]
            }

        collection = build_postman_collection(
            st.session_state.selected_endpoint,
            st.session_state.mock_response,
            method,
            path
        )

        st.subheader("Export to Postman")
        st.download_button(
            label="Download Postman Collection",
            data=json.dumps(collection, indent=2),
            file_name="postman_collection.json",
            mime="application/json"
        )
    else:
        st.info("Generate a mock response first.")

# --- Tab 4: Swagger-to-Swagger Enhanced Spec ---
with tabs[3]:
    st.subheader("Generate Enhanced Swagger Spec with Fake Samples")

    if st.session_state.spec:
        st.write("This will generate an enhanced Swagger/OpenAPI spec with fake example data injected into request/response schemas.")

        if st.button("Generate Enhanced Swagger Spec"):
            enhanced_spec = enhance_swagger_with_samples(st.session_state.spec)
            st.session_state.enhanced_spec = enhanced_spec
            st.success("Enhanced Swagger spec generated!")

        if st.session_state.enhanced_spec:
            enhanced_yaml = yaml.dump(st.session_state.enhanced_spec, sort_keys=False)
            edited_yaml = st.text_area("Enhanced Swagger Spec (YAML)", value=enhanced_yaml, height=500)

            st.download_button(
                "Download Enhanced Swagger Spec",
                data=edited_yaml,
                file_name="enhanced_swagger.yaml",
                mime="application/x-yaml"
            )

            try:
                updated_spec = yaml.safe_load(edited_yaml)
                st.session_state.enhanced_spec = updated_spec
            except Exception as e:
                st.error(f"Error parsing YAML: {e}")

    else:
        st.info("Please upload and parse a Swagger file first.")

# --- Tab 5: Run Mock Server ---
with tabs[4]:
    st.subheader("Mock Server Settings")

    port = st.number_input("Port", min_value=1024, max_value=65535, value=5000, step=1)
    delay = st.slider("Response Delay (in milliseconds)", min_value=0, max_value=5000, value=0, step=100)
    strict_mode = st.checkbox("Enable strict mode (validate request params, headers, body)", value=False)

    if st.button("Start Mock API Server") or st.session_state.get("auto_start_trigger", False):
        if st.session_state.raw_content:
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w')
            try:
                tmp_file.write(st.session_state.raw_content.decode("utf-8"))
            except:
                tmp_file.write(st.session_state.raw_content)
            tmp_file.flush()

            cmd = [sys.executable, "run_server.py", tmp_file.name, str(port), str(delay)]
            if strict_mode:
                cmd.append("--strict")

            subprocess.Popen(cmd)

            st.session_state.auto_start_trigger = False

            if st.session_state.selected_endpoint:
                _, path = st.session_state.selected_endpoint.split(" ", 1)
                endpoint_url = f"http://localhost:{port}{path}"
                webbrowser.open_new_tab(endpoint_url)
                st.success(f"Mock server started: {endpoint_url}")
            else:
                st.success(f"Mock server started on http://localhost:{port}")
        else:
            st.warning("Please upload and parse a Swagger file first.")
