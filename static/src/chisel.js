// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/** The non-breaking space character. */
export const nbsp = String.fromCharCode(160);


/**
 * Render a document element hierarchy model
 *
 * @param {Element} parent - The parent element to render within
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 * @param {boolean} [clear=true] - If true, empty parent before rendering
 */
export function render(parent, elems = null, clear = true) {
    if (clear) {
        parent.innerHTML = '';
    }
    appendElements(parent, elems);
}


/**
 * Helper function to create an Element object and append it to the given parent Element object
 *
 * @param {Element} parent - The parent document element
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
 * Create an Element object from a chisel.js element model object
 *
 * @param {Object} element - A chisel.js element model object
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
 * Create a chisel.js element model object
 *
 * @param {string} tag - The element tag
 * @param {Object} [attrs=null] - The element attributes
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
 * Create a chisel.js SVG element model object
 *
 * @param {string} tag - The element tag
 * @param {Object} [attrs=null] - The element attributes
 * @param {(null|Object|Array)} [elems=null] - The element heirarchy model.
 *     An element hierarchy model is either null, a chisel.js element object, or an array of any of these.
 * @returns {Object}
 */
export function svg(tag, attrs, elems) {
    return elem(tag, attrs, elems, 'http://www.w3.org/2000/svg');
}


/**
 * Create a chilel.js text model object
 *
 * @param {string} str - The element text
 * @returns {Object}
 */
export function text(str) {
    return {'text': str};
}


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
 */
function encodeParamsHelper(obj, memberFqn = null, keyValues = []) {
    const objType = typeof obj;
    if (objType === 'boolean' || objType === 'number') {
        keyValues.push(memberFqn !== null ? `${memberFqn}=${obj}` : `${obj}`);
    } else if (objType === 'string') {
        const objEncoded = encodeURIComponent(obj);
        keyValues.push(memberFqn !== null ? `${memberFqn}=${objEncoded}` : `${objEncoded}`);
    } else if (obj instanceof Date) {
        const objEncoded = encodeURIComponent(obj.toISOString());
        keyValues.push(memberFqn !== null ? `${memberFqn}=${objEncoded}` : `${objEncoded}`);
    } else if (Array.isArray(obj)) {
        if (obj.length === 0) {
            keyValues.push(memberFqn !== null ? `${memberFqn}=` : '');
        } else {
            for (let ix = 0; ix < obj.length; ix++) {
                encodeParamsHelper(obj[ix], memberFqn !== null ? `${memberFqn}.${ix}` : `${ix}`, keyValues);
            }
        }
    } else if (obj !== null && typeof obj === 'object') {
        const keys = Object.keys(obj).sort();
        if (keys.length === 0) {
            keyValues.push(memberFqn !== null ? `${memberFqn}=` : '');
        } else {
            for (let ixKey = 0; ixKey < keys.length; ixKey++) {
                const key = keys[ixKey];
                const keyEncoded = encodeParamsHelper(key);
                encodeParamsHelper(obj[key], memberFqn !== null ? `${memberFqn}.${keyEncoded}` : `${keyEncoded}`, keyValues);
            }
        }
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
        (keyValue) => {
            const [keyFqn, valueEncoded = null] = keyValue.split('=');
            if (valueEncoded === null) {
                throw new Error(`Invalid key/value pair '${keyValue.slice(0, 100)}'`);
            }
            const value = decodeURIComponent(valueEncoded);

            // Find/create the object on which to set the value
            let parent = result;
            let keyParent = 0;
            const keys = keyFqn.split('.');
            for (let ixKey = 0; ixKey < keys.length; ixKey++) {
                let key = decodeURIComponent(keys[ixKey]);
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
    return validateTypeHelper(types, {'user': typeName}, value, memberFqn);
}


/**
 * Type-validate a value using a type model
 *
 * @param {Object} types - The map of user type name to user type model
 * @param {Object} type - The type object model
 * @param {Object} value - The value object to validate
 * @param {string} memberFqn - The fully-qualified member name
 * @returns {Object} The validated, transformed value object
 * @throws {Error} Validation error string
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
                const isDate = value.match(/^\d{4}-\d{2}-\d{2}$/) !== null;
                const isDatetime = value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})$/) !== null;
                if (!(isDate || isDatetime)) {
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

        // object?
        } else if (builtin === 'object') {
            // null?
            if (value === null) {
                throwMemberError(type, value, memberFqn);
            }
        }

    // array?
    } else if ('array' in type) {
        // Valid value type?
        const {array} = type;
        const arrayType = array.type;
        if (value === '') {
            valueNew = [];
        } else if (!Array.isArray(value)) {
            throwMemberError(type, value, memberFqn);
        }

        // Validate the list contents
        const valueCopy = [];
        for (let ixArrayValue = 0; ixArrayValue < valueNew.length; ixArrayValue++) {
            const memberFqnValue = memberFqn !== null ? `${memberFqn}.${ixArrayValue}` : `${ixArrayValue}`;
            const arrayValue = validateTypeHelper(types, arrayType, valueNew[ixArrayValue], memberFqnValue);
            if ('attr' in array) {
                validateAttr(arrayType, array.attr, arrayValue, memberFqnValue);
            }
            valueCopy.push(arrayValue);
        }

        // Return the validated, transformed copy
        valueNew = valueCopy;

    // dict?
    } else if ('dict' in type) {
        // Valid value type?
        const {dict} = type;
        if (value === '') {
            valueNew = {};
        } else if (value.constructor !== Object) {
            throwMemberError(type, value, memberFqn);
        }

        // Validate the dict key/value pairs
        const valueCopy = {};
        const dictKeyType = 'key_type' in dict ? dict.key_type : {'builtin': 'string'};
        Object.keys(valueNew).forEach((dictKey) => {
            const memberFqnKey = memberFqn !== null ? `${memberFqn}.${dictKey}` : `${dictKey}`;

            // Validate the key
            validateTypeHelper(types, dictKeyType, dictKey, memberFqn);
            if ('key_attr' in dict) {
                validateAttr(dictKeyType, dict.key_attr, dictKey, memberFqn);
            }

            // Validate the value
            const dictValue = validateTypeHelper(types, dict.type, valueNew[dictKey], memberFqnKey);
            if ('attr' in dict) {
                validateAttr(dict.type, dict.attr, dictValue, memberFqnKey);
            }

            // Copy the key/value
            valueCopy[dictKey] = dictValue;
        });

        // Return the validated, transformed copy
        valueNew = valueCopy;

    // User type?
    } else if ('user' in type) {
        const userType = types[type.user];

        // typedef?
        if ('typedef' in userType) {
            const {typedef} = userType;

            // Validate the value
            valueNew = validateTypeHelper(types, typedef.type, value, memberFqn);
            if ('attr' in typedef) {
                validateAttr(type, typedef.attr, valueNew, memberFqn);
            }

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
            const valueCopy = {};
            if ('members' in struct) {
                for (let ixMember = 0; ixMember < struct.members.length; ixMember++) {
                    const member = struct.members[ixMember];
                    const memberName = member.name;
                    const memberFqnMember = memberFqn !== null ? `${memberFqn}.${memberName}` : `${memberName}`;
                    const memberOptional = 'optional' in member ? member.optional : false;
                    const memberNullable = 'nullable' in member ? member.nullable : false;

                    // Missing non-optional member?
                    if (!(memberName in value)) {
                        if (!memberOptional && !isUnion) {
                            throw new Error(`Required member '${memberFqnMember}' missing`);
                        }
                    } else {
                        // Validate the member value
                        let memberValue = valueNew[memberName];
                        if (!(memberNullable && memberValue === null)) {
                            memberValue = validateTypeHelper(types, member.type, memberValue, memberFqnMember);
                            if ('attr' in member) {
                                validateAttr(member.type, member.attr, memberValue, memberFqnMember);
                            }
                        }

                        // Copy the validated member
                        valueCopy[memberName] = memberValue;
                    }
                }
            }

            // Any unknown members?
            if (Object.keys(valueCopy).length !== Object.keys(valueNew).length) {
                let unknownKey;
                if ('members' in struct) {
                    const memberSet = new Set(struct.members.map((member) => member.name));
                    [unknownKey] = Object.keys(valueNew).filter((key) => !memberSet.has(key));
                } else {
                    [unknownKey] = Object.keys(valueNew);
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
 */
function throwMemberError(type, value, memberFqn, attr = null) {
    const memberPart = memberFqn !== null ? ` for member '${memberFqn}'` : '';
    const typeName = 'builtin' in type ? type.builtin : ('array' in type ? 'array' : ('dict' in type ? 'dict' : type.user));
    const attrPart = attr !== null ? ` [${attr}]` : '';
    const msg = `Invalid value ${JSON.stringify(value).slice(0, 1000)} (type '${typeof value}')` +
          `${memberPart}, expected type '${typeName}'${attrPart}`;
    throw new Error(msg);
}


/**
 * Attribute-validate a value using an attribute model
 *
 * @param {Object} type - The type object model
 * @param {Object} attr - The attribute model
 * @param {Object} value - The value object to validate
 * @param {string} memberFqn - The fully-qualified member name
 * @throws {Error} Validation error string
 */
function validateAttr(type, attr, value, memberFqn) {
    const length = Array.isArray(value) || typeof value === 'string' ? value.length
        : (typeof value === 'object' ? Object.keys(value).length : null);
    const attrError = (attrKey, attrStr) => {
        const attrValue = `${attr[attrKey]}`;
        throwMemberError(type, value, memberFqn, `${attrStr} ${attrValue}`);
    };

    if ('eq' in attr && !(value === attr.eq)) {
        attrError('eq', '==');
    }
    if ('lt' in attr && !(value < attr.lt)) {
        attrError('lt', '<');
    }
    if ('lte' in attr && !(value <= attr.lte)) {
        attrError('lte', '<=');
    }
    if ('gt' in attr && !(value > attr.gt)) {
        attrError('gt', '>');
    }
    if ('gte' in attr && !(value >= attr.gte)) {
        attrError('gte', '>=');
    }
    if ('len_eq' in attr && !(length === attr.len_eq)) {
        attrError('len_eq', 'len ==');
    }
    if ('len_lt' in attr && !(length < attr.len_lt)) {
        attrError('len_lt', 'len <');
    }
    if ('len_lte' in attr && !(length <= attr.len_lte)) {
        attrError('len_lte', 'len <=');
    }
    if ('len_gt' in attr && !(length > attr.len_gt)) {
        attrError('len_gt', 'len >');
    }
    if ('len_gte' in attr && !(length >= attr.len_gte)) {
        attrError('len_gte', 'len >=');
    }
}
