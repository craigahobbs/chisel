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
                    'name': 'url',
                    'doc': ['The JSON type model with title resource URL'],
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
 * @property {?string} defaultTypeModel - The default type model object
 * @property {?string} defaultTypeModelURL - The default JSON type model with title resource URL
 * @property {Array} windowHashChangeArgs - The arguments for the window.addEventListener for "hashchange"
 * @property {Object} params - The validated hash parameters object
 * @property {Object} config - The validated hash parameters with defaults
 */
export class DocPage {
    /**
     * Create a documentation application instance
     *
     * @param {?string|Object} [typeModel=null] - Optional type model with title (object or resource URL)
     */
    constructor(typeModel = null) {
        this.defaultTypeModel = typeof typeModel !== 'string' ? typeModel : null;
        this.defaultTypeModelURL = typeof typeModel === 'string' ? typeModel : null;
        this.windowHashChangeArgs = null;
        this.params = null;
        this.config = null;
    }


    /**
     * Run the application
     *
     * @param {?string|Object} [typeModel=null] - Optional type model object or JSON type model resource URL
     * @returns {DocPage}
     */
    static run(typeModel = null) {
        const docPage = new DocPage(typeModel);
        docPage.init();
        docPage.render();
        return docPage;
    }


    /**
     * Initialize the global application state
     */
    init() {
        this.windowHashChangeArgs = ['hashchange', () => this.render(), false];
        window.addEventListener(...this.windowHashChangeArgs);
    }


    /**
     * Uninitialize the global application state
     */
    uninit() {
        if (this.windowHashChangeArgs !== null) {
            window.removeEventListener(...this.windowHashChangeArgs);
            this.windowHashChangeArgs = null;
        }
    }


    /**
     * Helper function to parse and validate the hash parameters
     *
     *
     * @param {?string} params - The (hash) params string
     */
    updateParams(params = null) {
        // Clear params and config
        this.params = null;
        this.config = null;

        // Validate the hash parameters (may throw)
        this.params = chisel.validateType(docPageTypes, 'DocPageParams', chisel.decodeParams(params));

        // Set the default hash parameters
        this.config = {
            'name': null,
            'url': null,
            ...this.params
        };
    }


    /**
     * Render the documentation application page
     */
    render() {
        // Validate hash parameters
        try {
            const oldParams = this.params;
            this.updateParams();

            // Skip the render if the page params haven't changed
            if (oldParams !== null && JSON.stringify(oldParams) === JSON.stringify(this.params)) {
                return;
            }
        } catch ({message}) {
            DocPage.renderErrorPage(message);
            return;
        }

        // Clear the page
        chisel.render(document.body);

        // Type model URL provided?
        const typeModelURL = this.config.url !== null ? this.config.url : this.defaultTypeModelURL;
        if (typeModelURL !== null) {
            // Load the type model URL
            window.fetch(typeModelURL).
                then((response) => {
                    if (!response.ok) {
                        throw new Error(`Could not fetch type mode '${typeModelURL}': ${response.statusText}`);
                    }
                    return response.json();
                }).
                then((typeModel) => {
                    this.renderTypeModelPage(chisel.validateTypeModel(typeModel));
                }).catch(({message}) => {
                    DocPage.renderErrorPage(message);
                });
        } else if (this.defaultTypeModel !== null) {
            this.renderTypeModelPage(this.defaultTypeModel);
        } else if (this.config.name !== null) {
            // Call the request API
            window.fetch(`doc_request?name=${this.config.name}`).
                then((response) => {
                    if (!response.ok) {
                        throw new Error(`Could not fetch request '${this.config.name}': ${response.statusText}`);
                    }
                    return response.json();
                }).
                then((request) => {
                    this.renderRequestPage(request);
                }).catch(({message}) => {
                    DocPage.renderErrorPage(message);
                });
        } else {
            // Call the index API
            window.fetch('doc_index').
                then((response) => {
                    if (!response.ok) {
                        throw new Error(`Could not fetch index: ${response.statusText}`);
                    }
                    return response.json();
                }).
                then((index) => {
                    this.renderIndexPage(index);
                }).catch(({message}) => {
                    DocPage.renderErrorPage(message);
                });
        }
    }


    /**
     * Helper function to render a type model experience
     */
    renderTypeModelPage(typeModel) {
        // Type page?
        if (this.config.name !== null) {
            // Unknown type?
            if (!(this.config.name in typeModel.types)) {
                DocPage.renderErrorPage(`Unknown type name '${this.config.name}'`);
            } else {
                this.renderRequestPage({'name': this.config.name, 'types': typeModel.types});
            }
            return;
        }

        // Render the index page
        const index = {
            'title': typeModel.title,
            'groups': {}
        };
        const userTypesSorted = Object.entries(typeModel.types).sort();
        for (const [userTypeName, userType] of userTypesSorted) {
            let docGroup;
            if ('enum' in userType) {
                docGroup = 'docGroup' in userType.enum ? userType.enum.docGroup : 'Enumerations';
            } else if ('struct' in userType) {
                docGroup = 'docGroup' in userType.struct ? userType.struct.docGroup : 'Structs';
            } else if ('typedef' in userType) {
                docGroup = 'docGroup' in userType.typedef ? userType.typedef.docGroup : 'Typedefs';
            } else {
                docGroup = 'docGroup' in userType.action ? userType.action.docGroup : 'Uncategorized';
            }
            if (!(docGroup in index.groups)) {
                index.groups[docGroup] = [];
            }
            index.groups[docGroup].push(userTypeName);
        }
        this.renderIndexPage(index);
    }


    /**
     * Helper function to render an index page
     *
     * @param {Object} index - The index API response
    */
    renderIndexPage(index) {
        document.title = index.title;
        chisel.render(document.body, this.indexPage(index));
    }


    /**
     * Helper function to render a request page
     *
     * @param {Object} request - The request API response
     */
    renderRequestPage(request) {
        document.title = request.name;
        chisel.render(document.body, this.requestPage(request));
    }


    /**
     * Helper function to render an error page
     */
    static renderErrorPage(message) {
        document.title = 'Error';
        chisel.render(document.body, DocPage.errorPage(message));
    }


    /**
     * Helper function to generate the error page's element hierarchy model
     *
     * @param {string} message - The error message
     * @return {Object}
     */
    static errorPage(message) {
        return {
            'html': 'p',
            'elem': {'text': `Error: ${message}`}
        };
    }


    /**
     * Helper function to generate the index page's element hierarchy model
     *
     * @param {Object} index - The Chisel documentation index API response
     * @returns {Array}
     */
    indexPage(index) {
        return [
            // Title
            {'html': 'h1', 'elem': {'text': index.title}},

            // Groups
            Object.keys(index.groups).sort().map((group) => [
                {'html': 'h2', 'elem': {'text': group}},
                {
                    'html': 'ul',
                    'attr': {'class': 'chisel-index-list'},
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
        const indexParams = {...this.params};
        delete indexParams.name;

        return [
            // Navigation bar
            {
                'html': 'p',
                'elem': {
                    'html': 'a',
                    'attr': {'href': chisel.href(indexParams)},
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
