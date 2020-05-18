// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/** The non-breaking space character. */
export const nbsp = String.fromCharCode(160);

/**
 * Render a document element hierarchy model.
 *
 * @param {Element} parent - The parent element to render within.
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 * @param {boolean} [clear=true] - If true, empty parent before rendering.
 */
export function render(parent, elems = null, clear = true) {
    if (clear) {
        parent.innerHTML = '';
    }
    appendElements(parent, elems);
}

/**
 * Helper function to create an Element object and append it to the given parent Element object.
 *
 * @param {Element} parent - The parent document element.
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 *
 * @ignore
 */
function appendElements(parent, elems = null) {
    if (Array.isArray(elems)) {
        for (let iElem = 0; iElem < elems.length; iElem++) {
            appendElements(parent, elems[iElem]);
        }
    } else if (elems !== null) {
        parent.appendChild(createElement(elems));
    }
}

/**
 * Create an Element object from a chisel.js element model object.
 *
 * @param {Object} element - A chisel.js element model object.
 * @returns {Element}
 *
 * @ignore
 */
function createElement(element) {
    let browserElement;

    // Create an element of the appropriate type
    if (element.text) {
        browserElement = document.createTextNode(element.text);
    } else if ('ns' in element) {
        browserElement = document.createElementNS(element.ns, element.tag);
    } else {
        browserElement = document.createElement(element.tag);
    }

    // Add attributes, if any, to the newly created element
    if ('attrs' in element) {
        for (const [attr, value] of Object.entries(element.attrs)) {
            // Skip null values as well as the special "_callback" attribute
            if (attr !== '_callback' && value !== null) {
                browserElement.setAttribute(attr, value);
            }
        }

        // Call the element callback, if any
        if ('_callback' in element.attrs && element.attrs._callback !== null) {
            element.attrs._callback(browserElement);
        }
    }

    // Create the newly created element's child elements
    appendElements(browserElement, element.elems);

    return browserElement;
}

/**
 * Create a chisel.js element model object.
 *
 * @param {string} tag - The element tag.
 * @param {Object} [attrs=null] - The element attributes.
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 * @param {string} [ns=null] - The element namespace.
 *     If null, the returned element is of the namespace "http://www.w3.org/1999/xhtml".
 * @returns {Object}
 */
export function elem(tag, attrs = null, elems = null, ns = null) {
    const element = {'tag': tag};
    if (attrs !== null) {
        element.attrs = attrs;
    }
    if (elems !== null) {
        element.elems = elems;
    }
    if (ns !== null) {
        element.ns = ns;
    }
    return element;
}

/**
 * Create a chisel.js SVG element model object.
 *
 * @param {string} tag - The element tag.
 * @param {Object} [attrs=null] - The element attributes.
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 * @returns {Object}
 */
export function svg(tag, attrs, elems) {
    return elem(tag, attrs, elems, 'http://www.w3.org/2000/svg');
}

/**
 * Create a chilel.js text model object.
 *
 * @param {string} str - The element text.
 * @returns {Object}
 */
export function text(str) {
    return {'text': str};
}

/**
 * Create a resource location string for the local server.
 *
 * @param {Object} [hash=null] - The hash parameters.
 * @param {Object} [queyr=null] - The query string parameters
 * @param {string} [pathname=null] - The location's path. If null, use "window.location.pathname".
 * @returns {string}
 */
export function href(hash = null, query = null, pathname = null) {
    // Encode the hash parameters, if any
    let hashStr = '';
    if (hash !== null) {
        hashStr = `#${encodeParams(hash)}`;
    } else if (query === null) {
        hashStr = '#';
    }

    // Encode the query parameters, if any
    let queryStr = '';
    if (query !== null) {
        queryStr = `?${encodeParams(query)}`;
        if (queryStr === '?') {
            queryStr = '';
        }
    }

    // No pathname provided? If so, provide a default.
    let pathname_ = pathname;
    if (pathname_ === null) {
        pathname_ = window.location.pathname;
    }

    return `${pathname_}${queryStr}${hashStr}`;
}

/**
 * URL-encode a parameters object.
 *
 * @param {Object} params - The parameters object.
 * @returns {string}
 */
export function encodeParams(params) {
    const items = [];
    Object.keys(params).sort().forEach((name) => {
        // Skip null values
        if (params[name] !== null) {
            items.push(`${encodeURIComponent(name)}=${encodeURIComponent(params[name])}`);
        }
    });
    return items.join('&');
}

/**
 * URL-decode a paramaters string.
 *
 * @params {string} [paramStr=null] - The parameters string.
 *     If null, "window.location.hash.substring(1)" is used.
 * @returns {Object}
 */
export function decodeParams(paramStr = null) {
    // No parameters string provided? If so, provide a default
    let paramStr_ = paramStr;
    if (paramStr_ === null) {
        paramStr_ = window.location.hash.substring(1);
    }

    // Decode the parameter string key/values
    const rNextKeyValue = /([^&=]+)=?([^&]*)/g;
    let match;
    const params = {};
    while ((match = rNextKeyValue.exec(paramStr_)) !== null) {
        params[decodeURIComponent(match[1])] = decodeURIComponent(match[2]);
    }

    return params;
}
