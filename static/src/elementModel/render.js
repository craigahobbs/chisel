// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {validateElements} from './model.js';


/**
 * Render an element model
 *
 * @param {Element} parent - The parent element to render within
 * @param {?(Object|Array)} [elements=null] - The element model.
 *     An element model is either null, an element object, or an array of any of these.
 * @param {boolean} [clear=true] - If true, empty parent before rendering
 */
export function renderElements(parent, elements = null, clear = true) {
    validateElements(elements);
    if (clear) {
        parent.innerHTML = '';
    }
    renderElementsHelper(parent, elements);
}


/**
 * Helper function to create an Element object and append it to the given parent Element object
 *
 * @param {Element} parent - The parent document element
 * @param {?(Object|Array)} elements - The element model.
 *     An element model is either null, an element object, or an array of any of these.
 *
 * @ignore
 */
function renderElementsHelper(parent, elements) {
    if (Array.isArray(elements)) {
        for (const element of elements) {
            renderElementsHelper(parent, element);
        }
    } else if (elements !== null) {
        const element = elements;
        let browserElement;

        // Create an element of the appropriate type
        if ('text' in element) {
            browserElement = document.createTextNode(element.text);
        } else if ('svg' in element) {
            browserElement = document.createElementNS('http://www.w3.org/2000/svg', element.svg);
        } else {
            browserElement = document.createElement(element.html);
        }

        // Add attributes, if any, to the newly created element
        if ('attr' in element && element.attr !== null) {
            for (const [attr, value] of Object.entries(element.attr)) {
                // Skip null values
                if (value !== null) {
                    browserElement.setAttribute(attr, `${value}`);
                }
            }
        }

        // Create the newly created element's child elements
        if ('elem' in element) {
            renderElementsHelper(browserElement, element.elem);
        }

        // Add the child element
        parent.appendChild(browserElement);

        // Call the element callback, if any
        if ('callback' in element) {
            element.callback(browserElement);
        }
    }
}
