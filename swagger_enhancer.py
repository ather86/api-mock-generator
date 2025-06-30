#swagger_enhancer.py
import copy
from mock_generator import generate_mock_response

def enhance_swagger_with_samples(spec: dict) -> dict:
    """
    Given a Swagger/OpenAPI spec dict, return a new spec dict with fake example
    data injected into requestBody and responses schemas.
    """

    spec_copy = copy.deepcopy(spec)

    # OpenAPI 3.x uses "paths" -> each path -> methods (get/post/put/...)
    paths = spec_copy.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            method = method.lower()
            if method not in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
                continue

            # Enhance requestBody if present
            request_body = details.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                for media_type, media_obj in content.items():
                    schema = media_obj.get("schema")
                    if schema:
                        example = _generate_example_for_schema(schema)
                        if example is not None:
                            media_obj["example"] = example

            # Enhance responses
            responses = details.get("responses", {})
            for status_code, resp_obj in responses.items():
                content = resp_obj.get("content", {})
                for media_type, media_obj in content.items():
                    schema = media_obj.get("schema")
                    if schema:
                        example = _generate_example_for_schema(schema)
                        if example is not None:
                            media_obj["example"] = example

    return spec_copy


def _generate_example_for_schema(schema: dict):
    """
    Use your existing generate_mock_response or custom logic to
    generate a fake example for the given JSON schema.
    """

    # generate_mock_response expects a JSON schema dict and returns a fake instance
    try:
        example = generate_mock_response(schema)
        return example
    except Exception as e:
        # In case generation fails, just skip
        return None
