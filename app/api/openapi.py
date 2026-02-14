from typing import Any

import msgspec


def openapi_response(
    struct_type: type[msgspec.Struct], description: str = "Successful Response"
) -> dict[int | str, dict[str, Any]]:
    schema, defs = msgspec.json.schema(struct_type)

    result: dict[str, Any] = {}
    if defs:
        result["$defs"] = defs

    if isinstance(schema, str):
        result["$ref"] = schema
    else:
        result.update(schema)

    return {
        200: {
            "description": description,
            "content": {"application/json": {"schema": result}},
        }
    }
