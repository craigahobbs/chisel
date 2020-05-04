// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import * as chisel from './chisel.js';


export class DocPage {
    render() {
        const params = chisel.decodeParams();
        this.params = params;
        if (typeof params.name !== 'undefined') {
            chisel.xhr('get', 'doc_request', {
                'params': {
                    'name': params.name
                },
                'onerror': (error) => {
                    chisel.render(document.body, DocPage.errorPage(error));
                },
                'onok': (request) => {
                    document.title = params.name;
                    chisel.render(document.body, this.requestPage(request));
                }
            });
        } else {
            chisel.xhr('get', 'doc_index', {
                'onerror': (error) => {
                    chisel.render(document.body, DocPage.errorPage(error));
                },
                'onok': (index) => {
                    document.title = window.location.host;
                    chisel.render(document.body, DocPage.indexPage(window.location.host, index));
                }
            });
        }
    }

    static errorPage(params) {
        if (typeof params.error === 'undefined') {
            return chisel.text('An unexpected error occurred');
        }
        return chisel.text(`Error: ${params.error}`);
    }

    static indexPage(title, index) {
        return [
            // Title
            chisel.elem('h1', null, chisel.text(title)),

            // Groups
            Object.keys(index.groups).sort().map((group) => [
                chisel.elem('h2', null, chisel.text(group)),
                chisel.elem(
                    'ul', {'class': 'chisel-request-list'},
                    chisel.elem('li', null, chisel.elem('ul', null, index.groups[group].sort().map(
                        (name) => chisel.elem('li', null, chisel.elem('a', {'href': chisel.href({'name': name})}, chisel.text(name)))
                    )))
                )
            ])
        ];
    }

    requestPage(request) {
        return [
            // Navigation bar
            chisel.elem(
                'div',
                {'class': 'chisel-header'},
                chisel.elem('a', {'href': chisel.href()}, chisel.text('Back to documentation index'))
            ),

            // Title
            chisel.elem('h1', null, chisel.text(request.name)),
            DocPage.textElem(request.doc),

            // Notes
            chisel.elem('div', {'class': 'chisel-notes'}, [
                // Request URLs note
                (!request.urls.length ? null : chisel.elem('div', null, [
                    chisel.elem('p', null, [
                        chisel.elem('b', null, chisel.text('Note: ')),
                        chisel.text(`The request is exposed at the following URL ${request.urls.length > 1 ? 's:' : ':'}`),
                        chisel.elem('ul', null, request.urls.map((url) => chisel.elem('li', null, [
                            chisel.elem('a', {'href': url.url}, chisel.text(url.method ? `${url.method} ${url.url}` : url.url))
                        ])))
                    ])
                ])),

                // Action non-default response note
                (!request.action || request.action.output ? null : chisel.elem('div', null, [
                    chisel.elem('p', null, [
                        chisel.elem('b', null, chisel.text('Note: ')),
                        chisel.text('The action has a non-default response. See documentation for details.')
                    ])
                ])),

                // Action?
                (!request.action ? null : [
                    this.structElem(request.action.path, 'h2', 'Path Parameters', 'The action has no path parameters.'),
                    this.structElem(request.action.query, 'h2', 'Query Parameters', 'The action has no query parameters.'),
                    this.structElem(request.action.input, 'h2', 'Input Parameters', 'The action has no input parameters.'),
                    this.structElem(request.action.output, 'h2', 'Output Parameters', 'The action has no output parameters.'),
                    this.enumElem(request.action.errors, 'h2', 'Error Codes', 'The action returns no custom error codes.'),

                    // Typedefs
                    (!request.typedefs ? null : [
                        chisel.elem('h2', null, chisel.text('Typedefs')),
                        request.typedefs.map((typedef) => this.typedefElem(typedef, 'h3', `typedef ${typedef.name}`))
                    ]),

                    // Structs
                    (!request.structs ? null : [
                        chisel.elem('h2', null, chisel.text('Struct Types')),
                        request.structs.map((struct) => this.structElem(
                            struct,
                            'h3',
                            `${struct.union ? 'union' : 'struct'} ${struct.name}`, 'The struct is empty.'
                        ))
                    ]),

                    // Enums
                    (!request.enums ? null : [
                        chisel.elem('h2', null, chisel.text('Enum Types')),
                        request.enums.map((enum_) => this.enumElem(enum_, 'h3', `enum ${enum_.name}`, 'The enum is empty.'))
                    ])
                ])
            ])
        ];
    }

    static textElem(lines) {
        const divElems = [];
        let paragraph = [];
        if (Array.isArray(lines)) {
            for (let iLine = 0; iLine < lines.length; iLine++) {
                if (lines[iLine].length) {
                    paragraph.push(lines[iLine]);
                } else if (paragraph.length) {
                    divElems.push(chisel.elem('p', null, chisel.text(paragraph.join('\n'))));
                    paragraph = [];
                }
            }
        } else if (lines) {
            paragraph.push(lines);
        }
        if (paragraph.length) {
            divElems.push(chisel.elem('p', null, chisel.text(paragraph.join('\n'))));
        }
        return divElems.length ? chisel.elem('div', null, divElems) : null;
    }

    typeHref(type) {
        const href = chisel.encodeParams({'name': this.params.name});
        if (typeof type.typedef !== 'undefined') {
            return `${href}&typedef_${type.typedef}`;
        } else if (typeof type.enum !== 'undefined') {
            return `${href}&enum_${type.enum}`;
        }
        return `${href}&struct_${type.struct}`;
    }

    typeElem(type) {
        if (typeof type.array !== 'undefined') {
            return [this.typeElem(type.array.type), chisel.text(`${chisel.nbsp}[]`)];
        } else if (typeof type.dict !== 'undefined') {
            return [
                type.dict.key_type !== 'string' ? null : [this.typeElem(type.dict.key_type), chisel.text(`${chisel.nbsp}:${chisel.nbsp}`)],
                this.typeElem(type.dict.type),
                chisel.text(`${chisel.nbsp}{}`)
            ];
        } else if (typeof type.enum !== 'undefined') {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.enum));
        } else if (typeof type.struct !== 'undefined') {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.struct));
        } else if (typeof type.typedef !== 'undefined') {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.typedef));
        }
        return chisel.text(type.builtin);
    }

    static attrParts(typeName, attr) {
        const parts = [];
        if (attr !== null && typeof attr.gt !== 'undefined') {
            parts.push({'lhs': typeName, 'op': '>', 'rhs': attr.gt});
        }
        if (attr !== null && typeof attr.gte !== 'undefined') {
            parts.push({'lhs': typeName, 'op': '>=', 'rhs': attr.gte});
        }
        if (attr !== null && typeof attr.lt !== 'undefined') {
            parts.push({'lhs': typeName, 'op': '<', 'rhs': attr.lt});
        }
        if (attr !== null && typeof attr.lte !== 'undefined') {
            parts.push({'lhs': typeName, 'op': '<=', 'rhs': attr.lte});
        }
        if (attr !== null && typeof attr.eq !== 'undefined') {
            parts.push({'lhs': typeName, 'op': '==', 'rhs': attr.eq});
        }
        if (attr !== null && typeof attr.len_gt !== 'undefined') {
            parts.push({'lhs': `len(${typeName})`, 'op': '>', 'rhs': attr.len_gt});
        }
        if (attr !== null && typeof attr.len_gte !== 'undefined') {
            parts.push({'lhs': `len(${typeName})`, 'op': '>=', 'rhs': attr.len_gte});
        }
        if (attr !== null && typeof attr.len_lt !== 'undefined') {
            parts.push({'lhs': `len(${typeName})`, 'op': '<', 'rhs': attr.len_lt});
        }
        if (attr !== null && typeof attr.len_lte !== 'undefined') {
            parts.push({'lhs': `len(${typeName})`, 'op': '<=', 'rhs': attr.len_lte});
        }
        if (attr !== null && typeof attr.len_eq !== 'undefined') {
            parts.push({'lhs': `len(${typeName})`, 'op': '==', 'rhs': attr.len_eq});
        }
        return parts;
    }

    static attrPartsElem(attrPart) {
        return chisel.elem('li', null, [
            chisel.elem('span', {'class': 'chisel-emphasis'}, chisel.text(attrPart.lhs)),
            attrPart.op ? chisel.text(` ${attrPart.op} ${attrPart.rhs}`) : null
        ]);
    }

    static attrElem({type, attr = null}, optional, nullable) {
        return chisel.elem('ul', {'class': 'chisel-constraint-list'}, [
            optional ? DocPage.attrPartsElem({'lhs': 'optional'}) : null,
            nullable ? DocPage.attrPartsElem({'lhs': 'nullable'}) : null,
            DocPage.attrParts(type.array ? 'array' : (type.dict ? 'dict' : 'value'), attr).map(DocPage.attrPartsElem)
        ]);
    }

    typedefElem(typedef, titleTag, title) {
        const hasAttributes = !!typedef.attr;
        return [
            chisel.elem(titleTag, {'id': this.typeHref({'typedef': typedef.name})}, [
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ]),
            DocPage.textElem(typedef.doc),
            chisel.elem('table', null, [
                chisel.elem('tr', null, [
                    chisel.elem('th', null, chisel.text('Type')),
                    hasAttributes ? chisel.elem('th', null, chisel.text('Attributes')) : null
                ]),
                chisel.elem('tr', null, [
                    chisel.elem('td', null, [this.typeElem(typedef.type)]),
                    hasAttributes ? chisel.elem('td', null, DocPage.attrElem(typedef, false, false)) : null
                ])
            ])
        ];
    }

    structElem(struct, titleTag, title, emptyText) {
        const hasAttributes = struct.members.reduce(
            (prevValue, curValue) => prevValue || !!(curValue.optional || curValue.nullable || curValue.attr),
            false
        );
        const hasDescription = struct.members.reduce((prevValue, curValue) => prevValue || !!curValue.doc, false);
        return [
            // Section title
            chisel.elem(titleTag, {'id': this.typeHref({'struct': struct.name})}, [
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ]),
            DocPage.textElem(struct.doc),

            // Struct members
            (!struct.members.length ? DocPage.textElem(emptyText) : [
                chisel.elem('table', null, [
                    chisel.elem('tr', null, [
                        chisel.elem('th', null, chisel.text('Name')),
                        chisel.elem('th', null, chisel.text('Type')),
                        hasAttributes ? chisel.elem('th', null, chisel.text('Attributes')) : null,
                        hasDescription ? chisel.elem('th', null, chisel.text('Description')) : null
                    ]),
                    struct.members.map((member) => chisel.elem('tr', null, [
                        chisel.elem('td', null, chisel.text(member.name)),
                        chisel.elem('td', null, this.typeElem(member.type)),
                        hasAttributes
                            ? chisel.elem('td', null, DocPage.attrElem(member, member.optional, member.nullable))
                            : null,
                        hasDescription ? chisel.elem('td', null, DocPage.textElem(member.doc)) : null
                    ]))
                ])
            ])
        ];
    }

    enumElem(enum_, titleTag, title, emptyText) {
        const hasDescription = enum_.values.reduce((prevValue, curValue) => prevValue || !!curValue.doc, false);
        return [
            // Section title
            chisel.elem(titleTag, {'id': this.typeHref({'enum': enum_.name})}, [
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ]),
            DocPage.textElem(enum_.doc),

            // Enum values
            (!enum_.values.length ? DocPage.textElem(emptyText) : [
                chisel.elem('table', null, [
                    chisel.elem('tr', null, [
                        chisel.elem('th', chisel.text('Value')),
                        hasDescription ? chisel.elem('th', null, chisel.text('Description')) : null
                    ]),
                    enum_.values.map((value) => chisel.elem('tr', null, [
                        chisel.elem('td', null, chisel.text(value.value)),
                        hasDescription ? chisel.elem('td', null, DocPage.textElem(value.doc)) : null
                    ]))
                ])
            ])
        ];
    }
}
