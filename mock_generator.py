#mock_generator.py
from faker import Faker
import random
import uuid

fake = Faker()


def smart_mock(field_name, data_type, format_type=None, enum_list=None):
    """
    Generate a mock value based on field name heuristics, data type,
    format, and enum values if provided.
    """
    fname = field_name.lower()

    # Enum takes highest priority
    if enum_list:
        return random.choice(enum_list)

    # Format-based generation
    if format_type == "email":
        return fake.email()
    elif format_type == "date-time":
        return fake.iso8601()
    elif format_type == "date":
        return fake.date()

    # Field-name heuristics (prioritize booleans early)
    if fname.startswith("is_") or fname.startswith("has_"):
        return random.choice([True, False])
    elif "email" in fname:
        return fake.email()
    elif "name" in fname:
        return fake.name()
    elif "price" in fname or "amount" in fname:
        return round(random.uniform(50, 1000), 2)
    elif "status" in fname:
        return random.choice(["start", "processing", "end"])
    elif fname.endswith("id"):
        if data_type == "string":
            return str(uuid.uuid4())
        elif data_type == "integer":
            return random.randint(1000, 99999)

    # Fallback based on data type
    if data_type == "boolean":
        return random.choice([True, False])
    elif data_type == "string":
        return fake.word()
    elif data_type == "integer":
        return random.randint(1, 1000)
    elif data_type == "number":
        return round(random.uniform(1, 1000), 2)

    return "sample"


def generate_mock_response(schema):
    """
    Recursively generate a mock response based on JSON schema dict.
    Supports type: object, array, primitives, and basic allOf/oneOf/anyOf.
    """
    if not schema:
        return {}

    # Handle schema compositions (basic)
    if "allOf" in schema:
        combined = {}
        for subschema in schema["allOf"]:
            mock_part = generate_mock_response(subschema)
            if isinstance(mock_part, dict):
                combined.update(mock_part)
        return combined

    if "oneOf" in schema or "anyOf" in schema:
        subschemas = schema.get("oneOf") or schema.get("anyOf")
        # Just pick one subschema to generate example
        return generate_mock_response(subschemas[0])

    schema_type = schema.get("type")

    if schema_type == "array":
        items_schema = schema.get("items", {})
        # Return list with 2 sample items
        return [generate_mock_response(items_schema) for _ in range(2)]

    if schema_type == "object":
        properties = schema.get("properties", {})
        response = {}
        for field, props in properties.items():
            dtype = props.get("type", "string")
            fmt = props.get("format")
            enum_list = props.get("enum")

            if dtype == "array":
                response[field] = generate_mock_response(props)
            elif dtype == "object":
                response[field] = generate_mock_response(props)
            else:
                response[field] = smart_mock(field, dtype, fmt, enum_list)
        return response

    # For primitive types without object or array wrapper
    dtype = schema.get("type", "string")
    fmt = schema.get("format")
    enum_list = schema.get("enum")
    return smart_mock("value", dtype, fmt, enum_list)
