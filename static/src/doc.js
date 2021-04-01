// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {decodeParams, href} from './schema-markdown/util.js';
import {SchemaMarkdownParser} from './schema-markdown/parser.js';
import {UserTypeElements} from './schema-markdown/doc.js';
import {renderElements} from './schema-markdown/elements.js';
import {validateType} from './schema-markdown/schema.js';


const docPageTypes = (new SchemaMarkdownParser(`\
# The Chisel documentation application hash parameters type model
struct DocPageParams

    # The Chisel documentation application hash parameters struct
    optional string(len > 0) name
`)).types;


/**
 * The Chisel documentation application
 *
 * @property {Array} windowHashChangeArgs - The arguments for the window.addEventListener for "hashchange"
 * @property {Object} params - The validated hash parameters object
 */
export class DocPage {
    /**
     * Create a documentation application instance
     */
    constructor() {
        this.windowHashChangeArgs = null;
        this.params = null;
    }

    /**
     * Run the application
     *
     * @returns {DocPage}
     */
    static run() {
        const docPage = new DocPage();
        docPage.init();
        docPage.render();
        return docPage;
    }

    // Initialize the global application state
    init() {
        this.windowHashChangeArgs = ['hashchange', () => this.render(), false];
        window.addEventListener(...this.windowHashChangeArgs);
    }

    // Uninitialize the global application state
    uninit() {
        if (this.windowHashChangeArgs !== null) {
            window.removeEventListener(...this.windowHashChangeArgs);
            this.windowHashChangeArgs = null;
        }
    }

    // Helper function to parse and validate the hash parameters
    updateParams(params = null) {
        // Clear params and config
        this.params = null;

        // Validate the hash parameters (may throw)
        this.params = validateType(docPageTypes, 'DocPageParams', decodeParams(params));
    }

    // Helper function to render the documentation application page
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
        renderElements(document.body);

        // Type model URL provided?
        if ('name' in this.params) {
            // Call the request API
            window.fetch(`doc_request?name=${this.params.name}`).
                then((response) => {
                    if (!response.ok) {
                        throw new Error(`Could not fetch request '${this.params.name}': ${response.statusText}`);
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

    // Helper function to render an index page
    renderIndexPage(index) {
        document.title = index.title;
        renderElements(document.body, this.indexPage(index));
    }

    // Helper function to render a request page
    renderRequestPage(request) {
        document.title = request.name;
        renderElements(document.body, this.requestPage(request));
    }

    // Helper function to render an error page
    static renderErrorPage(message) {
        document.title = 'Error';
        renderElements(document.body, DocPage.errorPage(message));
    }

    // Helper function to generate the error page's element hierarchy model
    static errorPage(message) {
        return {
            'html': 'p',
            'elem': {'text': `Error: ${message}`}
        };
    }

    // Helper function to generate the index page's element hierarchy model
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
                            'elem': {'html': 'a', 'attr': {'href': href({...this.params, 'name': name})}, 'elem': {'text': name}}
                        })
                    )}}
                }
            ])
        ];
    }

    // Helper function to generate the request page's element hierarchy model
    requestPage(request) {
        // Compute the referenced types
        const userType = 'types' in request ? request.types[request.name] : null;
        const indexParams = {...this.params};
        delete indexParams.name;

        return [
            // Navigation bar
            {
                'html': 'p',
                'elem': {
                    'html': 'a',
                    'attr': {'href': href(indexParams)},
                    'elem': {'text': 'Back to documentation index'}
                }
            },

            userType !== null
                ? (new UserTypeElements(this.params)).getElements(request.types, request.name, request.urls)
                : [
                    {'html': 'h1', 'elem': {'text': request.name}},
                    UserTypeElements.markdownElem(request.doc),
                    UserTypeElements.getUrlNoteElements(request.urls)
                ]
        ];
    }
}
