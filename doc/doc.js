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
                    'name': 'types',
                    'doc': 'JSON user type model resource URL',
                    'type': {'builtin': 'string'},
                    'attr': {'len_gt': 0},
                    'optional': true
                },
                {
                    'name': 'title',
                    'doc': 'The index page title',
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
 * @property {string} typesUrl - The JSON type model resource URL or null
 * @property {string} indexTitle - The index page title or null
 * @property {Object} params - The parsed and validated hash parameters object
 */
export class DocPage {
    /**
     * Create a documentation application instance
     *
     * @param {string} [typesUrl=null] - Optional JSON type model resource URL
     * @param {string} [indexTitle=null] - Optional index page title
     */
    constructor(typesUrl = null, indexTitle = null) {
        this.typesUrl = typesUrl;
        this.indexTitle = indexTitle;
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
        if (oldParams !== null && oldParams.name === this.params.name && oldParams.types === this.params.types) {
            return;
        }

        // Clear the page
        chisel.render(document.body);

        // Types resource URL?
        const typesUrl = 'types' in this.params ? this.params.types : (this.typesUrl !== null ? this.typesUrl : null);
        if (typesUrl !== null) {
            document.title = 'name' in this.params ? this.params.name : this.getIndexPageTitle();

            // Fetch the JSON type model
            window.fetch(typesUrl).
                then((response) => response.json()).
                then((response) => {
                    chisel.render(document.body, this.typesPage(response, this.params.name));
                }).catch(() => {
                    chisel.render(document.body, DocPage.errorPage());
                });
        } else if ('name' in this.params) {
            document.title = this.params.name;

            // Call the request API
            window.fetch(`doc_request?name=${this.params.name}`).
                then((response) => response.json()).
                then((response) => {
                    chisel.render(document.body, this.requestPage(response));
                }).catch(() => {
                    chisel.render(document.body, DocPage.errorPage());
                });
        } else {
            // Call the index API
            window.fetch('doc_index').
                then((response) => response.json()).
                then((response) => {
                    document.title = this.getIndexPageTitle(response.title);
                    chisel.render(document.body, DocPage.indexPage(response));
                }).catch(() => {
                    document.title = this.getIndexPageTitle();
                    chisel.render(document.body, DocPage.errorPage());
                });
        }
    }

    /**
     * Helper function to generate the error page's element hierarchy model
     *
     * @param {string} [error=null] - The error code. If null, an unexpected error is reported.
     * @return {Object}
     */
    static errorPage(error = null) {
        return {
            'tag': 'p',
            'elems': chisel.text(error !== null ? `Error: ${error}` : 'An unexpected error occurred.')
        };
    }

    /**
     * Helper function to generate the user type's element hierarchy model
     *
     * @param {Object} types - The type model
     * @param {?string} [typeName=null] - The type name
     * @returns {Array}
     */
    typesPage(types, typeName = null) {
        // Invalid type model?
        try {
            chisel.validateTypes(types);
        } catch (error) {
            return DocPage.errorPage(error.message);
        }

        // Type page?
        if (typeName !== null) {
            // Unknown type?
            if (!(typeName in types)) {
                return DocPage.errorPage(`Unknown type name '${typeName}'`);
            }

            return this.requestPage({'name': typeName, 'types': types});
        }

        // Create the index response
        const index = {
            'title': this.getIndexPageTitle(),
            'groups': {}
        };

        // Group by user type
        const typesSorted = Object.entries(types).sort().map(([, userType]) => userType);
        [['action', 'Actions'], ['enum', 'Enumerations'], ['struct', 'Structs'], ['typedef', 'Typedefs']].forEach(([key, groupName]) => {
            const objects = typesSorted.filter((userType) => key in userType).map((userType) => userType[key].name);
            if (objects.length) {
                index.groups[groupName] = objects;
            }
        });

        return DocPage.indexPage(index);
    }

    /**
     * The index page title
     */
    getIndexPageTitle(title = null) {
        if (title !== null) {
            return title;
        } else if ('title' in this.params) {
            return this.params.title;
        } else if (this.indexTitle !== null) {
            return this.indexTitle;
        }
        return 'Index';
    }

    /**
     * Helper function to generate the index page's element hierarchy model
     *
     * @param {Object} index - The Chisel documentation index API response
     * @returns {Array}
     */
    static indexPage(index) {
        // Error?
        if ('error' in index) {
            return DocPage.errorPage(index.error);
        }

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
     * Helper function to generate the request page's element hierarchy model
     *
     * @param {Object} request - The Chisel documentation request API response
     * @returns {Array}
     */
    requestPage(request) {
        // Error?
        if ('error' in request) {
            return DocPage.errorPage(request.error);
        }

        // Compute the referenced types
        const userType = 'types' in request ? request.types[request.name] : null;
        const action = userType !== null && 'action' in userType ? userType.action : null;
        const referencedTypes = userType !== null ? chisel.getReferencedTypes(request.types, request.name) : [];
        let typesFilter;
        if (action !== null) {
            typesFilter = [request.name, action.path, action.query, action.input, action.output, action.errors];
        } else {
            typesFilter = [request.name];
        }
        const typesSorted =
              Object.entries(referencedTypes).sort().filter(([name]) => !typesFilter.includes(name)).map(([, type]) => type);
        const enums = typesSorted.filter((type) => 'enum' in type).map((type) => type.enum);
        const structs = typesSorted.filter((type) => 'struct' in type).map((type) => type.struct);
        const typedefs = typesSorted.filter((type) => 'typedef' in type).map((type) => type.typedef);

        return [
            // Navigation bar
            chisel.elem('p', null, chisel.elem('a', {'href': chisel.href()}, chisel.text('Back to documentation index'))),

            // Title
            chisel.elem('h1', null, chisel.text(request.name)),
            DocPage.textElem(request.doc),
            action !== null ? DocPage.textElem(action.doc) : null,

            // Request URLs note
            !('urls' in request) || !request.urls.length ? null : chisel.elem('p', {'class': 'chisel-note'}, [
                chisel.elem('b', null, chisel.text('Note: ')),
                chisel.text(`The request is exposed at the following ${request.urls.length > 1 ? 'URLs:' : 'URL:'}`),
                chisel.elem('ul', null, request.urls.map((url) => chisel.elem('li', null, [
                    chisel.elem('a', {'href': url.url}, chisel.text(url.method ? `${url.method} ${url.url}` : url.url))
                ])))
            ]),

            // The user type
            userType !== null ? this.userTypeElem(request.types, request.name) : null,

            // Referenced typedefs
            !typedefs.length ? null : [
                chisel.elem('h2', null, chisel.text('Typedefs')),
                typedefs.map((typedef) => this.userTypeElem(request.types, typedef.name, 'h3', `typedef ${typedef.name}`))
            ],

            // Referenced structs
            !structs.length ? null : [
                chisel.elem('h2', null, chisel.text('Struct Types')),
                structs.map(
                    (struct) => this.userTypeElem(request.types, struct.name, 'h3', `${struct.union ? 'union' : 'struct'} ${struct.name}`)
                )
            ],

            // Referenced enums
            !enums.length ? null : [
                chisel.elem('h2', null, chisel.text('Enum Types')),
                enums.map((enum_) => this.userTypeElem(request.types, enum_.name, 'h3', `enum ${enum_.name}`))
            ]
        ];
    }

    /**
     * Helper function to generate a text block's element hierarchy model
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
     * @param {Object} typeName - The type name
     * @return {string}
     */
    typeHref(typeName) {
        return `${chisel.encodeParams(this.params)}&type_${typeName}`;
    }

    /**
     * Helper method to generate a member/typedef type's element hierarchy model
     *
     * @param {Object} type - The type model
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
     * Helper method to generate a member/typedef's attributes element hierarchy model
     *
     * @param {Object} type - The type model
     * @param {Object} attr - The attribute model
     * @param {boolean} optional - If true, the type has the optional attribute
     * @param {boolean} nullable - If true, the type has the nullable attribute
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
     * Helper method to generate a user type's element hierarchy model
     *
     * @param {Object} types - The type model
     * @param {string} typeName - The type name
     * @param {string} [titleTag='h1'] - The HTML tag for the title element
     * @param {string} [title=null] - The section's title string
     * @returns {Array}
     */
    userTypeElem(types, typeName, titleTag = 'h1', title = null) {
        const userType = types[typeName];
        if ('action' in userType) {
            const {action} = userType;
            return [
                'path' in action ? this.userTypeElem(types, action.path, 'h2', 'Path Parameters') : null,
                'query' in action ? this.userTypeElem(types, action.query, 'h2', 'Query Parameters') : null,
                'input' in action ? this.userTypeElem(types, action.input, 'h2', 'Input Parameters') : null,
                'output' in action ? this.userTypeElem(types, action.output, 'h2', 'Output Parameters') : null,
                'errors' in action ? this.userTypeElem(types, action.errors, 'h2', 'Error Codes') : null
            ];
        } else if ('struct' in userType) {
            return this.structElem(userType.struct, titleTag, title !== null ? title : typeName);
        } else if ('enum' in userType) {
            return this.enumElem(userType.enum, titleTag, title !== null ? title : typeName);
        } else if ('typedef' in userType) {
            return this.typedefElem(userType.typedef, titleTag, title !== null ? title : typeName);
        }
        return null;
    }

    /**
     * Helper method to generate a typedef's element hierarchy model
     *
     * @param {Object} typedef - The typedef model
     * @param {string} titleTag - The HTML tag for the title element
     * @param {string} title - The section's title string
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
     * Helper method to generate a struct's element hierarchy model
     *
     * @param {Object} struct - The struct model
     * @param {string} titleTag - The HTML tag for the title element
     * @param {string} title - The section's title string
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
     * Helper method to generate a enum's element hierarchy model
     *
     * @param {Object} enum - The enum model
     * @param {string} titleTag - The HTML tag for the title element
     * @param {string} title - The section's title string
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
