/* eslint-disable quotes */
export const markdownModel =
{
    "title": "Markdown Model",
    "types": {
        "CharacterStyle": {
            "enum": {
                "doc": [
                    "Character style enum"
                ],
                "name": "CharacterStyle",
                "values": [
                    {
                        "name": "bold"
                    },
                    {
                        "name": "italic"
                    }
                ]
            }
        },
        "CodeBlock": {
            "struct": {
                "doc": [
                    "Code block markdown part struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 100
                        },
                        "doc": [
                            "The code block's language"
                        ],
                        "name": "language",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenLT": 1000
                        },
                        "doc": [
                            "The code block's text lines"
                        ],
                        "name": "lines",
                        "type": {
                            "array": {
                                "type": {
                                    "builtin": "string"
                                }
                            }
                        }
                    }
                ],
                "name": "CodeBlock"
            }
        },
        "ImageSpan": {
            "struct": {
                "doc": [
                    "Image span struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The image URL"
                        ],
                        "name": "src",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The image's alternate text"
                        ],
                        "name": "alt",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The image's title"
                        ],
                        "name": "title",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    }
                ],
                "name": "ImageSpan"
            }
        },
        "LinkSpan": {
            "struct": {
                "doc": [
                    "Link span struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The link's URL"
                        ],
                        "name": "href",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The image's title"
                        ],
                        "name": "title",
                        "optional": true,
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The contained spans"
                        ],
                        "name": "spans",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "Span"
                                }
                            }
                        }
                    }
                ],
                "name": "LinkSpan"
            }
        },
        "List": {
            "struct": {
                "doc": [
                    "List markdown part struct"
                ],
                "members": [
                    {
                        "attr": {
                            "gte": 0.0
                        },
                        "doc": [
                            "The list is numbered and this is starting number"
                        ],
                        "name": "start",
                        "optional": true,
                        "type": {
                            "builtin": "int"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The list's items"
                        ],
                        "name": "items",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "ListItem"
                                }
                            }
                        }
                    }
                ],
                "name": "List"
            }
        },
        "ListItem": {
            "struct": {
                "doc": [
                    "List item struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The markdown document's parts"
                        ],
                        "name": "parts",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "MarkdownPart"
                                }
                            }
                        }
                    }
                ],
                "name": "ListItem"
            }
        },
        "Markdown": {
            "struct": {
                "doc": [
                    "Markdown document struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenLT": 1000
                        },
                        "doc": [
                            "The markdown document's parts"
                        ],
                        "name": "parts",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "MarkdownPart"
                                }
                            }
                        }
                    }
                ],
                "name": "Markdown"
            }
        },
        "MarkdownPart": {
            "struct": {
                "doc": [
                    "Markdown document part struct"
                ],
                "members": [
                    {
                        "doc": [
                            "A paragraph"
                        ],
                        "name": "paragraph",
                        "type": {
                            "user": "Paragraph"
                        }
                    },
                    {
                        "attr": {
                            "nullable": true
                        },
                        "doc": [
                            "A horizontal rule (value is ignored)"
                        ],
                        "name": "hr",
                        "type": {
                            "builtin": "object"
                        }
                    },
                    {
                        "doc": [
                            "A list"
                        ],
                        "name": "list",
                        "type": {
                            "user": "List"
                        }
                    },
                    {
                        "doc": [
                            "A code block"
                        ],
                        "name": "codeBlock",
                        "type": {
                            "user": "CodeBlock"
                        }
                    }
                ],
                "name": "MarkdownPart",
                "union": true
            }
        },
        "Paragraph": {
            "struct": {
                "doc": [
                    "Paragraph markdown part struct"
                ],
                "members": [
                    {
                        "doc": [
                            "The paragraph style"
                        ],
                        "name": "style",
                        "optional": true,
                        "type": {
                            "user": "ParagraphStyle"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The paragraph span array"
                        ],
                        "name": "spans",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "Span"
                                }
                            }
                        }
                    }
                ],
                "name": "Paragraph"
            }
        },
        "ParagraphStyle": {
            "enum": {
                "doc": [
                    "Paragraph style enum"
                ],
                "name": "ParagraphStyle",
                "values": [
                    {
                        "name": "h1"
                    },
                    {
                        "name": "h2"
                    },
                    {
                        "name": "h3"
                    },
                    {
                        "name": "h4"
                    },
                    {
                        "name": "h5"
                    },
                    {
                        "name": "h6"
                    }
                ]
            }
        },
        "Span": {
            "struct": {
                "doc": [
                    "Paragraph span struct"
                ],
                "members": [
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "Text span"
                        ],
                        "name": "text",
                        "type": {
                            "builtin": "string"
                        }
                    },
                    {
                        "attr": {
                            "nullable": true
                        },
                        "doc": [
                            "Line break (value is ignored)"
                        ],
                        "name": "br",
                        "type": {
                            "builtin": "object"
                        }
                    },
                    {
                        "doc": [
                            "Style span"
                        ],
                        "name": "style",
                        "type": {
                            "user": "StyleSpan"
                        }
                    },
                    {
                        "doc": [
                            "Link span"
                        ],
                        "name": "link",
                        "type": {
                            "user": "LinkSpan"
                        }
                    },
                    {
                        "doc": [
                            "Image span"
                        ],
                        "name": "image",
                        "type": {
                            "user": "ImageSpan"
                        }
                    }
                ],
                "name": "Span",
                "union": true
            }
        },
        "StyleSpan": {
            "struct": {
                "doc": [
                    "Style span struct"
                ],
                "members": [
                    {
                        "doc": [
                            "The span's character style"
                        ],
                        "name": "style",
                        "type": {
                            "user": "CharacterStyle"
                        }
                    },
                    {
                        "attr": {
                            "lenGT": 0,
                            "lenLT": 1000
                        },
                        "doc": [
                            "The contained spans"
                        ],
                        "name": "spans",
                        "type": {
                            "array": {
                                "type": {
                                    "user": "Span"
                                }
                            }
                        }
                    }
                ],
                "name": "StyleSpan"
            }
        }
    }
};
