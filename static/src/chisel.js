// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {typeModel} from './typeModel.js';


/** The non-breaking space character. */
export const nbsp = String.fromCharCode(160);


/**
 * Check if a URL is absolute
 *
 * @param {string} url - The URL
 * @returns {bool} true if the URL is absolute, false otherwise
 */
export function isAbsoluteURL(url) {
    return rAbsoluteURL.test(url);
}

const rAbsoluteURL = /^[a-z]{3,5}:/;


/**
 * Get a URL's base URL
 *
 * @param {string} url - The URL
 * @returns {string} The base URL or the URL
 */
export function getBaseURL(url) {
    const ixBaseSlash = url.lastIndexOf('/');
    return ixBaseSlash === -1 ? '' : url.slice(0, ixBaseSlash + 1);
}


/**
 * Render an element model
 *
 * @param {Element} parent - The parent element to render within
 * @param {?(Object|Array)} [elements=null] - The element model.
 *     An element model is either null, an element object, or an array of any of these.
 * @param {boolean} [clear=true] - If true, empty parent before rendering
 */
export function render(parent, elements = null, clear = true) {
    validateElements(elements);
    if (clear) {
        parent.innerHTML = '';
    }
    renderElements(parent, elements);
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
function renderElements(parent, elements) {
    if (Array.isArray(elements)) {
        for (const element of elements) {
            renderElements(parent, element);
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
            renderElements(browserElement, element.elem);
        }

        // Add the child element
        parent.appendChild(browserElement);

        // Call the element callback, if any
        if ('callback' in element) {
            element.callback(browserElement);
        }
    }
}


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


/**
 * Create a resource location string for the local server.
 *
 * @param {Object} [hash=null] - The hash parameters
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
 * Encode an object as a query/hash string. Dictionaries, lists, and tuples are recursed. Each member key is expressed
 * in fully-qualified form. List keys are the index into the list, and are in order.
 *
 * @param {Object} obj - The parameters object
 * @returns {string}
 */
export function encodeParams(obj) {
    return encodeParamsHelper(obj).join('&');
}


/**
 * Helper function for encodeParams
 *
 * @param {Object} obj - The parameters object
 * @param {string} memberFqn - The fully qualified member name. If null, this is a top-level object.
 * @param {string} keyValues - The list of encoded key/value strings
 * @returns {string[]}
 *
 * @ignore
 */
function encodeParamsHelper(obj, memberFqn = null, keyValues = []) {
    const objType = typeof obj;
    if (Array.isArray(obj)) {
        if (obj.length === 0) {
            keyValues.push(memberFqn !== null ? `${memberFqn}=` : '');
        } else {
            for (let ix = 0; ix < obj.length; ix++) {
                encodeParamsHelper(obj[ix], memberFqn !== null ? `${memberFqn}.${ix}` : `${ix}`, keyValues);
            }
        }
    } else if (obj instanceof Date) {
        const objEncoded = encodeURIComponent(obj.toISOString());
        keyValues.push(memberFqn !== null ? `${memberFqn}=${objEncoded}` : `${objEncoded}`);
    } else if (obj !== null && typeof obj === 'object') {
        const keys = Object.keys(obj).sort();
        if (keys.length === 0) {
            keyValues.push(memberFqn !== null ? `${memberFqn}=` : '');
        } else {
            for (const key of keys) {
                const keyEncoded = encodeParamsHelper(key);
                encodeParamsHelper(obj[key], memberFqn !== null ? `${memberFqn}.${keyEncoded}` : `${keyEncoded}`, keyValues);
            }
        }
    } else if (obj === null || objType === 'boolean' || objType === 'number') {
        keyValues.push(memberFqn !== null ? `${memberFqn}=${obj}` : `${obj}`);
    } else {
        const objEncoded = encodeURIComponent(obj);
        keyValues.push(memberFqn !== null ? `${memberFqn}=${objEncoded}` : `${objEncoded}`);
    }
    return keyValues;
}


/**
 * Decode an object from a query/hash string. Each member key of the query string is expressed in fully-qualified
 * form. List keys are the index into the list, must be in order.
 *
 * @param {string} [paramStr=null] - The parameters string.
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
    const result = [null];
    paramStr_.split('&').filter((keyValue) => keyValue.length).forEach(
        (keyValue, ixKeyValue, keyValuesFiltered) => {
            const [keyFqn, valueEncoded = null] = keyValue.split('=');
            if (valueEncoded === null) {
                // Ignore anchor tags
                if (ixKeyValue === keyValuesFiltered.length - 1) {
                    return;
                }
                throw new Error(`Invalid key/value pair '${keyValue.slice(0, 100)}'`);
            }
            const value = decodeURIComponent(valueEncoded);

            // Find/create the object on which to set the value
            let parent = result;
            let keyParent = 0;
            const keys = keyFqn.split('.');
            for (const keyEncoded of keys) {
                let key = decodeURIComponent(keyEncoded);
                let obj = parent[keyParent];

                // Array key?  First "key" of an array must start with "0".
                if (Array.isArray(obj) || (obj === null && key === '0')) {
                    // Create this key's container, if necessary
                    if (obj === null) {
                        obj = [];
                        parent[keyParent] = obj;
                    }

                    // Parse the key as an integer
                    if (isNaN(key)) {
                        throw new Error(`Invalid array index '${key.slice(0, 100)}' in key '${keyFqn.slice(0, 100)}'`);
                    }
                    const keyOrig = key;
                    key = parseInt(key, 10);

                    // Append the value placeholder null
                    if (key === obj.length) {
                        obj.push(null);
                    } else if (key < 0 || key > obj.length) {
                        throw new Error(`Invalid array index '${keyOrig.slice(0, 100)}' in key '${keyFqn.slice(0, 100)}'`);
                    }
                } else {
                    // Create this key's container, if necessary
                    if (obj === null) {
                        obj = {};
                        parent[keyParent] = obj;
                    }

                    // Create the index for this key
                    if (!(key in obj)) {
                        obj[key] = null;
                    }
                }

                // Update the parent object and key
                parent = obj;
                keyParent = key;
            }

            // Set the value
            if (parent[keyParent] !== null) {
                throw new Error(`Duplicate key '${keyFqn.slice(0, 100)}'`);
            }
            parent[keyParent] = value;
        }
    );

    return result[0] !== null ? result[0] : {};
}


/**
 * Get a user type's referenced type model
 *
 * @param {Object} types - The map of user type name to user type model
 * @param {string} typeName - The type name
 * @param {Object} [referencedTypes=null] - Optional map of referenced user type name to user type model
 * @returns {Object}
 */
export function getReferencedTypes(types, typeName, referencedTypes = {}) {
    return getReferencedTypesHelper(types, {'user': typeName}, referencedTypes);
}


/**
 * Get a type's referenced type model
 *
 * @param {Object} types - The map of user type name to user type model
 * @param {string} type - The type model
 * @param {Object} [referencedTypes=null] - Optional map of referenced user type name to user type model
 * @returns {Object}
 *
 * @ignore
 */
// eslint-disable-next-line no-unused-vars
function getReferencedTypesHelper(types, type, referencedTypes) {
    // Array?
    if ('array' in type) {
        const {array} = type;
        getReferencedTypesHelper(types, array.type, referencedTypes);

    // Dict?
    } else if ('dict' in type) {
        const {dict} = type;
        getReferencedTypesHelper(types, dict.type, referencedTypes);
        if ('keyType' in dict) {
            getReferencedTypesHelper(types, dict.keyType, referencedTypes);
        }

    // User type?
    } else if ('user' in type) {
        const typeName = type.user;

        // Already encountered?
        if (!(typeName in referencedTypes)) {
            const userType = types[typeName];
            referencedTypes[typeName] = userType;

            // Struct?
            if ('struct' in userType) {
                const {struct} = userType;
                if ('members' in struct) {
                    for (const member of struct.members) {
                        getReferencedTypesHelper(types, member.type, referencedTypes);
                    }
                }

            // Typedef?
            } else if ('typedef' in userType) {
                const {typedef} = userType;
                getReferencedTypesHelper(types, typedef.type, referencedTypes);

            // Action?
            } else if ('action' in userType) {
                const {action} = userType;
                if ('path' in action) {
                    getReferencedTypesHelper(types, {'user': action.path}, referencedTypes);
                }
                if ('query' in action) {
                    getReferencedTypesHelper(types, {'user': action.query}, referencedTypes);
                }
                if ('input' in action) {
                    getReferencedTypesHelper(types, {'user': action.input}, referencedTypes);
                }
                if ('output' in action) {
                    getReferencedTypesHelper(types, {'user': action.output}, referencedTypes);
                }
                if ('errors' in action) {
                    getReferencedTypesHelper(types, {'user': action.errors}, referencedTypes);
                }
            }
        }
    }

    return referencedTypes;
}


/**
 * Type-validate a value using a user type model. Container values are duplicated since some member types are
 * transformed during validation.
 *
 * @param {Object} types - The map of user type name to user type model
 * @param {string} typeName - The type name
 * @param {Object} value - The value object to validate
 * @param {string} [memberFqn=null] - Optional fully-qualified member name
 * @returns {Object} The validated, transformed value object
 * @throws {Error} Validation error string
 */
export function validateType(types, typeName, value, memberFqn = null) {
    if (!(typeName in types)) {
        throw new Error(`Unknown type '${typeName}'`);
    }
    return validateTypeHelper(types, {'user': typeName}, value, memberFqn);
}


// Regular expressions used by validateTypeHelper
const rDate = /^\d{4}-\d{2}-\d{2}$/;
const rDatetime = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})$/;


/**
 * Type-validate a value using a type model
 *
 * @param {Object} types - The map of user type name to user type model
 * @param {Object} type - The type object model
 * @param {Object} value - The value object to validate
 * @param {string} memberFqn - The fully-qualified member name
 * @returns {Object} The validated, transformed value object
 * @throws {Error} Validation error string
 *
 * @ignore
 */
function validateTypeHelper(types, type, value, memberFqn) {
    let valueNew = value;

    // Built-in type?
    if ('builtin' in type) {
        const {builtin} = type;

        // string or uuid?
        if (builtin === 'string' || builtin === 'uuid') {
            // Not a string?
            if (typeof value !== 'string') {
                throwMemberError(type, value, memberFqn);
            }

            // Not a valid UUID?
            if (builtin === 'uuid' && !value.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$/i)) {
                throwMemberError(type, value, memberFqn);
            }

        // int or float?
        } else if (builtin === 'int' || builtin === 'float') {
            // Convert string?
            if (typeof value === 'string') {
                if (isNaN(value)) {
                    throwMemberError(type, value, memberFqn);
                }
                valueNew = parseFloat(value);

            // Not a number?
            } else if (typeof value !== 'number') {
                throwMemberError(type, value, memberFqn);

            // Non-int number?
            } else if (builtin === 'int' && Math.trunc(value) !== value) {
                throwMemberError(type, value, memberFqn);
            }

        // bool?
        } else if (builtin === 'bool') {
            // Convert string?
            if (typeof value === 'string') {
                if (value === 'true') {
                    valueNew = true;
                } else if (value === 'false') {
                    valueNew = false;
                } else {
                    throwMemberError(type, value, memberFqn);
                }

            // Not a bool?
            } else if (typeof value !== 'boolean') {
                throwMemberError(type, value, memberFqn);
            }

        // date or datetime?
        } else if (builtin === 'date' || builtin === 'datetime') {
            // Convert string?
            if (typeof value === 'string') {
                valueNew = new Date(value);
                if (isNaN(valueNew)) {
                    throwMemberError(type, value, memberFqn);
                }

                // Invalid date format?
                if (!(rDate.test(value) || rDatetime.test(value))) {
                    throwMemberError(type, value, memberFqn);
                }

            // Not a date?
            } else if (!(value instanceof Date)) {
                throwMemberError(type, value, memberFqn);
            }

            // For date type, clear hours, minutes, seconds, and milliseconds
            if (builtin === 'date') {
                valueNew = new Date(valueNew.getFullYear(), valueNew.getMonth(), valueNew.getUTCDate());
            }
        }

    // array?
    } else if ('array' in type) {
        // Valid value type?
        const {array} = type;
        const arrayType = array.type;
        const arrayAttr = 'attr' in array ? array.attr : null;
        if (value === '') {
            valueNew = [];
        } else if (!Array.isArray(value)) {
            throwMemberError(type, value, memberFqn);
        }

        // Validate the list contents
        const valueCopy = [];
        const arrayValueNullable = arrayAttr !== null && 'nullable' in arrayAttr && arrayAttr.nullable;
        for (let ixArrayValue = 0; ixArrayValue < valueNew.length; ixArrayValue++) {
            const memberFqnValue = memberFqn !== null ? `${memberFqn}.${ixArrayValue}` : `${ixArrayValue}`;
            let arrayValue = valueNew[ixArrayValue];
            if (arrayValue === null || (arrayValueNullable && arrayValue === 'null')) {
                arrayValue = null;
            } else {
                arrayValue = validateTypeHelper(types, arrayType, arrayValue, memberFqnValue);
            }
            validateAttr(arrayType, arrayAttr, arrayValue, memberFqnValue);
            valueCopy.push(arrayValue);
        }

        // Return the validated, transformed copy
        valueNew = valueCopy;

    // dict?
    } else if ('dict' in type) {
        // Valid value type?
        const {dict} = type;
        const dictType = dict.type;
        const dictAttr = 'attr' in dict ? dict.attr : null;
        const dictKeyType = 'keyType' in dict ? dict.keyType : {'builtin': 'string'};
        const dictKeyAttr = 'keyAttr' in dict ? dict.keyAttr : null;
        if (value === '') {
            valueNew = {};
        } else if (typeof value !== 'object') {
            throwMemberError(type, value, memberFqn);
        }

        // Validate the dict key/value pairs
        const valueCopy = valueNew instanceof Map ? new Map() : {};
        const dictKeyNullable = dictKeyAttr !== null && 'nullable' in dictKeyAttr && dictKeyAttr.nullable;
        const dictValueNullable = dictAttr !== null && 'nullable' in dictAttr && dictAttr.nullable;
        for (let [dictKey, dictValue] of (valueNew instanceof Map ? valueNew.entries() : Object.entries(valueNew))) {
            const memberFqnKey = memberFqn !== null ? `${memberFqn}.${dictKey}` : `${dictKey}`;

            // Validate the key
            if (dictKey === null || (dictKeyNullable && dictKey === 'null')) {
                dictKey = null;
            } else {
                dictKey = validateTypeHelper(types, dictKeyType, dictKey, memberFqn);
            }
            validateAttr(dictKeyType, dictKeyAttr, dictKey, memberFqn);

            // Validate the value
            if (dictValue === null || (dictValueNullable && dictValue === 'null')) {
                dictValue = null;
            } else {
                dictValue = validateTypeHelper(types, dictType, dictValue, memberFqnKey);
            }
            validateAttr(dictType, dictAttr, dictValue, memberFqnKey);

            // Copy the key/value
            if (valueCopy instanceof Map) {
                valueCopy.set(dictKey, dictValue);
            } else {
                valueCopy[dictKey] = dictValue;
            }
        }

        // Return the validated, transformed copy
        valueNew = valueCopy;

    // User type?
    } else if ('user' in type) {
        const userType = types[type.user];

        // action?
        if ('action' in userType) {
            throwMemberError(type, value, memberFqn);
        }

        // typedef?
        if ('typedef' in userType) {
            const {typedef} = userType;
            const typedefAttr = 'attr' in typedef ? typedef.attr : null;

            // Validate the value
            const valueNullable = typedefAttr !== null && 'nullable' in typedefAttr && typedefAttr.nullable;
            if (value === null || (valueNullable && value === 'null')) {
                valueNew = null;
            } else {
                valueNew = validateTypeHelper(types, typedef.type, value, memberFqn);
            }
            validateAttr(type, typedefAttr, valueNew, memberFqn);

        // enum?
        } else if ('enum' in userType) {
            const enum_ = userType.enum;

            // Not a valid enum value?
            if (!('values' in enum_) || !enum_.values.some((enumValue) => value === enumValue.name)) {
                throwMemberError(type, value, memberFqn);
            }

        // struct?
        } else if ('struct' in userType) {
            const {struct} = userType;

            // Valid value type?
            if (value === '') {
                valueNew = {};
            } else if (typeof value !== 'object') {
                throwMemberError({'user': struct.name}, value, memberFqn);
            }

            // Valid union?
            const isUnion = 'union' in struct ? struct.union : false;
            if (isUnion) {
                if (Object.keys(value).length !== 1) {
                    throwMemberError({'user': struct.name}, value, memberFqn);
                }
            }

            // Validate the struct members
            const valueCopy = valueNew instanceof Map ? new Map() : {};
            if ('members' in struct) {
                for (const member of struct.members) {
                    const memberName = member.name;
                    const memberFqnMember = memberFqn !== null ? `${memberFqn}.${memberName}` : `${memberName}`;
                    const memberOptional = 'optional' in member ? member.optional : false;

                    // Missing non-optional member?
                    if (!(valueNew instanceof Map ? valueNew.has(memberName) : memberName in valueNew)) {
                        if (!memberOptional && !isUnion) {
                            throw new Error(`Required member '${memberFqnMember}' missing`);
                        }
                    } else {
                        // Validate the member value
                        let memberValue = valueNew instanceof Map ? valueNew.get(memberName) : valueNew[memberName];
                        if (memberValue !== null) {
                            memberValue = validateTypeHelper(types, member.type, memberValue, memberFqnMember);
                        }
                        validateAttr(member.type, 'attr' in member ? member.attr : null, memberValue, memberFqnMember);

                        // Copy the validated member
                        if (valueCopy instanceof Map) {
                            valueCopy.set(memberName, memberValue);
                        } else {
                            valueCopy[memberName] = memberValue;
                        }
                    }
                }
            }

            // Any unknown members?
            const valueCopyKeys = valueCopy instanceof Map ? Array.from(valueCopy.keys()) : Object.keys(valueCopy);
            const valueNewKeys = valueNew instanceof Map ? Array.from(valueNew.keys()) : Object.keys(valueNew);
            if (valueCopyKeys.length !== valueNewKeys.length) {
                let unknownKey;
                if ('members' in struct) {
                    const memberSet = new Set(struct.members.map((member) => member.name));
                    [unknownKey] = valueNewKeys.filter((key) => !memberSet.has(key));
                } else {
                    [unknownKey] = valueNewKeys;
                }
                const unknownFqn = memberFqn !== null ? `${memberFqn}.${unknownKey}` : `${unknownKey}`;
                throw new Error(`Unknown member '${unknownFqn.slice(0, 100)}'`);
            }

            // Return the validated, transformed copy
            valueNew = valueCopy;
        }
    }

    return valueNew;
}


/**
 * Throw a member validation error
 *
 * @param {Object} type - The type object model
 * @param {Object} value - The invalid value
 * @param {string} memberFqn - The fully-qualified member name
 * @param {string} [attr = null] - Optional attribute string
 * @throws {Error} Validation error string
 *
 * @ignore
 */
function throwMemberError(type, value, memberFqn, attr = null) {
    const memberPart = memberFqn !== null ? ` for member '${memberFqn}'` : '';
    const typeName = 'builtin' in type ? type.builtin : ('array' in type ? 'array' : ('dict' in type ? 'dict' : type.user));
    const attrPart = attr !== null ? ` [${attr}]` : '';
    const valueStr = `${JSON.stringify(value)}`;
    const msg = `Invalid value ${valueStr.slice(0, 100)} (type '${typeof value}')${memberPart}, expected type '${typeName}'${attrPart}`;
    throw new Error(msg);
}

/**
 * Attribute-validate a value using an attribute model
 *
 * @param {Object} type - The type object model
 * @param {?Object} attr - The attribute model
 * @param {Object} value - The value object to validate
 * @param {string} memberFqn - The fully-qualified member name
 * @throws {Error} Validation error string
 *
 * @ignore
 */
function validateAttr(type, attr, value, memberFqn) {
    if (value === null) {
        const valueNullable = attr !== null && 'nullable' in attr && attr.nullable;
        if (!valueNullable) {
            throwMemberError(type, value, memberFqn);
        }
    } else if (attr !== null) {
        const length = Array.isArray(value) || typeof value === 'string' ? value.length
            : (typeof value === 'object' ? Object.keys(value).length : null);

        if ('eq' in attr && !(value === attr.eq)) {
            throwMemberError(type, value, memberFqn, `== ${attr.eq}`);
        }
        if ('lt' in attr && !(value < attr.lt)) {
            throwMemberError(type, value, memberFqn, `< ${attr.lt}`);
        }
        if ('lte' in attr && !(value <= attr.lte)) {
            throwMemberError(type, value, memberFqn, `<= ${attr.lte}`);
        }
        if ('gt' in attr && !(value > attr.gt)) {
            throwMemberError(type, value, memberFqn, `> ${attr.gt}`);
        }
        if ('gte' in attr && !(value >= attr.gte)) {
            throwMemberError(type, value, memberFqn, `>= ${attr.gte}`);
        }
        if ('lenEq' in attr && !(length === attr.lenEq)) {
            throwMemberError(type, value, memberFqn, `len == ${attr.lenEq}`);
        }
        if ('lenLT' in attr && !(length < attr.lenLT)) {
            throwMemberError(type, value, memberFqn, `len < ${attr.lenLT}`);
        }
        if ('lenLTE' in attr && !(length <= attr.lenLTE)) {
            throwMemberError(type, value, memberFqn, `len <= ${attr.lenLTE}`);
        }
        if ('lenGT' in attr && !(length > attr.lenGT)) {
            throwMemberError(type, value, memberFqn, `len > ${attr.lenGT}`);
        }
        if ('lenGTE' in attr && !(length >= attr.lenGTE)) {
            throwMemberError(type, value, memberFqn, `len >= ${attr.lenGTE}`);
        }
    }
}


/**
 * Validate a type model's types object
 *
 * @param {Object} types - The map of user type name to user type model
 * @returns {Object} The validated, transformed types object
 */
export function validateTypeModelTypes(types) {
    // Validate with the type model
    const validatedTypes = validateType(typeModel.types, 'Types', types);

    // Do additional type model validation
    const errors = validateTypesErrors(validatedTypes);
    if (errors.length) {
        throw new Error(errors.map(([,, message]) => message).join('\n'));
    }

    return validatedTypes;
}


/**
 * Validate a user type model
 *
 * @param {Object} userTypeModel - The user type model
 * @returns {Object} The validated, transformed type model
 */
export function validateTypeModel(userTypeModel) {
    // Validate with the type model
    const validatedUserTypeModel = validateType(typeModel.types, 'TypeModel', userTypeModel);

    // Do additional type model validation
    const errors = validateTypesErrors(validatedUserTypeModel.types);
    if (errors.length) {
        throw new Error(errors.map(([,, message]) => message).join('\n'));
    }

    return validatedUserTypeModel;
}


/**
 * Get a type model's effective type (e.g. typedef int is an int)
 *
 * @param {Object} types: The map of user type name to user type model
 * @param {Object} type: The type model
 *
 * @ignore
 */
function getEffectiveType(types, type) {
    if ('user' in type && type.user in types) {
        const userType = types[type.user];
        if ('typedef' in userType) {
            return getEffectiveType(types, userType.typedef.type);
        }
    }
    return type;
}


/**
 * Count string occurrences in an array of strings
 *
 * @param {string[]} strings - The array of strings
 * @returns {Object} The map of string to number of occurrences
 *
 * @ignore
 */
function countStrings(strings, stringCounts = {}) {
    for (const string of strings) {
        if (string in stringCounts) {
            stringCounts[string] += 1;
        } else {
            stringCounts[string] = 1;
        }
    }
    return stringCounts;
}


/**
 * Helper function to validate user type dictionary
 *
 * @param {Object} types - The map of user type name to user type model
 * @returns {Array<Array>} The list of type name, member name, and error message tuples
 *
 * @ignore
 */
function validateTypesErrors(types) {
    const errors = [];

    // Check each user type
    for (const [typeName, userType] of Object.entries(types)) {
        // Struct?
        /* istanbul ignore else */
        if ('struct' in userType) {
            const {struct} = userType;

            // Inconsistent type name?
            if (typeName !== struct.name) {
                errors.push([typeName, null, `Inconsistent type name '${struct.name}' for '${typeName}'`]);
            }

            // Has members?
            if ('members' in struct) {
                // Check member types and their attributes
                for (const member of struct.members) {
                    validateTypesType(errors, types, member.type, 'attr' in member ? member.attr : null, struct.name, member.name);
                }

                // Check for duplicate members
                const memberCounts = countStrings(struct.members.map((member) => member.name));
                for (const [memberName, memberCount] of Object.entries(memberCounts)) {
                    if (memberCount > 1) {
                        errors.push([typeName, memberName, `Redefinition of '${typeName}' member '${memberName}'`]);
                    }
                }
            }

        // Enum?
        } else if ('enum' in userType) {
            const enum_ = userType.enum;

            // Inconsistent type name?
            if (typeName !== enum_.name) {
                errors.push([typeName, null, `Inconsistent type name '${enum_.name}' for '${typeName}'`]);
            }

            // Check for duplicate enumeration values
            if ('values' in enum_) {
                const valueCounts = countStrings(enum_.values.map((value) => value.name));
                for (const [valueName, valueCount] of Object.entries(valueCounts)) {
                    if (valueCount > 1) {
                        errors.push([typeName, valueName, `Redefinition of '${typeName}' value '${valueName}'`]);
                    }
                }
            }

        // Typedef?
        } else if ('typedef' in userType) {
            const {typedef} = userType;

            // Inconsistent type name?
            if (typeName !== typedef.name) {
                errors.push([typeName, null, `Inconsistent type name '${typedef.name}' for '${typeName}'`]);
            }

            // Check the type and its attributes
            validateTypesType(errors, types, typedef.type, 'attr' in typedef ? typedef.attr : null, typeName, null);

        // Action?
        } else if ('action' in userType) {
            const {action} = userType;

            // Inconsistent type name?
            if (typeName !== action.name) {
                errors.push([typeName, null, `Inconsistent type name '${action.name}' for '${typeName}'`]);
            }

            // Check action section types
            for (const section of ['path', 'query', 'input', 'output', 'errors']) {
                if (section in action) {
                    const sectionTypeName = action[section];

                    // Check the section type
                    validateTypesType(errors, types, {'user': sectionTypeName}, null, typeName, null);
                }
            }

            // Compute effective input member counts
            const memberCounts = {};
            const memberSections = {};
            for (const section of ['path', 'query', 'input']) {
                if (section in action) {
                    const sectionTypeName = action[section];
                    if (sectionTypeName in types) {
                        const sectionType = getEffectiveType(types, {'user': sectionTypeName});
                        if ('user' in sectionType && 'struct' in types[sectionType.user]) {
                            const sectionStruct = types[sectionType.user].struct;
                            if ('members' in sectionStruct) {
                                countStrings(sectionStruct.members.map((member) => member.name), memberCounts);
                                for (const member of sectionStruct.members) {
                                    if (!(member.name in memberSections)) {
                                        memberSections[member.name] = [];
                                    }
                                    memberSections[member.name].push(sectionStruct.name);
                                }
                            }
                        }
                    }
                }
            }

            // Check for duplicate input members
            for (const [memberName, memberCount] of Object.entries(memberCounts)) {
                if (memberCount > 1) {
                    for (const sectionType of memberSections[memberName]) {
                        errors.push([sectionType, memberName, `Redefinition of '${sectionType}' member '${memberName}'`]);
                    }
                }
            }
        }
    }

    return errors;
}


// Map of attribute struct member name to attribute description
const attrToText = {
    'eq': '==',
    'lt': '<',
    'lte': '<=',
    'gt': '>',
    'gte': '>=',
    'lenEq': 'len ==',
    'lenLT': 'len <',
    'lenLTE': 'len <=',
    'lenGT': 'len >',
    'lenGTE': 'len >='
};


// Map of type name to valid attribute set
const typeToAllowedAttr = {
    'float': ['eq', 'lt', 'lte', 'gt', 'gte'],
    'int': ['eq', 'lt', 'lte', 'gt', 'gte'],
    'string': ['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE'],
    'array': ['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE'],
    'dict': ['lenEq', 'lenLT', 'lenLTE', 'lenGT', 'lenGTE']
};


/**
 * Helper function for validateTypes to validate a type model
 *
 * @param {Array<Array>} The list of type name, member name, and error message tuples
 * @param {Object} types - The map of user type name to user type model
 * @param {Object} type - The type model
 * @param {Object} attr - The type attribute model
 * @param {string} typeName - The containing type's name
 * @param {string} memberName - The contianing struct's member name
 * @returns {Array<Array>} The list of type name, member name, and error message tuples
 *
 * @ignore
 */
function validateTypesType(errors, types, type, attr, typeName, memberName) {
    // Helper function to push an error tuple
    const error = (message) => {
        if (memberName !== null) {
            errors.push([typeName, memberName, `${message} from '${typeName}' member '${memberName}'`]);
        } else {
            errors.push([typeName, null, `${message} from '${typeName}'`]);
        }
    };

    // Array?
    if ('array' in type) {
        const {array} = type;

        // Check the type and its attributes
        const arrayType = getEffectiveType(types, array.type);
        validateTypesType(errors, types, arrayType, 'attr' in array ? array.attr : null, typeName, memberName);

    // Dict?
    } else if ('dict' in type) {
        const {dict} = type;

        // Check the type and its attributes
        const dictType = getEffectiveType(types, dict.type);
        validateTypesType(errors, types, dictType, 'attr' in dict ? dict.attr : null, typeName, memberName);

        // Check the dict key type and its attributes
        if ('keyType' in dict) {
            const dictKeyType = getEffectiveType(types, dict.keyType);
            validateTypesType(errors, types, dictKeyType, 'keyAttr' in dict ? dict.keyAttr : null, typeName, memberName);

            // Valid dict key type (string or enum)
            if (!('builtin' in dictKeyType && dictKeyType.builtin === 'string') &&
                !('user' in dictKeyType && dictKeyType.user in types && 'enum' in types[dictKeyType.user])) {
                error('Invalid dictionary key type');
            }
        }

    // User type?
    } else if ('user' in type) {
        const userTypeName = type.user;

        // Unknown user type?
        if (!(userTypeName in types)) {
            error(`Unknown type '${userTypeName}'`);
        } else {
            const userType = types[userTypeName];

            // Action type references not allowed
            if ('action' in userType) {
                error(`Invalid reference to action '${userTypeName}'`);
            }
        }
    }

    // Any not-allowed attributes?
    if (attr !== null) {
        const typeEffective = getEffectiveType(types, type);
        const [typeKey] = Object.keys(typeEffective);
        const typeAttrKey = typeKey === 'builtin' ? typeEffective[typeKey] : typeKey;
        const allowedAttr = typeAttrKey in typeToAllowedAttr ? typeToAllowedAttr[typeAttrKey] : null;
        const disallowedAttr = Object.fromEntries(Object.keys(attr).map((attrKey) => [attrKey, null]));
        delete disallowedAttr.nullable;
        if (allowedAttr !== null) {
            for (const attrKey of allowedAttr) {
                delete disallowedAttr[attrKey];
            }
        }
        if (Object.keys(disallowedAttr).length) {
            for (const attrKey of Object.keys(disallowedAttr)) {
                const attrValue = `${attr[attrKey]}`;
                const attrText = `${attrToText[attrKey]} ${attrValue}`;
                error(`Invalid attribute '${attrText}'`);
            }
        }
    }
}
