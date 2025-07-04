"""
Provide hooks for drf-spectacular schema post-processing.

Some generated schemas by drf-spectacular contain issues that don't pass linter
validation or emit warnings. The hooks in this module address these.
"""

import itertools
from collections.abc import MutableMapping, Sequence


def remove_invalid_url_defaults(result, *args, **kwargs):
    """
    Fix ``URLField(default="")`` schema generation.

    An empty string does not satisfy the `format: uri` validation, and schema validation
    tools can trip on this.

    The majority of the code here is inspired by the built in
    :func:`drf_spectacular.hooks.postprocess_schema_enums` hook.

    .. todo:: contribute a fix to upstream library.
    """

    def _is_type(schema_type: Sequence, expected: str) -> bool:
        if schema_type == expected:
            return True
        return not isinstance(schema_type, str) and expected in schema_type

    def iter_parameter_schemas():
        for path in result.get("paths", {}).values():
            for operation in path.values():
                if not (parameters := operation.get("parameters")):
                    continue
                for parameter in parameters:
                    yield parameter["schema"]

    def iter_component_schemas(schema):
        """
        Walk the schema definitions recursively so that each schema can be processed.
        """
        match schema:
            # array schema type variants
            case {"type": Sequence() as types} if _is_type(types, "array"):
                if item_schema := schema.get("items"):
                    yield item_schema
                    yield from iter_component_schemas(item_schema)

                if prefix_items := schema.get("prefixItems"):
                    for item_schema in prefix_items:
                        yield item_schema
                        yield from iter_component_schemas(item_schema)
            # object schema type
            case {"properties": props}:
                yield from iter_component_schemas(props)
            # any other actual schema that has a 'type' key. At this point, it cannot
            # be a container, as these have been handled before.
            case {"type": Sequence()}:
                yield schema
            case {"oneOf": nested} | {"allOf": nested} | {"anyOf": nested}:
                yield from iter_component_schemas(nested)
            case [*nested]:
                for child in nested:
                    yield from iter_component_schemas(child)
            case MutableMapping():
                for nested in schema.values():
                    yield from iter_component_schemas(nested)

    schemas_iterator = itertools.chain(
        iter_parameter_schemas(),
        iter_component_schemas(result.get("components", {}).get("schemas", {})),
    )

    # find all string (with format uri) properties that have an invalid default
    for schema in schemas_iterator:
        # only consider string types - the first match skips over everything that's
        # not a string type schema
        match schema:
            case {"type": "string"}:
                pass
            case {"type": [*types]} if "string" in types:
                pass
            case _:
                continue

        # this actual processes the default value for URI schemas
        match schema:
            case {"format": "uri", "default": ""}:
                del schema["default"]
            case _:
                continue

    return result
