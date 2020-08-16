// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import * as chisel from './chisel.js';
import * as markdown from './markdown.js';


/**
 * The Chisel documentation application hash parameters type model specification
 */
const docPageTypes = {
    'DocPageParams': {
        'struct': {
            'name': 'DocPageParams',
            'doc': ['The Chisel documentation application hash parameters struct'],
            'members': [
                {
                    'name': 'name',
                    'doc': ['Request name to render documentation. If not provided, the request index is displayed.'],
                    'type': {'builtin': 'string'},
                    'attr': {'lenGT': 0},
                    'optional': true
                },
                {
                    'name': 'types',
                    'doc': ['JSON user type model resource URL'],
                    'type': {'builtin': 'string'},
                    'attr': {'lenGT': 0},
                    'optional': true
                },
                {
                    'name': 'title',
                    'doc': ['The index page title'],
                    'type': {'builtin': 'string'},
                    'attr': {'lenGT': 0},
                    'optional': true
                }
            ]
        }
    }
};


/**
 * The Chisel documentation application
 *
 * @property {?string} types - The type model object, JSON type model resource URL, or null
 * @property {?string} indexTitle - The index page title or null
 * @property {?Object} params - The parsed and validated hash parameters object
 */
export class DocPage {
    /**
     * Create a documentation application instance
     *
     * @param {?string|Object} [types=null] - Optional type model object or JSON type model resource URL
     * @param {?string} [indexTitle=null] - Optional index page title
     */
    constructor(types = null, indexTitle = null) {
        this.types = types;
        this.indexTitle = indexTitle;
        this.params = null;
    }

    /**
     * Run the application
     *
     * @param {?string|Object} [types=null] - Optional type model object or JSON type model resource URL
     * @param {?string} [indexTitle=null] - Optional index page title
     * @returns {Object} Object meant to be passed to "runCleanup" for application shutdown
     */
    static run(types = null, indexTitle = null) {
        // Create the applicaton object and render
        const docPage = new DocPage(types, indexTitle);
        docPage.render();

        // Add the hash parameters listener
        const addEventListenerArgs = ['hashchange', () => docPage.render(), false];
        window.addEventListener(...addEventListenerArgs);

        // Return the cleanup object
        return {
            'windowRemoveEventListener': addEventListenerArgs
        };
    }

    /*
     * Cleanup global state created by "run"
     *
     * @param {Object} runResult - The return value of "run"
     */
    static runCleanup(runResult) {
        window.removeEventListener(...runResult.windowRemoveEventListener);
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
        // Decode and validate hash parameters
        try {
            const oldParams = this.params;
            this.updateParams();

            // Skip the render if the page params haven't changed
            if (oldParams !== null && JSON.stringify(oldParams) === JSON.stringify(this.params)) {
                return;
            }
        } catch ({message}) {
            chisel.render(document.body, DocPage.errorPage(message));
            return;
        }

        // Clear the page
        chisel.render(document.body);

        // Compute the document title
        let title;
        if ('name' in this.params) {
            title = this.params.name;
        } else if ('types' in this.params) {
            title = 'title' in this.params ? this.params.title : 'Index';
        } else {
            title = this.indexTitle !== null ? this.indexTitle : 'Index';
        }

        // Types resource URL?
        const types = 'types' in this.params ? this.params.types : (this.types !== null ? this.types : null);
        if (types !== null) {
            // Types object?
            if (typeof types === 'string') {
                // Fetch the JSON type model
                window.fetch(types).
                    then((response) => response.json()).
                    then((response) => {
                        chisel.render(document.body, this.typesPage(response, title, this.params.name));
                    }).catch(() => {
                        chisel.render(document.body, DocPage.errorPage());
                    });
            } else {
                chisel.render(document.body, this.typesPage(types, title, this.params.name));
            }
        } else if ('name' in this.params) {
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
                    if ('title' in response) {
                        ({title} = response);
                    }
                    chisel.render(document.body, this.indexPage(response));
                }).catch(() => {
                    chisel.render(document.body, DocPage.errorPage());
                });
        }

        // Set the document title
        document.title = title;
    }

    /**
     * Helper function to generate the error page's element hierarchy model
     *
     * @param {string} [error=null] - The error code. If null, an unexpected error is reported.
     * @return {Object}
     */
    static errorPage(error = null) {
        return {
            'html': 'p',
            'elem': {'text': error !== null ? `Error: ${error}` : 'An unexpected error occurred.'}
        };
    }

    /**
     * Helper function to generate the user type's element hierarchy model
     *
     * @param {Object} types - The type model
     * @param {string} title - The types page title
     * @param {?string} [typeName=null] - The type name
     * @returns {Array}
     */
    typesPage(types, title, typeName = null) {
        // Validate the type model
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
            'title': title,
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

        return this.indexPage(index);
    }

    /**
     * Helper function to generate the index page's element hierarchy model
     *
     * @param {Object} index - The Chisel documentation index API response
     * @returns {Array}
     */
    indexPage(index) {
        // Error?
        if ('error' in index) {
            return DocPage.errorPage(index.error);
        }

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
                            'elem': {'html': 'a', 'attr': {'href': chisel.href({...this.params, 'name': name})}, 'elem': {'text': name}}
                        })
                    )}}
                }
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
        const filteredTypes =
              Object.entries(referencedTypes).sort().filter(([name]) => !typesFilter.includes(name)).map(([, type]) => type);

        return [
            // Navigation bar
            {
                'html': 'p',
                'elem': {
                    'html': 'a',
                    'attr': {'href': chisel.href({...this.params, 'name': null})},
                    'elem': {'text': 'Back to documentation index'}
                }
            },

            // The user type
            userType !== null
                ? this.userTypeElem(request.types, request.name, request.urls, 'h1', request.name)
                : DocPage.requestElem(request),

            // Referenced types
            !filteredTypes.length ? null : [
                {'html': 'hr'},
                {'html': 'h2', 'elem': {'text': 'Referenced Types'}},
                filteredTypes.map((refType) => this.userTypeElem(request.types, Object.values(refType)[0].name, null, 'h3'))
            ]
        ];
    }

    /**
     * Helper function to generate a text block's element hierarchy model
     *
     * @param {string} [text=null] - Markdown text
     * @returns {?Array}
     */
    static markdownElem(text = null) {
        if (text === null) {
            return null;
        }
        return markdown.markdownElements(markdown.parseMarkdown(text));
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
            return [this.typeElem(type.array.type), {'text': `${chisel.nbsp}[]`}];
        } else if ('dict' in type) {
            return [
                !('keyType' in type.dict) || 'builtin' in type.dict ? null
                    : [this.typeElem(type.dict.keyType), {'text': `${chisel.nbsp}:${chisel.nbsp}`}],
                this.typeElem(type.dict.type),
                {'text': `${chisel.nbsp}{}`}
            ];
        } else if ('user' in type) {
            return {'html': 'a', 'attr': {'href': `#${this.typeHref(type.user)}`}, 'elem': {'text': type.user}};
        }
        return {'text': type.builtin};
    }

    /**
     * Helper method to generate a member/typedef's attributes element hierarchy model
     *
     * @param {Object} type - The type model
     * @param {Object} attr - The attribute model
     * @param {boolean} optional - If true, the type has the optional attribute
     * @returns {(null|Array)}
     */
    static attrElem({type, attr = null, optional = false}) {
        // Create the array of attribute "parts" (lhs, op, rhs)
        const parts = [];
        const typeName = type.array ? 'array' : (type.dict ? 'dict' : 'value');
        if (optional) {
            parts.push({'lhs': 'optional'});
        }
        if (attr !== null && 'nullable' in attr) {
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
        if (attr !== null && 'lenGT' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '>', 'rhs': attr.lenGT});
        }
        if (attr !== null && 'lenGTE' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '>=', 'rhs': attr.lenGTE});
        }
        if (attr !== null && 'lenLT' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '<', 'rhs': attr.lenLT});
        }
        if (attr !== null && 'lenLTE' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '<=', 'rhs': attr.lenLTE});
        }
        if (attr !== null && 'lenEq' in attr) {
            parts.push({'lhs': `len(${typeName})`, 'op': '==', 'rhs': attr.lenEq});
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
     * Helper method to generate a non-action request's element model
     *
     * @param {Object} request - The Chisel documentation request API response
     * @returns {Array}
     */
    static requestElem(request) {
        return [
            {'html': 'h1', 'elem': {'text': request.name}},
            DocPage.markdownElem(request.doc),
            DocPage.urlsNoteElem(request.urls)
        ];
    }

    /**
     * Helper method to generate a request's URL note element model
     *
     * @param {?Object[]} [urls=null] - The array of request URL models or null
     * @returns {Object}
     */
    static urlsNoteElem(urls = null) {
        return urls === null || !urls.length ? null : {'html': 'p', 'attr': {'class': 'chisel-note'}, 'elem': [
            {'html': 'b', 'elem': {'text': 'Note: '}},
            {'text': `The request is exposed at the following ${urls.length > 1 ? 'URLs:' : 'URL:'}`},
            {'html': 'ul', 'elem': urls.map((url) => ({'html': 'li', 'elem': [
                {'html': 'a', 'attr': {'href': url.url}, 'elem': {'text': url.method ? `${url.method} ${url.url}` : url.url}}
            ]}))}
        ]};
    }

    /**
     * Helper method to generate a user type's element hierarchy model
     *
     * @param {Object} types - The type model
     * @param {string} typeName - The type name
     * @param {?Object[]} [urls=null] - The array of request URL models or null
     * @param {string} [titleTag='h1'] - The HTML tag for the title element
     * @param {?string} [title=null] - The section's title string
     * @returns {Array}
     */
    userTypeElem(types, typeName, urls, titleTag, title = null, introMarkdown = null) {
        const userType = types[typeName];

        // Generate the header element models
        const titleElem = (titleDefault) => ({
            'html': titleTag,
            'attr': {'id': this.typeHref(typeName)},
            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': title !== null ? title : titleDefault}}
        });

        // Action?
        if ('action' in userType) {
            const {action} = userType;

            // Add "UnexpectedError" to the action's errors
            const actionErrorTypeName = `${action.name}_errors`;
            const actionErrorValues = 'errors' in action && 'enum' in types[action.errors] ? types[action.errors].enum.values : [];
            const actionErrorTypes = {};
            actionErrorTypes[actionErrorTypeName] = {
                'enum': {
                    'name': actionErrorTypeName,
                    'values': [
                        {
                            'name': 'UnexpectedError',
                            'doc': ['An unexpected error occurred while processing the request']
                        },
                        ...actionErrorValues
                    ]
                }
            };

            // If no URLs passed use the action's URLs
            let actionUrls = urls;
            if (urls === null && 'urls' in action) {
                actionUrls = action.urls.map(({method = null, path = null}) => {
                    const url = {
                        'url': path !== null ? path : `/${typeName}`
                    };
                    if (method !== null) {
                        url.method = method;
                    }
                    return url;
                });
            }

            return [
                titleElem(`action ${typeName}`),
                DocPage.markdownElem(action.doc),
                DocPage.urlsNoteElem(actionUrls),

                // Action types
                'path' in action ? this.userTypeElem(types, action.path, null, 'h2', 'Path Parameters') : null,
                'query' in action ? this.userTypeElem(types, action.query, null, 'h2', 'Query Parameters') : null,
                'input' in action ? this.userTypeElem(types, action.input, null, 'h2', 'Input Parameters') : null,
                'output' in action ? this.userTypeElem(types, action.output, null, 'h2', 'Output Parameters') : null,
                this.userTypeElem(
                    actionErrorTypes,
                    actionErrorTypeName,
                    null,
                    'h2',
                    'Error Codes',
                    `\
If an application error occurs, the response is of the form:

    {
        "error": "<code>",
        "message": "<message>"
    }

"message" is optional. "<code>" is one of the following values:`
                )
            ];

        // Struct?
        } else if ('struct' in userType) {
            const {struct} = userType;
            const members = 'members' in struct ? struct.members : null;
            const memberAttrElem = members !== null
                ? Object.fromEntries(members.map((member) => [member.name, DocPage.attrElem(member)])) : null;
            const hasAttr = members !== null && Object.values(memberAttrElem).some((attrElem) => attrElem !== null);
            const memberDocElem = members !== null
                ? Object.fromEntries(members.map(({name, doc}) => [name, DocPage.markdownElem(doc)])) : null;
            const hasDoc = members !== null && Object.values(memberDocElem).some((docElem) => docElem !== null);
            return [
                titleElem('union' in struct && struct.union ? `union ${typeName}` : `struct ${typeName}`),
                DocPage.markdownElem(struct.doc),

                // Struct members
                !members || !members.length ? DocPage.markdownElem('The struct is empty.') : {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Name'}},
                        {'html': 'th', 'elem': {'text': 'Type'}},
                        hasAttr ? {'html': 'th', 'elem': {'text': 'Attributes'}} : null,
                        hasDoc ? {'html': 'th', 'elem': {'text': 'Description'}} : null
                    ]},
                    members.map((member) => ({'html': 'tr', 'elem': [
                        {'html': 'td', 'elem': {'text': member.name}},
                        {'html': 'td', 'elem': this.typeElem(member.type)},
                        hasAttr ? {'html': 'td', 'elem': memberAttrElem[member.name]} : null,
                        hasDoc ? {'html': 'td', 'elem': memberDocElem[member.name]} : null
                    ]}))
                ]}
            ];

        // Enumeration?
        } else if ('enum' in userType) {
            const enum_ = userType.enum;
            const values = 'values' in enum_ ? enum_.values : null;
            const valueDocElem = values !== null
                ? Object.fromEntries(values.map(({name, doc}) => [name, DocPage.markdownElem(doc)])) : null;
            const hasDoc = values !== null && Object.values(valueDocElem).some((docElem) => docElem !== null);
            return [
                titleElem(`enum ${typeName}`),
                DocPage.markdownElem(enum_.doc),
                introMarkdown !== null ? DocPage.markdownElem(introMarkdown) : null,

                // Enumeration values
                !values || !values.length ? DocPage.markdownElem('The enum is empty.') : {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Value'}},
                        hasDoc ? {'html': 'th', 'elem': {'text': 'Description'}} : null
                    ]},
                    values.map((value) => ({'html': 'tr', 'elem': [
                        {'html': 'td', 'elem': {'text': value.name}},
                        hasDoc ? {'html': 'td', 'elem': valueDocElem[value.name]} : null
                    ]}))
                ]}
            ];

        // Typedef?
        } else if ('typedef' in userType) {
            const {typedef} = userType;
            const attrElem = 'attr' in typedef ? DocPage.attrElem(typedef) : null;
            return [
                titleElem(`typedef ${typeName}`),
                DocPage.markdownElem(typedef.doc),

                // Typedef type description
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

        return null;
    }
}
