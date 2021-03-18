// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {validateType} from '../schemaMarkdown/schema.js';


/**
 * Validate an element model
 *
 * @param {?(Object|Array)} elements - The element model.
 *     An element model is either null, an element object, or an array of any of these.
 * @throws {Error} Validation error string
 */
export function validateElements(elements) {
    // Array?
    if (Array.isArray(elements)) {
        // Validate the sub-elements
        for (const subElements of elements) {
            validateElements(subElements);
        }

    // Non-null?
    } else if (elements !== null) {
        // Validation error exception helper function
        const throwValueError = (message, value) => {
            const valueStr = `${JSON.stringify(value)}`;
            throw new Error(`${message} ${valueStr.slice(0, 100)} (type '${typeof value}')`);
        };

        // Non-object?
        if (typeof elements !== 'object') {
            throwValueError('Invalid element', elements);
        }

        // Validate the element model
        validateType(elementTypes, 'Element', elements);

        // Validate creation callback
        if ('callback' in elements && typeof elements.callback !== 'function') {
            throwValueError('Invalid element callback function', elements.callback);
        }

        // Text?
        if ('text' in elements) {
            // Text elements don't have attributes or children
            if ('attr' in elements) {
                throwValueError('Invalid text element member "attr"', elements.text);
            }
            if ('elem' in elements) {
                throwValueError('Invalid text element member "elem"', elements.text);
            }

        // HTML or SVG?
        } else if ('html' in elements || 'svg' in elements) {
            // Validate the sub-elements
            if ('elem' in elements) {
                validateElements(elements.elem);
            }
        } else {
            throwValueError('Missing element key', elements);
        }
    }
}


// The element model
const elementTypes = {
    'Element': {
        'struct': {
            'name': 'Element',
            'members': [
                {
                    'name': 'html',
                    'doc': ['HTML element tag'],
                    'type': {'builtin': 'string'},
                    'attr': {'lenGT': 0, 'lenLT': 100},
                    'optional': true
                },
                {
                    'name': 'svg',
                    'doc': ['SVG element tag'],
                    'type': {'builtin': 'string'},
                    'attr': {'lenGT': 0, 'lenLT': 100},
                    'optional': true
                },
                {
                    'name': 'text',
                    'doc': ["text element's text"],
                    'type': {'builtin': 'string'},
                    'optional': true
                },
                {
                    'name': 'attr',
                    'doc': ["The element's attribute dictionary"],
                    'type': {'dict': {'type': {'builtin': 'object'}, 'attr': {'nullable': true}, 'keyAttr': {'lenGT': 0, 'lenLT': 100}}},
                    'attr': {'nullable': true},
                    'optional': true
                },
                {
                    'name': 'elem',
                    'doc': ['An element model or an array of element models'],
                    'type': {'builtin': 'object'},
                    'attr': {'nullable': true},
                    'optional': true
                },
                {
                    'name': 'callback',
                    'doc': ['The element creation callback function'],
                    'type': {'builtin': 'object'},
                    'optional': true
                }
            ]
        }
    }
};
