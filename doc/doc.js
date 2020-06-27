// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import * as chisel from './chisel.js';


/**
 * The Chisel documentation application hash parameters type model specification
 *
 * Compile the specification below with the following command:
 *
 * <pre><code>
 * python3 -m chisel compile <spec_file>
 * </code></pre>
 *
 * <pre><code>
 * # The Chisel documentation application hash parameters struct
 * struct DocPageParams
 *
 *     # Request name to render documentation. If not provided, the request index is displayed.
 *     optional string(len > 0) name
 * </code></pre>
 */
const docPageTypes = {
    'DocPageParams': {
        'struct': {
            'name': 'DocPageParams',
            'doc': 'The Chisel documentation application hash parameters struct',
            'members': [
                {
                    'name': 'name',
                    'doc': 'Request name to render documentation. If not provided, the request index is displayed.',
                    'type': {'builtin': 'string'},
                    'attr': {'len_gt': 0},
                    'optional': true
                }
            ]
        }
    }
};


/**
 * The Chisel documentation application
 *
 * @property {Object} params - The parsed and validated hash parameters object.
 */
export class DocPage {
    /**
     * Create a documentation application instance
     */
    constructor() {
        this.params = null;
    }

    /**
     * Parse the hash parameters and update this.params
     */
    updateParams() {
        this.params = null;
        this.params = chisel.validateType(docPageTypes, 'DocPageParams', chisel.decodeParams());
    }

    /**
     * Render the documentation application page
     */
    render() {
        const oldParams = this.params;
        try {
            this.updateParams();
        } catch ({message}) {
            chisel.render(document.body, DocPage.errorPage(message));
            return;
        }

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
     * Helper function to generate the error page's chisel.js element hierarchy model
     *
     * @param {string} [error=null] - The error code. If null, an unexpected error is reported.
     * @return {Object}
     */
    static errorPage(error = null) {
        return chisel.text(error !== null ? `Error: ${error}` : 'An unexpected error occurred.');
    }

    /**
     * Helper function to generate the index page's chisel.js element hierarchy model
     *
     * @param {Object} index - The Chisel documentation index API response
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
     * Helper function to generate the request page's chisel.js element hierarchy model
     *
     * @param {Object} request - The Chisel documentation request API response
     * @returns {Array}
     */
    requestPage(request) {
        const action = 'types' in request && request.types[request.name].action;
        const pathStruct = action && 'path' in action && request.types[action.path].struct;
        const queryStruct = action && 'query' in action && request.types[action.query].struct;
        const inputStruct = action && 'input' in action && request.types[action.input].struct;
        const outputStruct = action && 'output' in action && request.types[action.output].struct;
        const errorsEnum = action && 'errors' in action && request.types[action.errors].enum;
        const typesFilter = [action.name, action.path, action.query, action.input, action.output, action.errors];
        const types = 'types' in request && Object.entries(request.types).filter(
            ([typeName]) => !typesFilter.includes(typeName)
        ).sort().map(([, type]) => type);
        const enums = types && types.filter((type) => 'enum' in type).map((type) => type.enum);
        const structs = types && types.filter((type) => 'struct' in type).map((type) => type.struct);
        const typedefs = types && types.filter((type) => 'typedef' in type).map((type) => type.typedef);

        return [
            // Navigation bar
            chisel.elem('p', null, chisel.elem('a', {'href': chisel.href()}, chisel.text('Back to documentation index'))),

            // Title
            chisel.elem('h1', null, chisel.text(request.name)),
            DocPage.textElem(request.doc),
            !action ? null : DocPage.textElem(action.doc),

            // Request URLs note
            !request.urls.length ? null : chisel.elem('p', {'class': 'chisel-note'}, [
                chisel.elem('b', null, chisel.text('Note: ')),
                chisel.text(`The request is exposed at the following ${request.urls.length > 1 ? 'URLs:' : 'URL:'}`),
                chisel.elem('ul', null, request.urls.map((url) => chisel.elem('li', null, [
                    chisel.elem('a', {'href': url.url}, chisel.text(url.method ? `${url.method} ${url.url}` : url.url))
                ])))
            ]),

            // Action sections
            !pathStruct ? null : this.structElem(pathStruct, 'h2', 'Path Parameters'),
            !queryStruct ? null : this.structElem(queryStruct, 'h2', 'Query Parameters'),
            !inputStruct ? null : this.structElem(inputStruct, 'h2', 'Input Parameters'),
            !outputStruct ? null : this.structElem(outputStruct, 'h2', 'Output Parameters'),
            !errorsEnum ? null : this.enumElem(errorsEnum, 'h2', 'Error Codes'),

            // Typedefs
            !typedefs || !typedefs.length ? null : [
                chisel.elem('h2', null, chisel.text('Typedefs')),
                typedefs.map((typedef) => this.typedefElem(typedef, 'h3', `typedef ${typedef.name}`))
            ],

            // Structs
            !structs || !structs.length ? null : [
                chisel.elem('h2', null, chisel.text('Struct Types')),
                structs.map((struct) => this.structElem(struct, 'h3', `${struct.union ? 'union' : 'struct'} ${struct.name}`))
            ],

            // Enums
            !enums || !enums.length ? null : [
                chisel.elem('h2', null, chisel.text('Enum Types')),
                enums.map((enum_) => this.enumElem(enum_, 'h3', `enum ${enum_.name}`))
            ]
        ];
    }

    /**
     * Helper function to generate a text block's chisel.js element hierarchy model
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
     * Helper method to get a type href (target)
     *
     * @param {Object} type - The Chisel documentation request API type union
     * @return {string}
     */
    typeHref(typeName) {
        const href = chisel.encodeParams({'name': this.params.name});
        return `${href}&type_${typeName}`;
    }

    /**
     * Helper method to generate a member/typedef type's chisel.js element hierarchy model
     *
     * @param {Object} type - The Chisel documentation request API type union
     * @returns {(Object|Array)}
     */
    typeElem(type) {
        if ('array' in type) {
            return [this.typeElem(type.array.type), chisel.text(`${chisel.nbsp}[]`)];
        } else if ('dict' in type) {
            return [
                !('key_type' in type.dict) || 'builtin' in type.dict ? null
                    : [this.typeElem(type.dict.key_type), chisel.text(`${chisel.nbsp}:${chisel.nbsp}`)],
                this.typeElem(type.dict.type),
                chisel.text(`${chisel.nbsp}{}`)
            ];
        } else if ('user' in type) {
            return chisel.elem('a', {'href': `#${this.typeHref(type.user)}`}, chisel.text(type.user));
        }
        return chisel.text(type.builtin);
    }

    /**
     * Helper method to generate a member/typedef's attributes chisel.js element hierarchy model
     *
     * @param {Object} memberOrTypedef - Chisel documentation request API member or typedef
     * @param {Object} memberOrTypedef.type - The Chisel documentation request API type
     * @param {Object} [memberOrTypedef.attr=null] - The Chisel documentation request API attributes
     * @param {boolean} [memberOrTypedef.optional=false] - If true, the member is optional
     * @param {boolean} [memberOrTypedef.nullable=false] - If true, the member is nullable
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
     * Helper method to generate a typedef's chisel.js element hierarchy model
     *
     * @param {Object} typedef - The Chisel documentation request API typedef
     * @param {string} titleTag - The HTML tag for the typedef title element
     * @param {string} title - The typedef section's title string
     * @returns {Array}
     */
    typedefElem(typedef, titleTag, title) {
        const hasAttributes = !!typedef.attr;
        return [
            chisel.elem(
                titleTag,
                {'id': this.typeHref(typedef.name)},
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
     * Helper method to generate a struct's chisel.js element hierarchy model
     *
     * @param {Object} struct - The Chisel documentation request API struct
     * @param {string} titleTag - The HTML tag for the struct title element
     * @param {string} title - The struct section's title string
     * @returns {Array}
     */
    structElem(struct, titleTag, title) {
        const members = 'members' in struct && struct.members;
        const hasAttributes = members && members.reduce(
            (prevValue, curValue) => prevValue || 'optional' in curValue || 'nullable' in curValue || 'attr' in curValue,
            false
        );
        const hasDescription = members && members.reduce(
            (prevValue, curValue) => prevValue || 'doc' in curValue,
            false
        );
        return [
            // Section title
            chisel.elem(
                titleTag,
                {'id': this.typeHref(struct.name)},
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ),
            DocPage.textElem(struct.doc),

            // Struct members
            !members || !members.length ? DocPage.textElem('The struct is empty.') : chisel.elem('table', null, [
                chisel.elem('tr', null, [
                    chisel.elem('th', null, chisel.text('Name')),
                    chisel.elem('th', null, chisel.text('Type')),
                    hasAttributes ? chisel.elem('th', null, chisel.text('Attributes')) : null,
                    hasDescription ? chisel.elem('th', null, chisel.text('Description')) : null
                ]),
                members.map((member) => chisel.elem('tr', null, [
                    chisel.elem('td', null, chisel.text(member.name)),
                    chisel.elem('td', null, this.typeElem(member.type)),
                    hasAttributes ? chisel.elem('td', null, DocPage.attrElem(member)) : null,
                    hasDescription ? chisel.elem('td', null, DocPage.textElem(member.doc)) : null
                ]))
            ])
        ];
    }

    /**
     * Helper method to generate a enum's chisel.js element hierarchy model
     *
     * @param {Object} enum - The Chisel documentation request API enum
     * @param {string} titleTag - The HTML tag for the enum title element
     * @param {string} title - The enum section's title string
     * @returns {Array}
     */
    enumElem(enum_, titleTag, title) {
        const values = 'values' in enum_ && enum_.values;
        const hasDescription = values && values.reduce((prevValue, curValue) => prevValue || 'doc' in curValue, false);
        return [
            // Section title
            chisel.elem(
                titleTag,
                {'id': this.typeHref(enum_.name)},
                chisel.elem('a', {'class': 'linktarget'}, chisel.text(title))
            ),
            DocPage.textElem(enum_.doc),

            // Enum values
            !values || !values.length ? DocPage.textElem('The enum is empty.') : chisel.elem('table', null, [
                chisel.elem('tr', null, [
                    chisel.elem('th', null, chisel.text('Value')),
                    hasDescription ? chisel.elem('th', null, chisel.text('Description')) : null
                ]),
                values.map((value) => chisel.elem('tr', null, [
                    chisel.elem('td', null, chisel.text(value.name)),
                    hasDescription ? chisel.elem('td', null, DocPage.textElem(value.doc)) : null
                ]))
            ])
        ];
    }
}
