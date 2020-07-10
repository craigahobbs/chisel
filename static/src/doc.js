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
                },
                {
                    'name': 'url',
                    'doc': 'Request API JSON resource URL',
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
        if (oldParams !== null && oldParams.name === this.params.name && oldParams.url === this.params.url) {
            return;
        }

        // Clear the page
        chisel.render(document.body);

        // Render the page
        if ('name' in this.params || 'url' in this.params) {
            // Call the request API
            window.fetch('url' in this.params ? this.params.url : `doc_request/${this.params.name}`).then(
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
        return {'text': error !== null ? `Error: ${error}` : 'An unexpected error occurred.'};
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
            {'html': 'h1', 'elem': {'text': index.title}},

            // Groups
            Object.keys(index.groups).sort().map((group) => [
                {'html': 'h2', 'elem': {'text': group}},
                {
                    'html': 'ul',
                    'attr': {'class': 'chisel-request-list'},
                    'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': index.groups[group].sort().map(
                        (name) => ({
                            'html': 'li',
                            'elem': {'html': 'a', 'attr': {'href': chisel.href({'name': name})}, 'elem': {'text': name}}
                        })
                    )}}
                }
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
            {'html': 'p', 'elem': {'html': 'a', 'attr': {'href': chisel.href()}, 'elem': {'text': 'Back to documentation index'}}},

            // Title
            {'html': 'h1', 'elem': {'text': request.name}},
            DocPage.textElem(request.doc),
            !action ? null : DocPage.textElem(action.doc),

            // Request URLs note
            !request.urls.length ? null : {'html': 'p', 'attr': {'class': 'chisel-note'}, 'elem': [
                {'html': 'b', 'elem': {'text': 'Note: '}},
                {'text': `The request is exposed at the following ${request.urls.length > 1 ? 'URLs:' : 'URL:'}`},
                {'html': 'ul', 'elem': request.urls.map((url) => ({'html': 'li', 'elem': [
                    {'html': 'a', 'attr': {'href': url.url}, 'elem': {'text': url.method ? `${url.method} ${url.url}` : url.url}}
                ]}))}
            ]},

            // Action sections
            !pathStruct ? null : this.structElem(pathStruct, 'h2', 'Path Parameters'),
            !queryStruct ? null : this.structElem(queryStruct, 'h2', 'Query Parameters'),
            !inputStruct ? null : this.structElem(inputStruct, 'h2', 'Input Parameters'),
            !outputStruct ? null : this.structElem(outputStruct, 'h2', 'Output Parameters'),
            !errorsEnum ? null : this.enumElem(errorsEnum, 'h2', 'Error Codes'),

            // Typedefs
            !typedefs || !typedefs.length ? null : [
                {'html': 'h2', 'elem': {'text': 'Typedefs'}},
                typedefs.map((typedef) => this.typedefElem(typedef, 'h3', `typedef ${typedef.name}`))
            ],

            // Structs
            !structs || !structs.length ? null : [
                {'html': 'h2', 'elem': {'text': 'Struct Types'}},
                structs.map((struct) => this.structElem(struct, 'h3', `${struct.union ? 'union' : 'struct'} ${struct.name}`))
            ],

            // Enums
            !enums || !enums.length ? null : [
                {'html': 'h2', 'elem': {'text': 'Enum Types'}},
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
                    elems.push({'html': 'p', 'elem': {'text': paragraph.join('\n')}});
                    paragraph = [];
                }
            }
            if (paragraph.length) {
                elems.push({'html': 'p', 'elem': {'text': paragraph.join('\n')}});
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
        return `${chisel.encodeParams(this.params)}&type_${typeName}`;
    }

    /**
     * Helper method to generate a member/typedef type's chisel.js element hierarchy model
     *
     * @param {Object} type - The Chisel documentation request API type union
     * @returns {(Object|Array)}
     */
    typeElem(type) {
        if ('array' in type) {
            return [this.typeElem(type.array.type), {'text': `${chisel.nbsp}[]`}];
        } else if ('dict' in type) {
            return [
                !('key_type' in type.dict) || 'builtin' in type.dict ? null
                    : [this.typeElem(type.dict.key_type), {'text': `${chisel.nbsp}:${chisel.nbsp}`}],
                this.typeElem(type.dict.type),
                {'text': `${chisel.nbsp}{}`}
            ];
        } else if ('user' in type) {
            return {'html': 'a', 'attr': {'href': `#${this.typeHref(type.user)}`}, 'elem': {'text': type.user}};
        }
        return {'text': type.builtin};
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
        return !parts.length ? null : {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': parts.map(
            (part) => ({
                'html': 'li',
                'elem': {'text': part.op ? `${part.lhs}${chisel.nbsp}${part.op}${chisel.nbsp}${part.rhs}` : part.lhs}
            })
        )};
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
        const attrElem = 'attr' in typedef ? DocPage.attrElem(typedef) : null;
        return [
            {
                'html': titleTag,
                'attr': {'id': this.typeHref(typedef.name)},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': title}}
            },
            DocPage.textElem(typedef.doc),
            {'html': 'table', 'elem': [
                {'html': 'tr', 'elem': [
                    {'html': 'th', 'elem': {'text': 'Type'}},
                    attrElem !== null ? {'html': 'th', 'elem': {'text': 'Attributes'}} : null
                ]},
                {'html': 'tr', 'elem': [
                    {'html': 'td', 'elem': this.typeElem(typedef.type)},
                    attrElem !== null ? {'html': 'td', 'elem': attrElem} : null
                ]}
            ]}
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
        const members = 'members' in struct ? struct.members : null;
        const memberAttr = members !== null ? Object.fromEntries(members.map((member) => [member.name, DocPage.attrElem(member)])) : null;
        const hasAttr = members !== null && Object.values(memberAttr).some((attrElem) => attrElem !== null);
        const memberDoc = members !== null ? Object.fromEntries(members.map(({name, doc}) => [name, DocPage.textElem(doc)])) : null;
        const hasDoc = members !== null && Object.values(memberDoc).some((docElem) => docElem !== null);
        return [
            // Section title
            {
                'html': titleTag,
                'attr': {'id': this.typeHref(struct.name)},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': title}}
            },
            DocPage.textElem(struct.doc),

            // Struct members
            !members || !members.length ? DocPage.textElem('The struct is empty.') : {'html': 'table', 'elem': [
                {'html': 'tr', 'elem': [
                    {'html': 'th', 'elem': {'text': 'Name'}},
                    {'html': 'th', 'elem': {'text': 'Type'}},
                    hasAttr ? {'html': 'th', 'elem': {'text': 'Attributes'}} : null,
                    hasDoc ? {'html': 'th', 'elem': {'text': 'Description'}} : null
                ]},
                members.map((member) => ({'html': 'tr', 'elem': [
                    {'html': 'td', 'elem': {'text': member.name}},
                    {'html': 'td', 'elem': this.typeElem(member.type)},
                    hasAttr ? {'html': 'td', 'elem': memberAttr[member.name]} : null,
                    hasDoc ? {'html': 'td', 'elem': memberDoc[member.name]} : null
                ]}))
            ]}
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
        const hasDoc = values && values.reduce((prevValue, curValue) => prevValue || 'doc' in curValue, false);
        return [
            // Section title
            {
                'html': titleTag,
                'attr': {'id': this.typeHref(enum_.name)},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': title}}
            },
            DocPage.textElem(enum_.doc),

            // Enum values
            !values || !values.length ? DocPage.textElem('The enum is empty.') : {'html': 'table', 'elem': [
                {'html': 'tr', 'elem': [
                    {'html': 'th', 'elem': {'text': 'Value'}},
                    hasDoc ? {'html': 'th', 'elem': {'text': 'Description'}} : null
                ]},
                values.map((value) => ({'html': 'tr', 'elem': [
                    {'html': 'td', 'elem': {'text': value.name}},
                    hasDoc ? {'html': 'td', 'elem': DocPage.textElem(value.doc)} : null
                ]}))
            ]}
        ];
    }
}
