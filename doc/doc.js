// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import * as chisel from './chisel.js';


/**
 * The Chisel documentation application.
 *
 * @property {Object} params - The parsed and validated hash parameters object.
 */
export class DocPage {
    /**
     * Create a documentation application instance.
     */
    constructor() {
        this.params = null;
    }

    /**
     * Parse the hash parameters and update this.params.
     */
    updateParams() {
        this.params = chisel.decodeParams();
    }

    /**
     * Render the documentation application page.
     */
    render() {
        const oldParams = this.params;
        this.updateParams();

        // Skip the render if the page hasn't changed
        if (oldParams !== null && oldParams.name === this.params.name) {
            return;
        }

        // Clear the page
        chisel.render(document.body);

        // Render the page
        if ('name' in this.params) {
            // Call the request API
            window.fetch(`doc_request/${this.params.name}`).then(
                (response) => response.json()
            ).then((response) => {
                if ('error' in response) {
                    chisel.render(document.body, DocPage.errorPage(response.error));
                } else {
                    document.title = response.name;
                    chisel.render(document.body, this.requestPage(response));
                }
            }).catch(() => {
                chisel.render(document.body, DocPage.errorPage());
            });
        } else {
            // Call the index API
            window.fetch('doc_index').then(
                (response) => response.json()
            ).then((response) => {
                if ('error' in response) {
                    chisel.render(document.body, DocPage.errorPage(response.error));
                } else {
                    document.title = response.title;
                    chisel.render(document.body, DocPage.indexPage(response));
                }
            }).catch(() => {
                chisel.render(document.body, DocPage.errorPage());
            });
        }
    }

    /**
     * Helper function to generate the error page's chisel.js element hierarchy model.
     *
     * @param {string} [error=null] - The error code. If null, an unexpected error is reported.
     * @return {Object}
     */
    static errorPage(error = null) {
        return chisel.text(error !== null ? `Error: ${error}` : 'An unexpected error occurred.');
    }

    /**
     * Helper function to generate the index page's chisel.js element hierarchy model.
     *
     * @param {Object} index - The Chisel documentation index API response.
     * @returns {Array}
     */
    static indexPage(index) {
        return [
            // Title
            chisel.elem('h1', null, chisel.text(index.title)),

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

    /**
     * Helper function to generate the request page's chisel.js element hierarchy model.
     *
     * @param {Object} request - The Chisel documentation request API response.
     * @returns {Array}
     */
    requestPage(request) {
        const isAction = 'action' in request;
        const isCustomResponse = isAction && !('output' in request.action);
        return [
            // Navigation bar
            chisel.elem('p', null, chisel.elem('a', {'href': chisel.href()}, chisel.text('Back to documentation index'))),

            // Title
            chisel.elem('h1', null, chisel.text(request.name)),
            DocPage.textElem(request.doc),

            // Request URLs note
            !request.urls.length ? null : chisel.elem('p', {'class': 'chisel-note'}, [
                chisel.elem('b', null, chisel.text('Note: ')),
                chisel.text(`The request is exposed at the following ${request.urls.length > 1 ? 'URLs:' : 'URL:'}`),
                chisel.elem('ul', null, request.urls.map((url) => chisel.elem('li', null, [
                    chisel.elem('a', {'href': url.url}, chisel.text(url.method ? `${url.method} ${url.url}` : url.url))
                ])))
            ]),

            // Action non-default response note
            !isCustomResponse ? null : chisel.elem('p', {'class': 'chisel-note'}, [
                chisel.elem('b', null, chisel.text('Note: ')),
                chisel.text('The action has a non-default response. See documentation for details.')
            ]),

            // Action sections
            !(isAction && request.action.path.members.length) ? null : this.structElem(request.action.path, 'h2', 'Path Parameters'),
            !(isAction && request.action.query.members.length) ? null : this.structElem(request.action.query, 'h2', 'Query Parameters'),
            !(isAction && request.action.input.members.length) ? null : this.structElem(request.action.input, 'h2', 'Input Parameters'),
            !(isAction && !isCustomResponse && request.action.output.members.length) ? null
                : this.structElem(request.action.output, 'h2', 'Output Parameters'),
            !(isAction && request.action.errors.values.length) ? null : this.enumElem(request.action.errors, 'h2', 'Error Codes'),

            // Typedefs
            !('typedefs' in request) ? null : [
                chisel.elem('h2', null, chisel.text('Typedefs')),
                request.typedefs.map((typedef) => this.typedefElem(typedef, 'h3', `typedef ${typedef.name}`))
            ],

            // Structs
            !('structs' in request) ? null : [
                chisel.elem('h2', null, chisel.text('Struct Types')),
                request.structs.map(
                    (struct) => this.structElem(struct, 'h3', `${struct.union ? 'union' : 'struct'} ${struct.name}`)
                )
            ],

            // Enums
            !('enums' in request) ? null : [
                chisel.elem('h2', null, chisel.text('Enum Types')),
                request.enums.map((enum_) => this.enumElem(enum_, 'h3', `enum ${enum_.name}`))
            ]
        ];
    }

    /**
     * Helper function to generate a text block's chisel.js element hierarchy model.
     *
     * @param {string} [text=null] - Markdown text
     * @returns {?Array}
     */
    static textElem(text = null) {
        const elems = [];

        // Organize lines into paragraphs
        if (text !== null) {
            const lines = text.split('\n');
            let paragraph = [];
            for (let iLine = 0; iLine < lines.length; iLine++) {
                if (lines[iLine].length) {
                    paragraph.push(lines[iLine]);
                } else if (paragraph.length) {
                    elems.push(chisel.elem('p', null, chisel.text(paragraph.join('\n'))));
                    paragraph = [];
                }
            }
            if (paragraph.length) {
                elems.push(chisel.elem('p', null, chisel.text(paragraph.join('\n'))));
            }
        }

        // If there are no elements return null
        return elems.length ? elems : null;
    }

    /**
     * Helper method to get a type href (target).
     *
     * @param {Object} type - The Chisel documentation request API type union.
     * @return {string}
     */
    typeHref(type) {
        const href = chisel.encodeParams({'name': this.params.name});
        if ('typedef' in type) {
            return `${href}&typedef_${type.typedef}`;
        } else if ('enum' in type) {
            return `${href}&enum_${type.enum}`;
        }
        return `${href}&struct_${type.struct}`;
    }

    /**
     * Helper method to generate a member/typedef type's chisel.js element hierarchy model.
     *
     * @param {Object} type - The Chisel documentation request API type union.
     * @returns {(Object|Array)}
     */
    typeElem(type) {
        if ('array' in type) {
            return [this.typeElem(type.array.type), chisel.text(`${chisel.nbsp}[]`)];
        } else if ('dict' in type) {
            return [
                type.dict.key_type.builtin === 'string' ? null
                    : [this.typeElem(type.dict.key_type), chisel.text(`${chisel.nbsp}:${chisel.nbsp}`)],
                this.typeElem(type.dict.type),
                chisel.text(`${chisel.nbsp}{}`)
            ];
        } else if ('enum' in type) {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.enum));
        } else if ('struct' in type) {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.struct));
        } else if ('typedef' in type) {
            return chisel.elem('a', {'href': `#${this.typeHref(type)}`}, chisel.text(type.typedef));
        }
        return chisel.text(type.builtin);
    }

    /**
     * Helper method to generate a member/typedef's attributes chisel.js element hierarchy model.
     *
     * @param {Object} memberOrTypedef - Chisel documentation request API member or typedef.
     * @param {Object} memberOrTypedef.type - The Chisel documentation request API type.
     * @param {Object} [memberOrTypedef.attr=null] - The Chisel documentation request API attributes.
     * @param {boolean} [memberOrTypedef.optional=false] - If true, the member is optional.
     * @param {boolean} [memberOrTypedef.nullable=false] - If true, the member is nullable.
     * @returns {(null|Array)}
     */
    static attrElem({type, attr = null, optional = false, nullable = false}) {
        // Create the array of attribute "parts" (lhs, op, rhs)
        const parts = [];
        const typeName = type.array ? 'array' : (type.dict ? 'dict' : 'value');
        if (optional) {
            parts.push({'lhs': 'optional'});
        }
        if (nullable) {
            parts.push({'lhs': 'nullable'});
        }
        if (attr !== null && 'gt' in attr) {
            parts.push({'lhs': typeName, 'op': '>', 'rhs': attr.gt});
        }
        if (attr !== null && 'gte' in attr) {
            parts.push({'lhs': typeName, 'op': '>=', 'rhs': attr.gte});
        }
        if (attr !== null && 'lt' in attr) {
            parts.push({'lhs': typeName, 'op': '<', 'rhs': attr.lt});
        }
        if (attr !== null && 'lte' in attr) {
            parts.push({'lhs': typeName, 'op': '<=', 'rhs': attr.lte});
        }
        if (attr !== null && 'eq' in attr) {
            parts.push({'lhs': typeName, 'op': '==', 'rhs': attr.eq});
        }
        if (attr !== null && 'len_gt' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '>', 'rhs': attr.len_gt});
        }
        if (attr !== null && 'len_gte' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '>=', 'rhs': attr.len_gte});
        }
        if (attr !== null && 'len_lt' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '<', 'rhs': attr.len_lt});
        }
        if (attr !== null && 'len_lte' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '<=', 'rhs': attr.len_lte});
        }
        if (attr !== null && 'len_eq' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '==', 'rhs': attr.len_eq});
        }

        // Return the attributes element hierarchy model
        return !parts.length ? null : chisel.elem('ul', {'class': 'chisel-attr-list'}, parts.map(
            (part) => chisel.elem(
                'li',
                null,
                chisel.text(part.op ? `${part.lhs}${chisel.nbsp}${part.op}${chisel.nbsp}${part.rhs}` : part.lhs)
            )
        ));
    }

    /**
     * Helper method to generate a typedef's chisel.js element hierarchy model.
     *
     * @param {Object} typedef - The Chisel documentation request API typedef.
     * @param {string} titleTag - The HTML tag for the typedef title element.
     * @param {string} title - The typedef section's title string.
     * @returns {Array}
     */
    typedefElem(typedef, titleTag, title) {
        const hasAttributes = !!typedef.attr;
        return [
            chisel.elem(
                titleTag,
                {'id': this.typeHref({'typedef': typedef.name})},
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ),
            DocPage.textElem(typedef.doc),
            chisel.elem('table', null, [
                chisel.elem('tr', null, [
                    chisel.elem('th', null, chisel.text('Type')),
                    hasAttributes ? chisel.elem('th', null, chisel.text('Attributes')) : null
                ]),
                chisel.elem('tr', null, [
                    chisel.elem('td', null, [this.typeElem(typedef.type)]),
                    hasAttributes ? chisel.elem('td', null, DocPage.attrElem(typedef)) : null
                ])
            ])
        ];
    }

    /**
     * Helper method to generate a struct's chisel.js element hierarchy model.
     *
     * @param {Object} struct - The Chisel documentation request API struct.
     * @param {string} titleTag - The HTML tag for the struct title element.
     * @param {string} title - The struct section's title string.
     * @returns {Array}
     */
    structElem(struct, titleTag, title) {
        const hasAttributes = struct.members.reduce(
            (prevValue, curValue) => prevValue || !!(curValue.optional || curValue.nullable || curValue.attr),
            false
        );
        const hasDescription = struct.members.reduce((prevValue, curValue) => prevValue || 'doc' in curValue, false);
        return [
            // Section title
            chisel.elem(
                titleTag,
                {'id': this.typeHref({'struct': struct.name})},
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ),
            DocPage.textElem(struct.doc),

            // Struct members
            (!struct.members.length ? DocPage.textElem('The struct is empty.') : chisel.elem('table', null, [
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
                        ? chisel.elem('td', null, DocPage.attrElem(member))
                        : null,
                    hasDescription ? chisel.elem('td', null, DocPage.textElem(member.doc)) : null
                ]))
            ]))
        ];
    }

    /**
     * Helper method to generate a enum's chisel.js element hierarchy model.
     *
     * @param {Object} enum - The Chisel documentation request API enum.
     * @param {string} titleTag - The HTML tag for the enum title element.
     * @param {string} title - The enum section's title string.
     * @returns {Array}
     */
    enumElem(enum_, titleTag, title) {
        const hasDescription = enum_.values.reduce((prevValue, curValue) => prevValue || 'doc' in curValue, false);
        return [
            // Section title
            chisel.elem(
                titleTag,
                {'id': this.typeHref({'enum': enum_.name})},
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ),
            DocPage.textElem(enum_.doc),

            // Enum values
            (!enum_.values.length ? DocPage.textElem('The enum is empty.') : chisel.elem('table', null, [
                chisel.elem('tr', null, [
                    chisel.elem('th', null, chisel.text('Value')),
                    hasDescription ? chisel.elem('th', null, chisel.text('Description')) : null
                ]),
                enum_.values.map((value) => chisel.elem('tr', null, [
                    chisel.elem('td', null, chisel.text(value.value)),
                    hasDescription ? chisel.elem('td', null, DocPage.textElem(value.doc)) : null
                ]))
            ]))
        ];
    }
}
