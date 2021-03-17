/* eslint-disable quotes */
export const typeModel =
{
    "title": "Schema Markdown Type Model",
    "types": {
        "Action": {
            "struct": {
                "doc": [
                    "A JSON web service API"
                ],
                "members": [
                    {
                        "doc": [
                            "The user type name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The documentation group name"
                        ],
                        "name": "docGroup",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0
                        },
                        "doc": [
                            "The action's URLs"
                        ],
                        "name": "urls",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "user": "ActionURL"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The path parameters struct type name"
                        ],
                        "name": "path",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The query parameters struct type name"
                        ],
                        "name": "query",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The content body struct type name"
                        ],
                        "name": "input",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The response body struct type name"
                        ],
                        "name": "output",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The custom error response codes enum type name"
                        ],
                        "name": "errors",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    }
                ],
                "name": "Action"
            }
        },
        "ActionURL": {
            "struct": {
                "doc": [
                    "An action URL model"
                ],
                "members": [
                    {
                        "doc": [
                            "The HTTP method. If not provided, matches all HTTP methods."
                        ],
                        "name": "method",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The URL path. If not provided, uses the default URL path of \"/<actionName>\"."
                        ],
                        "name": "path",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    }
                ],
                "name": "ActionURL"
            }
        },
        "Array": {
            "struct": {
                "doc": [
                    "An array type"
                ],
                "members": [
                    {
                        "doc": [
                            "The contained type"
                        ],
                        "name": "type",
                        "type": {
                            "user": "Type"
                        }
                    },
                    {
                        "doc": [
                            "The contained type's attributes"
                        ],
                        "name": "attr",
                        "optional": true,
                        "type": {
                            "user": "Attributes"
                        }
                    }
                ],
                "name": "Array"
            }
        },
        "Attributes": {
            "struct": {
                "doc": [
                    "A type or member's attributes"
                ],
                "members": [
                    {
                        "doc": [
                            "If true, the value may be null"
                        ],
                        "name": "nullable",
                        "optional": true,
                        "type": {
                            "builtin": "bool"
                        }
                    },
                    {
                        "doc": [
                            "The value is equal"
                        ],
                        "name": "eq",
                        "optional": true,
                        "type": {
                            "builtin": "float"
                        }
                    },
                    {
                        "doc": [
                            "The value is less than"
                        ],
                        "name": "lt",
                        "optional": true,
                        "type": {
                            "builtin": "float"
                        }
                    },
                    {
                        "doc": [
                            "The value is less than or equal to"
                        ],
                        "name": "lte",
                        "optional": true,
                        "type": {
                            "builtin": "float"
                        }
                    },
                    {
                        "doc": [
                            "The value is greater than"
                        ],
                        "name": "gt",
                        "optional": true,
                        "type": {
                            "builtin": "float"
                        }
                    },
                    {
                        "doc": [
                            "The value is greater than or equal to"
                        ],
                        "name": "gte",
                        "optional": true,
                        "type": {
                            "builtin": "float"
                        }
                    },
                    {
                        "doc": [
                            "The length is equal to"
                        ],
                        "name": "lenEq",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    },
                    {
                        "doc": [
                            "The length is less-than"
                        ],
                        "name": "lenLT",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    },
                    {
                        "doc": [
                            "The length is less than or equal to"
                        ],
                        "name": "lenLTE",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    },
                    {
                        "doc": [
                            "The length is greater than"
                        ],
                        "name": "lenGT",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    },
                    {
                        "doc": [
                            "The length is greater than or equal to"
                        ],
                        "name": "lenGTE",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    }
                ],
                "name": "Attributes"
            }
        },
        "BuiltinType": {
            "enum": {
                "doc": [
                    "The built-in type enumeration"
                ],
                "name": "BuiltinType",
                "values": [
                    {
                        "doc": [
                            "The string type"
                        ],
                        "name": "string"
                    },
                    {
                        "doc": [
                            "The integer type"
                        ],
                        "name": "int"
                    },
                    {
                        "doc": [
                            "The float type"
                        ],
                        "name": "float"
                    },
                    {
                        "doc": [
                            "The boolean type"
                        ],
                        "name": "bool"
                    },
                    {
                        "doc": [
                            "A date formatted as an ISO-8601 date string"
                        ],
                        "name": "date"
                    },
                    {
                        "doc": [
                            "A date/time formatted as an ISO-8601 date/time string"
                        ],
                        "name": "datetime"
                    },
                    {
                        "doc": [
                            "A UUID formatted as string"
                        ],
                        "name": "uuid"
                    },
                    {
                        "doc": [
                            "An object of any type"
                        ],
                        "name": "object"
                    }
                ]
            }
        },
        "Dict": {
            "struct": {
                "doc": [
                    "A dictionary type"
                ],
                "members": [
                    {
                        "doc": [
                            "The contained key type"
                        ],
                        "name": "type",
                        "type": {
                            "user": "Type"
                        }
                    },
                    {
                        "doc": [
                            "The contained key type's attributes"
                        ],
                        "name": "attr",
                        "optional": true,
                        "type": {
                            "user": "Attributes"
                        }
                    },
                    {
                        "doc": [
                            "The contained value type"
                        ],
                        "name": "keyType",
                        "optional": true,
                        "type": {
                            "user": "Type"
                        }
                    },
                    {
                        "doc": [
                            "The contained value type's attributes"
                        ],
                        "name": "keyAttr",
                        "optional": true,
                        "type": {
                            "user": "Attributes"
                        }
                    }
                ],
                "name": "Dict"
            }
        },
        "Enum": {
            "struct": {
                "doc": [
                    "An enumeration type"
                ],
                "members": [
                    {
                        "doc": [
                            "The user type name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The documentation group name"
                        ],
                        "name": "docGroup",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0
                        },
                        "doc": [
                            "The enumeration values"
                        ],
                        "name": "values",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "user": "EnumValue"
                                }
                            }
                        }
                    }
                ],
                "name": "Enum"
            }
        },
        "EnumValue": {
            "struct": {
                "doc": [
                    "An enumeration type value"
                ],
                "members": [
                    {
                        "doc": [
                            "The value string"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    }
                ],
                "name": "EnumValue"
            }
        },
        "Struct": {
            "struct": {
                "doc": [
                    "A struct type"
                ],
                "members": [
                    {
                        "doc": [
                            "The user type name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The documentation group name"
                        ],
                        "name": "docGroup",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0
                        },
                        "doc": [
                            "The struct members"
                        ],
                        "name": "members",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "user": "StructMember"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "If true, the struct is a union and exactly one of the optional members is present"
                        ],
                        "name": "union",
                        "optional": true,
                        "type": {
                            "builtin": "bool"
                        }
                    }
                ],
                "name": "Struct"
            }
        },
        "StructMember": {
            "struct": {
                "doc": [
                    "A struct member"
                ],
                "members": [
                    {
                        "doc": [
                            "The member name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The member type"
                        ],
                        "name": "type",
                        "type": {
                            "user": "Type"
                        }
                    },
                    {
                        "doc": [
                            "The member type attributes"
                        ],
                        "name": "attr",
                        "optional": true,
                        "type": {
                            "user": "Attributes"
                        }
                    },
                    {
                        "doc": [
                            "If true, the member is optional and may not be present"
                        ],
                        "name": "optional",
                        "optional": true,
                        "type": {
                            "builtin": "bool"
                        }
                    }
                ],
                "name": "StructMember"
            }
        },
        "Type": {
            "struct": {
                "doc": [
                    "Union representing a member type"
                ],
                "members": [
                    {
                        "doc": [
                            "A built-in type"
                        ],
                        "name": "builtin",
                        "type": {
                            "user": "BuiltinType"
                        }
                    },
                    {
                        "doc": [
                            "An array type"
                        ],
                        "name": "array",
                        "type": {
                            "user": "Array"
                        }
                    },
                    {
                        "doc": [
                            "A dictionary type"
                        ],
                        "name": "dict",
                        "type": {
                            "user": "Dict"
                        }
                    },
                    {
                        "doc": [
                            "A user type name"
                        ],
                        "name": "user",
                        "type": {
                            "builtin": "string"
                        }
                    }
                ],
                "name": "Type",
                "union": true
            }
        },
        "TypeModel": {
            "struct": {
                "doc": [
                    "A type model with a title"
                ],
                "members": [
                    {
                        "doc": [
                            "The type model's title"
                        ],
                        "name": "title",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The type model"
                        ],
                        "name": "types",
                        "type": {
                            "user": "Types"
                        }
                    }
                ],
                "name": "TypeModel"
            }
        },
        "Typedef": {
            "struct": {
                "doc": [
                    "A typedef type"
                ],
                "members": [
                    {
                        "doc": [
                            "The user type name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The documentation group name"
                        ],
                        "name": "docGroup",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The typedef's type"
                        ],
                        "name": "type",
                        "type": {
                            "user": "Type"
                        }
                    },
                    {
                        "doc": [
                            "The typedef's type attributes"
                        ],
                        "name": "attr",
                        "optional": true,
                        "type": {
                            "user": "Attributes"
                        }
                    }
                ],
                "name": "Typedef"
            }
        },
        "Types": {
            "typedef": {
                "attr": {
                    "lenGT": 0
                },
                "doc": [
                    "Map of user type name to user type model"
                ],
                "name": "Types",
                "type": {
                    "dict": {
                        "type": {
                            "user": "UserType"
                        }
                    }
                }
            }
        },
        "UserBase": {
            "struct": {
                "doc": [
                    "User type base struct"
                ],
                "members": [
                    {
                        "doc": [
                            "The user type name"
                        ],
                        "name": "name",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "doc": [
                            "The documentation markdown text lines"
                        ],
                        "name": "doc",
                        "optional": true,
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    },
                    {
                        "doc": [
                            "The documentation group name"
                        ],
                        "name": "docGroup",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    }
                ],
                "name": "UserBase"
            }
        },
        "UserType": {
            "struct": {
                "doc": [
                    "A user type"
                ],
                "members": [
                    {
                        "doc": [
                            "An enumeration type"
                        ],
                        "name": "enum",
                        "type": {
                            "user": "Enum"
                        }
                    },
                    {
                        "doc": [
                            "A struct type"
                        ],
                        "name": "struct",
                        "type": {
                            "user": "Struct"
                        }
                    },
                    {
                        "doc": [
                            "A type definition"
                        ],
                        "name": "typedef",
                        "type": {
                            "user": "Typedef"
                        }
                    },
                    {
                        "doc": [
                            "A JSON web API (not reference-able)"
                        ],
                        "name": "action",
                        "type": {
                            "user": "Action"
                        }
                    }
                ],
                "name": "UserType",
                "union": true
            }
        }
    }
};
