// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE


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
 * Helper function to validate user type dictionary
 *
 * @param {Object} types - The map of user type name to user type model
 * @returns {Array<Array>} The list of type name, member name, and error message tuples
 *
 * @ignore
 */
export function validateTypeModelTypesErrors(types) {
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
                    validateTypeModelType(errors, types, member.type, 'attr' in member ? member.attr : null, struct.name, member.name);
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
            validateTypeModelType(errors, types, typedef.type, 'attr' in typedef ? typedef.attr : null, typeName, null);

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
                    validateTypeModelType(errors, types, {'user': sectionTypeName}, null, typeName, null);
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
 * Helper function for validateTypeModelTypes to validate a type model
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
function validateTypeModelType(errors, types, type, attr, typeName, memberName) {
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
        validateTypeModelType(errors, types, arrayType, 'attr' in array ? array.attr : null, typeName, memberName);

    // Dict?
    } else if ('dict' in type) {
        const {dict} = type;

        // Check the type and its attributes
        const dictType = getEffectiveType(types, dict.type);
        validateTypeModelType(errors, types, dictType, 'attr' in dict ? dict.attr : null, typeName, memberName);

        // Check the dict key type and its attributes
        if ('keyType' in dict) {
            const dictKeyType = getEffectiveType(types, dict.keyType);
            validateTypeModelType(errors, types, dictKeyType, 'keyAttr' in dict ? dict.keyAttr : null, typeName, memberName);

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
