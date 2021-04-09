// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {
    SchemaMarkdownParser, UserTypeElements, decodeQueryString, encodeHref, renderElements, validateType
} from './schema-markdown/index.js';


const docPageTypes = (new SchemaMarkdownParser(`\
# The Chisel documentation application hash parameters type model
struct Documentation

    # The request name. If not provided, the index is displayed.
    optional string(len > 0) name

    # Optional command
    optional DocumentationCommand cmd

# The Chisel documentation application command union
union DocumentationCommand

    # Render the application's hash parameter model documentation
    int(==1) help
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
        this.params = validateType(docPageTypes, 'Documentation', decodeQueryString(params));
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

        // Command provided?
        if ('cmd' in this.params) {
            // 'help' in this.params.cmd
            document.title = 'Documentation';
            renderElements(document.body, (new UserTypeElements(this.params)).getElements(docPageTypes, 'Documentation'));
        } else if ('name' in this.params) {
            // Call the request API
            window.fetch(`doc_request?name=${this.params.name}`).
                then((response) => {
                    if (!response.ok) {
                        throw new Error(`Could not fetch request '${this.params.name}': ${response.statusText}`);
                    }
                    return response.json();
                }).
                then((request) => {
                    document.title = request.name;
                    renderElements(document.body, this.requestPage(request));
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
                    document.title = index.title;
                    renderElements(document.body, this.indexPage(index));
                }).catch(({message}) => {
                    DocPage.renderErrorPage(message);
                });
        }
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
                    'attr': {'class': 'smd-index-list'},
                    'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': index.groups[group].sort().map(
                        (name) => ({
                            'html': 'li',
                            'elem': {'html': 'a', 'attr': {'href': encodeHref({...this.params, 'name': name})}, 'elem': {'text': name}}
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
                    'attr': {'href': encodeHref(indexParams)},
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
