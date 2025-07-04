from maykin_common.drf_spectacular.hooks import remove_invalid_url_defaults


def test_invalid_url_format_removed_from_paths_and_components():
    schema = {
        "paths": {
            "/": {
                "get": {
                    "operationId": "retrieve-root",
                    "parameters": [
                        {
                            "in": "header",
                            "name": "resourceUrl",
                            "schema": {
                                "type": "string",
                                "format": "uri",
                                "default": "",
                            },
                        },
                        {
                            "in": "query",
                            "name": "slug",
                            "schema": {
                                "type": "string",
                                "pattern": r"^(a-z)*$",
                                "default": "",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Root",
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "/no-params": {
                "get": {
                    "responses": {},
                },
            },
        },
        "components": {
            "schemas": {
                "Root": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "format": "uri",
                            "default": "",
                        },
                        "exampleUrl": {
                            "type": "string",
                            "format": "uri",
                            "default": "https://example.com",
                        },
                        "null": {
                            "type": "null",
                        },
                    },
                }
            }
        },
    }

    updated = remove_invalid_url_defaults(schema)

    params = {
        param["name"]: param for param in updated["paths"]["/"]["get"]["parameters"]
    }
    assert "default" not in params["resourceUrl"]["schema"]
    assert "default" in params["slug"]["schema"]

    root_schema_props = updated["components"]["schemas"]["Root"]["properties"]
    assert "default" not in root_schema_props["url"]
    assert "default" in root_schema_props["exampleUrl"]


def test_primitive_schemas_processed():
    schema = {
        "components": {
            "schemas": {
                "test": {
                    "type": "string",
                    "format": "uri",
                    "default": "",
                }
            }
        }
    }

    updated = remove_invalid_url_defaults(schema)

    assert "default" not in updated["components"]["schemas"]["test"]


def test_composite_types_processed():
    schema = {
        "components": {
            "schemas": {
                "test": {
                    "type": "object",
                    "properties": {
                        "array": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "uri",
                                "default": "",
                            },
                        },
                        "prefixItemsArray": {
                            "type": "array",
                            "prefixItems": [
                                {
                                    "type": "string",
                                    "format": "uri",
                                    "default": "",
                                }
                            ],
                        },
                    },
                }
            }
        }
    }

    updated = remove_invalid_url_defaults(schema)

    props = updated["components"]["schemas"]["test"]["properties"]
    assert "default" not in props["array"]["items"]

    assert "default" not in props["prefixItemsArray"]["prefixItems"][0]


def test_multiple_types_are_processed_too():
    schema = {
        "components": {
            "schemas": {
                "test": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": ["string", "null"],
                            "format": "uri",
                            "default": "",
                        },
                    },
                }
            }
        }
    }

    updated = remove_invalid_url_defaults(schema)

    props = updated["components"]["schemas"]["test"]["properties"]
    assert "default" not in props["url"]


def test_composed_schemas_processed():
    schema = {
        "components": {
            "schemas": {
                "test": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "format": "uri",
                                    "default": "",
                                },
                            },
                        },
                        {"const": "foo"},
                    ]
                }
            }
        }
    }

    updated = remove_invalid_url_defaults(schema)

    props = updated["components"]["schemas"]["test"]["oneOf"][0]["properties"]
    assert "default" not in props["url"]
