import * as chisel from './chisel.js';

function indexPage(body, params) {
    chisel.xhr('get', 'doc_index', {
        onerror: function(error) { errorPage(body, error); },
        onok: function (index) {
            let title = window.location.host;
            document.title = title;

            chisel.render(body, [
                // Title
                chisel.elem('h1', [chisel.text(title)]),

                // Groups
                Object.keys(index.groups).map(function (group, group_ix) {
                    return [
                        chisel.elem('h2', [chisel.text(group)]),
                        chisel.elem('ul', {'class': 'chsl-request-list'}, [
                            chisel.elem('li', index.groups[group].map(function (name) {
                                return chisel.elem('li', [
                                    chisel.elem('a', {'href': chisel.href({'name': name})}, [chisel.text(name)]),
                                ]);
                            })),
                        ])
                    ];
                })
            ]);
        },
    });
}

function requestPage(body, params) {
    chisel.xhr('get', 'doc_request', {
        params: {name: params.name},
        onerror: function(error) { errorPage(body, error); },
        onok: function (request) {
            document.title = params.name;

            chisel.render(body, [
                // Navigation bar
                (request.hide_nav ? null : chisel.elem('div', {'class': 'chsl-header'}, [
                    chisel.elem('a', {'href': chisel.href()}, [chisel.text('Back to documentation index')]),
                ])),

                // Title
                chisel.elem('h1', [
                    chisel.text(request.name),
                ]),
                textElem(request.doc),

                // Notes
                chisel.elem('div', {'class': 'chsl-notes'}, [
                    // Request URLs note
                    (!request.urls.length ? null : chisel.elem('div', {'class': 'chsl-note'}, [
                        chisel.elem('p', [
                            chisel.elem('b', [chisel.text('Note: ')]),
                            chisel.text('The request is exposed at the following URL' + (request.urls.length > 1 ? 's:' : ':')),
                            chisel.elem('ul', request.urls.map(function (url) {
                                return chisel.elem('li', [
                                    chisel.elem('a', {'href': url.url}, [chisel.text(url.method ? url.method + ' ' + url.url : url.url)]),
                                ]);
                            })),
                        ]),
                    ])),

                    // Action non-default response note
                    (!request.action || request.action.output ? null : chisel.elem('div', {'class': 'chsl-note'}, [
                        chisel.elem('p', [
                            chisel.elem('b', [chisel.text('Note: ')]),
                            chisel.text('The action has a non-default response. See documentation for details.'),
                        ]),
                    ])),

                    // Action?
                    (!request.action ? null : [
                        structElem(request.action.path, 'h2', 'Path Parameters', 'The action has no path parameters.'),
                        structElem(request.action.query, 'h2', 'Query Parameters', 'The action has no query parameters.'),
                        structElem(request.action.input, 'h2', 'Input Parameters', 'The action has no input parameters.'),
                        structElem(request.action.output, 'h2', 'Output Parameters', 'The action has no output parameters.'),
                        enumElem(request.action.errors, 'h2', 'Error Codes', 'The action returns no custom error codes.'),

                        // Typedefs
                        (!request.typedefs ? null : [
                            chisel.elem('h2', [chisel.text('Typedefs')]),
                            request.typedefs.map(function (typedef) {
                                return typedefElem(typedef);
                            }),
                        ]),

                        // Structs
                        (!request.structs ? null : [
                            chisel.elem('h2', chisel.text('Struct Types')),
                            request.structs.map(function (struct) {
                                return structElem(struct);
                            }),
                        ]),

                        // Enums
                        (!request.enums ? null : [
                            chisel.elem('h2', chisel.text('Enum Types')),
                            request.enums.map(function (enum_) {
                                return enumElem(enum_);
                            }),
                        ]),
                    ]),
                ]),
            ]);
        }
    });
}

function errorPage(body, params) {
    if (undefined !== params.error) {
        chisel.render(body, chisel.text('Error: ' + params.error));
    } else {
        chisel.render(body, chisel.text('An unexpected error occurred'));
    }
}

function textElem(lines) {
    let divElems = [];
    let paragraph = [];
    if (Array.isArray(lines)) {
        for (let iLine = 0; iLine < lines.length; iLine++) {
            if (lines[iLine].length) {
                paragraph.push(lines[iLine]);
            } else if (paragraph.length) {
                divElems.push(chisel.elem('p', chisel.text(paragraph.join('\n'))));
                paragraph = [];
            }
        }
    } else if (lines) {
        paragraph.push(lines);
    }
    if (paragraph.length) {
        divElems.push(chisel.elem('p', [chisel.text(paragraph.join('\n'))]));
    }
    return divElems.length ? chisel.elem('div', {'class': 'chsl-text'}, divElems) : null;
}

function typeHref(type) {
    // TODO: avoid decoding params multiple times
    let paramsOld = chisel.decodeParams();
    let params = {};

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

    return chisel.encodeParams(params);
}

function typeElem(type) {
    if (type.array) {
        return [typeElem(type.array.type), chisel.text(chisel.nbsp + '[]')];
    } else if (type.dict) {
        return [
            type.dict.key_type !== 'string' ? null : [typeElem(type.dict.key_type), chisel.text(chisel.nbsp + ':' + chisel.nbsp)],
            typeElem(type.dict.type), chisel.text(chisel.nbsp + '{}')
        ];
    } else if (type['enum']) {
        return chisel.elem('a', {href: '#' + typeHref(type)}, [chisel.text(type['enum'])]);
    } else if (type.struct) {
        return chisel.elem('a', {href: '#' + typeHref(type)}, [chisel.text(type.struct)]);
    } else if (type.typedef) {
        return chisel.elem('a', {href: '#' + typeHref(type)}, [chisel.text(type.typedef)]);
    }
    return chisel.text(type.builtin);
}

function attrParts(typeName, attr) {
    let parts = [];
    if (attr && undefined !== attr.gt) {
        parts.push({lhs: typeName, op: '>', rhs: attr.gt});
    }
    if (attr && undefined !== attr.gte) {
        parts.push({lhs: typeName, op: '>=', rhs: attr.gte});
    }
    if (attr && undefined !== attr.lt) {
        parts.push({lhs: typeName, op: '<', rhs: attr.lt});
    }
    if (attr && undefined !== attr.lte) {
        parts.push({lhs: typeName, op: '<=', rhs: attr.lte});
    }
    if (attr && undefined !== attr.eq) {
        parts.push({lhs: typeName, op: '==', rhs: attr.eq});
    }
    if (attr && undefined !== attr.len_gt) {
        parts.push({lhs: 'len(' + typeName + ')', op: '>', rhs: attr.len_gt});
    }
    if (attr && undefined !== attr.len_gte) {
        parts.push({lhs: 'len(' + typeName + ')', op: '>=', rhs: attr.len_gte});
    }
    if (attr && undefined !== attr.len_lt) {
        parts.push({lhs: 'len(' + typeName + ')', op: '<', rhs: attr.len_lt});
    }
    if (attr && undefined !== attr.len_lte) {
        parts.push({lhs: 'len(' + typeName + ')', op: '<=', rhs: attr.len_lte});
    }
    if (attr && undefined !== attr.len_eq) {
        parts.push({lhs: 'len(' + typeName + ')', op: '==', rhs: attr.len_eq});
    }
    return parts;
}

function attrPartsElem(attrPart) {
    return chisel.elem('li', [
        chisel.elem('span', {'class': 'chsl-emphasis'}, [chisel.text(attrPart.lhs)]),
        attrPart.op ? chisel.text(' ' + attrPart.op + ' ' + attrPart.rhs) : null,
    ]);
}

function attrElem(type, attr, optional, nullable) {
    return chisel.elem('ul', {'class': 'chsl-constraint-list'}, [
        optional ? attrPartsElem({lhs: 'optional'}) : null,
        nullable ? attrPartsElem({lhs: 'nullable'}) : null,
        attrParts(type.array ? 'array' : (type.dict ? 'dict' : 'value'), attr).map(attrPartsElem)
    ]);
}

function typedefElem(typedef, titleTag, title) {
    titleTag = titleTag || 'h3';
    title = title || 'typedef ' + typedef.name;
    let hasAttributes = !!typedef.attr;

    return [
        chisel.elem(titleTag, {'id': typeHref({typedef: typedef.name})}, [
            chisel.elem('a', {'class': 'linktarget'}, [chisel.text(title)]),
        ]),
        textElem(typedef.doc),
        chisel.elem('table', [
            chisel.elem('tr', [
                chisel.elem('th', [chisel.text('Type')]),
                hasAttributes ? chisel.elem('th', [chisel.text('Attributes')]) : null,
            ]),
            chisel.elem('tr', [
                chisel.elem('td', [typeElem(typedef.type)]),
                hasAttributes ? chisel.elem('td', [attrElem(typedef.type, typedef.attr, false, false)]) : null,
            ]),
        ]),
    ];
}

function structElem(struct, titleTag, title, emptyText) {
    titleTag = titleTag || 'h3';
    title = title || ((struct.union ? 'union ' : 'struct ') + struct.name);
    emptyText = emptyText || 'The struct is empty.';
    let hasAttributes = struct.members.reduce(function (prevValue, curValue, index, array) {
        return prevValue || !!(curValue.optional || curValue.nullable || curValue.attr);
    }, false);
    let hasDescription = struct.members.reduce(function (prevValue, curValue, index, array) {
        return prevValue || !!curValue.doc;
    }, false);

    return [
        // Section title
        chisel.elem(titleTag, {'id': typeHref({struct: struct.name})}, [
            chisel.elem('a', {'class': 'linktarget'}, [chisel.text(title)]),
        ]),
        textElem(struct.doc),

        // Struct members
        (!struct.members.length ? textElem(emptyText) : [
            chisel.elem('table', [
                chisel.elem('tr', [
                    chisel.elem('th', [chisel.text('Name')]),
                    chisel.elem('th', [chisel.text('Type')]),
                    hasAttributes ? chisel.elem('th', [chisel.text('Attributes')]) : null,
                    hasDescription ? chisel.elem('th', [chisel.text('Description')]) : null,
                ]),
                struct.members.map(function (member) {
                    return chisel.elem('tr', [
                        chisel.elem('td', [chisel.text(member.name)]),
                        chisel.elem('td', [typeElem(member.type)]),
                        hasAttributes ? chisel.elem('td', [attrElem(member.type, member.attr, member.optional, member.nullable)]) : null,
                        hasDescription ? chisel.elem('td', [textElem(member.doc)]) : null,
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
    let hasDescription = enum_.values.reduce(function (prevValue, curValue, index, array) {
        return prevValue || !!curValue.doc;
    }, false);

    return [
        // Section title
        chisel.elem(titleTag, {'id': typeHref({'enum': enum_.name})}, [
            chisel.elem('a', {'class': 'linktarget'}, [chisel.text(title)]),
        ]),
        textElem(enum_.doc),

        // Enum values
        (!enum_.values.length ? textElem(emptyText) : [
            chisel.elem('table', [
                chisel.elem('tr', [
                    chisel.elem('th', [chisel.text('Value')]),
                    hasDescription ? chisel.elem('th', [chisel.text('Description')]) : null,
                ]),
                enum_.values.map(function (value) {
                    return chisel.elem('tr', [
                        chisel.elem('td', [chisel.text(value.value)]),
                        hasDescription ? chisel.elem('td', [textElem(value.doc)]) : null,
                    ]);
                }),
            ]),
        ]),
    ];
}

export function main(body) {
    // Listen for hash parameter changes
    window.onhashchange = function () {
        main(body);
    };

    // Index page?
    let params = chisel.decodeParams();
    if (undefined !== params.name) {
        requestPage(body, params);
    } else {
        indexPage(body, params);
    }
}
