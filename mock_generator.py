from faker import Faker
import random

fake = Faker()

def mock_value(data_type):
    if data_type == "string":
        return fake.word()
    elif data_type == "integer":
        return random.randint(1, 1000)
    elif data_type == "number":
        return round(random.uniform(1, 1000), 2)
    elif data_type == "boolean":
        return random.choice([True, False])
    elif data_type == "email":
        return fake.email()
    return "sample"

def generate_mock_response(schema):
    if not schema:
        return {}

    if schema.get("type") == "array":
        # Handle array of objects
        items_schema = schema.get("items", {})
        return [generate_mock_response(items_schema) for _ in range(2)]

    elif schema.get("type") == "object" and "properties" in schema:
        response = {}
        for field, props in schema["properties"].items():
            dtype = props.get("type", "string")
            if dtype == "array":
                response[field] = generate_mock_response(props)
            elif dtype == "object":
                response[field] = generate_mock_response(props)
            elif "format" in props and props["format"] == "email":
                response[field] = mock_value("email")
            else:
                response[field] = mock_value(dtype)
        return response

    else:
        dtype = schema.get("type", "string")
        return mock_value(dtype)
