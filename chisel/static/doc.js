var chisel;
if (undefined === chisel) {
    chisel = {};
}
chisel.doc = (function () {
    var module = {};

    module.index = function (body, params) {
        chips.xhr('get', '/docIndexApi', true, {
            onok: function (index) {
                var title = window.location.host;
                document.title = title;

                chips.render(body, [
                    chips.elem('h1', [chips.text(title)]),
                    chips.elem('ul', {'class': 'chsl-request-list'}, [
                        chips.elem('li', index.names.map(function (name) {
                            return chips.elem('li', [
                                chips.elem('a', {'href': chips.href({'name': name})}, [chips.text(name)]),
                            ]);
                        })),
                    ]),
                ], true);
            },
        });
    };

    module.request = function (body, params) {
        chips.xhr('get', '/docApi', true, {
            params: {name: params.name},
            onok: function (request) {
                document.title = params.name;

                chips.render(body, [
                    // Navigation bar
                    (params.nonav === 'true' ? null : chips.elem('div', {'class': 'chsl-header'}, [
                        chips.elem('a', {'href': chips.href()}, [chips.text('Back to documentation index')]),
                    ])),

                    // Title
                    chips.elem('h1', [
                        chips.text(request.name),
                    ]),
                    textElem(request.doc),

                    // Notes
                    chips.elem('div', {'class': 'chsl-notes'}, [
                        // Request URLs note
                        (!request.urls.length ? null : chips.elem('div', {'class': 'chsl-note'}, [
                            chips.elem('p', [
                                chips.elem('b', [chips.text('Note: ')]),
                                chips.text('The request is exposed at the following URL' + (request.urls.length > 1 ? 's:' : ':')),
                                chips.elem('ul', request.urls.map(function (url) {
                                    return chips.elem('li', [
                                        chips.elem('a', {'href': url.url}, [chips.text(url.method ? url.method + ' ' + url.url : url.url)]),
                                    ]);
                                })),
                            ]),
                        ])),

                        // Action non-default response note
                        (!request.action || request.action.output ? null : chips.elem('div', {'class': 'chsl-note'}, [
                            chips.elem('p', [
                                chips.elem('b', [chips.text('Note: ')]),
                                chips.text('The action has a non-default response. See documentation for details.'),
                            ]),
                        ])),

                        // Action?
                        (!request.action ? null : [
                            actionInputOutputElem(request.action.input, 'h2', 'Input Parameters', 'The action has no input parameters.'),
                            actionInputOutputElem(request.action.output, 'h2', 'Output Parameters', 'The action has no output parameters.'),
                            enumElem(request.action.errors, 'h2', 'Error Codes', 'The action returns no custom error codes.'),

                            // Typedefs
                            (!request.typedefs.length ? null : [
                                chips.elem('h2', [chips.text('Typedefs')]),
                                request.typedefs.map(function (typedef) {
                                    return typedefElem(typedef);
                                }),
                            ]),

                            // Structs
                            (!request.structs.length ? null : [
                                chips.elem('h2', chips.text('Struct Types')),
                                request.structs.map(function (struct) {
                                    return structElem(struct);
                                }),
                            ]),

                            // Enums
                            (!request.enums.length ? null : [
                                chips.elem('h2', chips.text('Enum Types')),
                                request.enums.map(function (enum_) {
                                    return enumElem(enum_);
                                }),
                            ]),
                        ]),
                    ]),
                ], true);
            }
        });
    };

    function textElem(lines) {
        var divElems = [];
        var paragraph = [];
        if (chips.isArray(lines)) {
            for (iLine = 0; iLine < lines.length; iLine++) {
                if (lines[iLine].length) {
                    paragraph.push(lines[iLine]);
                } else if (paragraph.length) {
                    divElems.push(chips.elem('p', chips.text(paragraph.join('\n'))));
                    paragraph = [];
                }
            }
        } else if (lines) {
            paragraph.push(lines);
        }
        if (paragraph.length) {
            divElems.push(chips.elem('p', [chips.text(paragraph.join('\n'))]));
        }
        return divElems.length ? chips.elem('div', {'class': 'chsl-text'}, divElems) : null;
    }

    function typeHref(type) {
        // TODO: avoid decoding params multiple times
        var paramsOld = chips.decodeParams();
        var params = {};

        if (paramsOld.name) {
            params.name = paramsOld.name;
        }
        if (paramsOld.nonav) {
            params.nonav = paramsOld.nonav;
        }

        if (type.typedef) {
            params['typedef_' + type.typedef] = null;
        } else if (type['enum']) {
            params['enum_' + type['enum']] = null;
        } else if (type.struct) {
            params['struct_' + type.struct] = null;
        }

        return chips.encodeParams(params);
    }

    function typeElem(type) {
        if (type.array) {
            return [typeElem(type.array.type), chips.text(chips.nbsp + '[]')];
        } else if (type.dict) {
            return [
                type.dict.key_type !== 'string' ? null : [typeElem(type.dict.key_type), chips.text(chips.nbsp + ':' + chips.nbsp)],
                typeElem(type.dict.type), chips.text(chips.nbsp + '{}')
            ];
        } else if (type['enum']) {
            return chips.elem('a', {href: '#' + typeHref(type)}, [chips.text(type['enum'])]);
        } else if (type.struct) {
            return chips.elem('a', {href: '#' + typeHref(type)}, [chips.text(type.struct)]);
        } else if (type.typedef) {
            return chips.elem('a', {href: '#' + typeHref(type)}, [chips.text(type.typedef)]);
        }
        return chips.text(type.builtin);
    }

    function attrParts(typeName, attr) {
        var parts = [];
        if (attr && attr.gt) {
            parts.push({lhs: typeName, op: '>', rhs: attr.gt});
        }
        if (attr && attr.gte) {
            parts.push({lhs: typeName, op: '>=', rhs: attr.gte});
        }
        if (attr && attr.lt) {
            parts.push({lhs: typeName, op: '<', rhs: attr.lt});
        }
        if (attr && attr.lte) {
            parts.push({lhs: typeName, op: '<=', rhs: attr.lte});
        }
        if (attr && attr.eq) {
            parts.push({lhs: typeName, op: '==', rhs: attr.eq});
        }
        if (attr && attr.len_gt) {
            parts.push({lhs: 'len(' + typeName + ')', op: '>', rhs: attr.len_gt});
        }
        if (attr && attr.len_gte) {
            parts.push({lhs: 'len(' + typeName + ')', op: '>=', rhs: attr.len_gte});
        }
        if (attr && attr.len_lt) {
            parts.push({lhs: 'len(' + typeName + ')', op: '<', rhs: attr.len_lt});
        }
        if (attr && attr.len_lte) {
            parts.push({lhs: 'len(' + typeName + ')', op: '<=', rhs: attr.len_lte});
        }
        if (attr && attr.len_eq) {
            parts.push({lhs: 'len(' + typeName + ')', op: '==', rhs: attr.len_eq});
        }
        return parts;
    }

    function attrPartsElem(attrPart) {
        return chips.elem('li', [
            chips.elem('span', {'class': 'chsl-emphasis'}, [chips.text(attrPart.lhs)]),
            attrPart.op ? chips.text(' ' + attrPart.op + ' ' + attrPart.rhs) : null,
        ]);
    }

    function attrElem(type, attr, optional) {
        return chips.elem('ul', {'class': 'chsl-constraint-list'}, [
            optional ? attrPartsElem({lhs: 'optional'}) : null,
            attrParts(type.array ? 'array' : (type.dict ? 'dict' : 'value'), attr).map(attrPartsElem),
            !optional && !attr ? attrPartsElem({lhs: 'none'}) : null,
        ]);
    }

    function actionInputOutputElem(type, titleTag, title, emptyText) {
        if (!type) {
            return null;
        } else if (type.dict) {
            return actionInputOutputElem(type, titleTag, title);
        }
        return structElem(type.struct, titleTag, title, emptyText);
    }

    function typedefElem(typedef, titleTag, title) {
        titleTag = titleTag || 'h3';
        title = title || 'typedef' + typedef.name;

        return [
            chips.elem(titleTag, {'id': typeHref({typedef: typedef.name})}, [
                chips.elem('a', {'class': 'linktarget'}, [chips.text(title)]),
            ]),
            textElem(typedef.doc),
            chips.elem('table', [
                chips.elem('tr', [
                    chips.elem('th', [chips.text('Type')]),
                    chips.elem('th', [chips.text('Attributes')]),
                ]),
                chips.elem('tr', [
                    chips.elem('td', [typeElem(typedef.type)]),
                    chips.elem('td', [attrElem(typedef.type, typedef.attr, typedef.optional)]),
                ]),
            ]),
        ];
    }

    function structElem(struct, titleTag, title, emptyText) {
        titleTag = titleTag || 'h3';
        title = title || ((struct.union ? 'union ' : 'struct ') + struct.name);
        emptyText = emptyText || 'The struct is empty.';
        var hasDescription = struct.members.reduce(function (prevValue, curValue, index, array) {
            return prevValue || !!curValue.doc;
        }, false);

        return [
            // Section title
            chips.elem(titleTag, {'id': typeHref({struct: struct.name})}, [
                chips.elem('a', {'class': 'linktarget'}, [chips.text(title)]),
            ]),
            textElem(struct.doc),

            // Struct members
            (!struct.members.length ? textElem(emptyText) : [
                chips.elem('table', [
                    chips.elem('tr', [
                        chips.elem('th', [chips.text('Name')]),
                        chips.elem('th', [chips.text('Type')]),
                        chips.elem('th', [chips.text('Attributes')]),
                        hasDescription ? chips.elem('th', [chips.text('Description')]) : null,
                    ]),
                    struct.members.map(function (member) {
                        return chips.elem('tr', [
                            chips.elem('td', [chips.text(member.name)]),
                            chips.elem('td', [typeElem(member.type)]),
                            chips.elem('td', [attrElem(member.type, member.attr, member.optional)]),
                            hasDescription ? chips.elem('td', [textElem(member.doc)]) : null,
                        ]);
                    }),
                ])
            ]),
        ];
    }

    function enumElem(enum_, titleTag, title, emptyText) {
        titleTag = titleTag || 'h3';
        title = title || ('enum ' + enum_.name);
        emptyText = emptyText || 'The enum is empty.';
        var hasDescription = enum_.values.reduce(function (prevValue, curValue, index, array) {
            return prevValue || !!curValue.doc;
        }, false);

        return [
            // Section title
            chips.elem(titleTag, {'id': typeHref({'enum': enum_.name})}, [
                chips.elem('a', {'class': 'linktarget'}, [chips.text(title)]),
            ]),
            textElem(enum_.doc),

            // Enum values
            (!enum_.values.length ? textElem(emptyText) : [
                chips.elem('table', [
                    chips.elem('tr', [
                        chips.elem('th', [chips.text('Value')]),
                        hasDescription ? chips.elem('th', [chips.text('Description')]) : null,
                    ]),
                    enum_.values.map(function (value) {
                        return chips.elem('tr', [
                            chips.elem('td', [chips.text(value.value)]),
                            hasDescription ? chips.elem('td', [textElem(value.doc)]) : null,
                        ]);
                    }),
                ]),
            ]),
        ];
    }

    module.main = function (body) {
        // Listen for hash parameter changes
        window.onhashchange = function () {
            module.main(body);
        };

        // Index page?
        var params = chips.decodeParams();
        if (undefined !== params.name) {
            module.request(body, params);
        } else {
            module.index(body, params);
        }
    };

    return module;
}());
