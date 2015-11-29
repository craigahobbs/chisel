import {decodeParams, elem, encodeParams, href, isArray, nbsp, render, text, xhr} from '../chips.js';

function index(body, params) {
    xhr('get', '/doc_index', true, {
        onok: function (index) {
            let title = window.location.host;
            document.title = title;

            render(body, [
                // Title
                elem('h1', [text(title)]),

                // Request link unordered-list
                elem('ul', {'class': 'chsl-request-list'}, [
                    elem('li', index.names.map(function (name) {
                        return elem('li', [
                            elem('a', {'href': href({'name': name})}, [text(name)]),
                        ]);
                    })),
                ]),
            ], true);
        },
    });
}

function request(body, params) {
    xhr('get', '/doc_request', true, {
        params: {name: params.name},
        onok: function (request) {
            document.title = params.name;

            render(body, [
                // Navigation bar
                (params.nonav === 'true' ? null : elem('div', {'class': 'chsl-header'}, [
                    elem('a', {'href': href()}, [text('Back to documentation index')]),
                ])),

                // Title
                elem('h1', [
                    text(request.name),
                ]),
                textElem(request.doc),

                // Notes
                elem('div', {'class': 'chsl-notes'}, [
                    // Request URLs note
                    (!request.urls.length ? null : elem('div', {'class': 'chsl-note'}, [
                        elem('p', [
                            elem('b', [text('Note: ')]),
                            text('The request is exposed at the following URL' + (request.urls.length > 1 ? 's:' : ':')),
                            elem('ul', request.urls.map(function (url) {
                                return elem('li', [
                                    elem('a', {'href': url.url}, [text(url.method ? url.method + ' ' + url.url : url.url)]),
                                ]);
                            })),
                        ]),
                    ])),

                    // Action non-default response note
                    (!request.action || request.action.output ? null : elem('div', {'class': 'chsl-note'}, [
                        elem('p', [
                            elem('b', [text('Note: ')]),
                            text('The action has a non-default response. See documentation for details.'),
                        ]),
                    ])),

                    // Action?
                    (!request.action ? null : [
                        actionInputOutputElem(request.action.input, 'h2', 'Input Parameters', 'The action has no input parameters.'),
                        actionInputOutputElem(request.action.output, 'h2', 'Output Parameters', 'The action has no output parameters.'),
                        enumElem(request.action.errors, 'h2', 'Error Codes', 'The action returns no custom error codes.'),

                        // Typedefs
                        (!request.typedefs.length ? null : [
                            elem('h2', [text('Typedefs')]),
                            request.typedefs.map(function (typedef) {
                                return typedefElem(typedef);
                            }),
                        ]),

                        // Structs
                        (!request.structs.length ? null : [
                            elem('h2', text('Struct Types')),
                            request.structs.map(function (struct) {
                                return structElem(struct);
                            }),
                        ]),

                        // Enums
                        (!request.enums.length ? null : [
                            elem('h2', text('Enum Types')),
                            request.enums.map(function (enum_) {
                                return enumElem(enum_);
                            }),
                        ]),
                    ]),
                ]),
            ], true);
        }
    });
}

function textElem(lines) {
    let divElems = [];
    let paragraph = [];
    if (isArray(lines)) {
        for (let iLine = 0; iLine < lines.length; iLine++) {
            if (lines[iLine].length) {
                paragraph.push(lines[iLine]);
            } else if (paragraph.length) {
                divElems.push(elem('p', text(paragraph.join('\n'))));
                paragraph = [];
            }
        }
    } else if (lines) {
        paragraph.push(lines);
    }
    if (paragraph.length) {
        divElems.push(elem('p', [text(paragraph.join('\n'))]));
    }
    return divElems.length ? elem('div', {'class': 'chsl-text'}, divElems) : null;
}

function typeHref(type) {
    // TODO: avoid decoding params multiple times
    let paramsOld = decodeParams();
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

    return encodeParams(params);
}

function typeElem(type) {
    if (type.array) {
        return [typeElem(type.array.type), text(nbsp + '[]')];
    } else if (type.dict) {
        return [
            type.dict.key_type !== 'string' ? null : [typeElem(type.dict.key_type), text(nbsp + ':' + nbsp)],
            typeElem(type.dict.type), text(nbsp + '{}')
        ];
    } else if (type['enum']) {
        return elem('a', {href: '#' + typeHref(type)}, [text(type['enum'])]);
    } else if (type.struct) {
        return elem('a', {href: '#' + typeHref(type)}, [text(type.struct)]);
    } else if (type.typedef) {
        return elem('a', {href: '#' + typeHref(type)}, [text(type.typedef)]);
    }
    return text(type.builtin);
}

function attrParts(typeName, attr) {
    let parts = [];
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
    return elem('li', [
        elem('span', {'class': 'chsl-emphasis'}, [text(attrPart.lhs)]),
        attrPart.op ? text(' ' + attrPart.op + ' ' + attrPart.rhs) : null,
    ]);
}

function attrElem(type, attr, optional) {
    return elem('ul', {'class': 'chsl-constraint-list'}, [
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
        elem(titleTag, {'id': typeHref({typedef: typedef.name})}, [
            elem('a', {'class': 'linktarget'}, [text(title)]),
        ]),
        textElem(typedef.doc),
        elem('table', [
            elem('tr', [
                elem('th', [text('Type')]),
                elem('th', [text('Attributes')]),
            ]),
            elem('tr', [
                elem('td', [typeElem(typedef.type)]),
                elem('td', [attrElem(typedef.type, typedef.attr, typedef.optional)]),
            ]),
        ]),
    ];
}

function structElem(struct, titleTag, title, emptyText) {
    titleTag = titleTag || 'h3';
    title = title || ((struct.union ? 'union ' : 'struct ') + struct.name);
    emptyText = emptyText || 'The struct is empty.';
    let hasDescription = struct.members.reduce(function (prevValue, curValue, index, array) {
        return prevValue || !!curValue.doc;
    }, false);

    return [
        // Section title
        elem(titleTag, {'id': typeHref({struct: struct.name})}, [
            elem('a', {'class': 'linktarget'}, [text(title)]),
        ]),
        textElem(struct.doc),

        // Struct members
        (!struct.members.length ? textElem(emptyText) : [
            elem('table', [
                elem('tr', [
                    elem('th', [text('Name')]),
                    elem('th', [text('Type')]),
                    elem('th', [text('Attributes')]),
                    hasDescription ? elem('th', [text('Description')]) : null,
                ]),
                struct.members.map(function (member) {
                    return elem('tr', [
                        elem('td', [text(member.name)]),
                        elem('td', [typeElem(member.type)]),
                        elem('td', [attrElem(member.type, member.attr, member.optional)]),
                        hasDescription ? elem('td', [textElem(member.doc)]) : null,
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
        elem(titleTag, {'id': typeHref({'enum': enum_.name})}, [
            elem('a', {'class': 'linktarget'}, [text(title)]),
        ]),
        textElem(enum_.doc),

        // Enum values
        (!enum_.values.length ? textElem(emptyText) : [
            elem('table', [
                elem('tr', [
                    elem('th', [text('Value')]),
                    hasDescription ? elem('th', [text('Description')]) : null,
                ]),
                enum_.values.map(function (value) {
                    return elem('tr', [
                        elem('td', [text(value.value)]),
                        hasDescription ? elem('td', [textElem(value.doc)]) : null,
                    ]);
                }),
            ]),
        ]),
    ];
}

function main(body) {
    // Listen for hash parameter changes
    window.onhashchange = function () {
        main(body);
    };

    // Index page?
    let params = decodeParams();
    if (undefined !== params.name) {
        request(body, params);
    } else {
        index(body, params);
    }
}

main(document.body);
