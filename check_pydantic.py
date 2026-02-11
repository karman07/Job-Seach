try:
    from pydantic.json_schema import JsonSchemaValue
    print("Successfully imported JsonSchemaValue from pydantic.json_schema")
except ImportError as e:
    print(f"Failed to import: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

import pydantic
print(f"Pydantic version: {pydantic.VERSION}")
