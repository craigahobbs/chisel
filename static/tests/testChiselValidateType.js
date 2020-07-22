import * as chisel from '../src/chisel.js';
import test from 'ava';

/* eslint-disable id-length */


test('chisel.validateType', (t) => {
    t.deepEqual(
        chisel.validateType({'MyType': {'struct': {'name': 'MyType'}}}, 'MyType', {}),
        {}
    );
});

function validateType(type, obj) {
    const types = {
        'MyTypedef': {
            'typedef': {
                'type': type
            }
        }
    };
    return chisel.validateType(types, 'MyTypedef', obj);
}

test('chisel.validateType, string', (t) => {
    const obj = 'abc';
    t.is(validateType({'builtin': 'string'}, obj), obj);
});

test('chisel.validateType, string error', (t) => {
    let errorMessage = null;
    const obj = 7;
    try {
        validateType({'builtin': 'string'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7 (type 'number'), expected type 'string'");
});

test('chisel.validateType, int', (t) => {
    const obj = 7;
    t.is(validateType({'builtin': 'int'}, obj), obj);
});

test('chisel.validateType, int float', (t) => {
    let errorMessage = null;
    const obj = 7.1;
    try {
        validateType({'builtin': 'int'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7.1 (type 'number'), expected type 'int'");
});

test('chisel.validateType, int string', (t) => {
    const obj = '7';
    t.is(validateType({'builtin': 'int'}, obj), 7);
});

test('chisel.validateType, int error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'int'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'int'");
});

test('chisel.validateType, int error bool', (t) => {
    let errorMessage = null;
    const obj = true;
    try {
        validateType({'builtin': 'int'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value true (type 'boolean'), expected type 'int'");
});

test('chisel.validateType, float', (t) => {
    const obj = 7.5;
    t.is(validateType({'builtin': 'float'}, obj), obj);
});

test('chisel.validateType, float int', (t) => {
    const obj = 7;
    t.is(validateType({'builtin': 'float'}, obj), 7.0);
});

test('chisel.validateType, float string', (t) => {
    const obj = '7.5';
    t.is(validateType({'builtin': 'float'}, obj), 7.5);
});

test('chisel.validateType, float error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'float'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'float'");
});

test('chisel.validateType, float error nan', (t) => {
    let errorMessage = null;
    const obj = 'nan';
    try {
        validateType({'builtin': 'float'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"nan\" (type 'string'), expected type 'float'");
});

test('chisel.validateType, float error inf', (t) => {
    let errorMessage = null;
    const obj = 'inf';
    try {
        validateType({'builtin': 'float'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"inf\" (type 'string'), expected type 'float'");
});

test('chisel.validateType, float error bool', (t) => {
    let errorMessage = null;
    const obj = true;
    try {
        validateType({'builtin': 'float'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value true (type 'boolean'), expected type 'float'");
});

test('chisel.validateType, bool', (t) => {
    const obj = false;
    t.is(validateType({'builtin': 'bool'}, obj), obj);
});

test('chisel.validateType, bool true', (t) => {
    const obj = 'true';
    t.is(validateType({'builtin': 'bool'}, obj), true);
});

test('chisel.validateType, bool false', (t) => {
    const obj = 'false';
    t.is(validateType({'builtin': 'bool'}, obj), false);
});

test('chisel.validateType, bool error', (t) => {
    let errorMessage = null;
    const obj = 0;
    try {
        validateType({'builtin': 'bool'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 0 (type 'number'), expected type 'bool'");
});

test('chisel.validateType, bool error string', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'bool'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'bool'");
});

test('chisel.validateType, date', (t) => {
    const obj = new Date(2020, 5, 26);
    t.deepEqual(validateType({'builtin': 'date'}, obj), obj);
});

test('chisel.validateType, date datetime', (t) => {
    const obj = new Date(2020, 5, 26, 18, 8);
    t.deepEqual(validateType({'builtin': 'date'}, obj), new Date(2020, 5, 26));
});

test('chisel.validateType, date string', (t) => {
    const obj = '2020-06-26';
    t.deepEqual(validateType({'builtin': 'date'}, obj), new Date(2020, 5, 26));
});

test('chisel.validateType, date string datetime', (t) => {
    const obj = '2020-06-26T13:11:00-07:00';
    t.deepEqual(validateType({'builtin': 'date'}, obj), new Date(2020, 5, 26));
});

test('chisel.validateType, date string error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'date'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'date'");
});

test('chisel.validateType, date error', (t) => {
    let errorMessage = null;
    const obj = 0;
    try {
        validateType({'builtin': 'date'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 0 (type 'number'), expected type 'date'");
});

test('chisel.validateType, date error excluded', (t) => {
    let errorMessage = null;
    const obj = 'December 17, 1995 03:24:00';
    try {
        validateType({'builtin': 'date'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"December 17, 1995 03:24:00\" (type 'string'), expected type 'date'");
});

test('chisel.validateType, datetime', (t) => {
    const obj = new Date(2020, 5, 26, 18, 8);
    t.deepEqual(validateType({'builtin': 'datetime'}, obj), obj);
});

test('chisel.validateType, datetime date', (t) => {
    const obj = new Date(2020, 5, 26);
    t.deepEqual(validateType({'builtin': 'datetime'}, obj), obj);
});

test('chisel.validateType, datetime string', (t) => {
    const obj = '2020-06-26T13:11:00-07:00';
    t.deepEqual(validateType({'builtin': 'datetime'}, obj), new Date(2020, 5, 26, 20, 11));
});

test('chisel.validateType, datetime string date', (t) => {
    const obj = '2020-06-26';
    t.deepEqual(validateType({'builtin': 'datetime'}, obj), new Date(2020, 5, 26));
});

test('chisel.validateType, datetime string error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'datetime'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'datetime'");
});

test('chisel.validateType, datetime error', (t) => {
    let errorMessage = null;
    const obj = 0;
    try {
        validateType({'builtin': 'datetime'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 0 (type 'number'), expected type 'datetime'");
});

test('chisel.validateType, datetime error excluded', (t) => {
    let errorMessage = null;
    const obj = 'December 17, 1995 03:24:00';
    try {
        validateType({'builtin': 'datetime'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"December 17, 1995 03:24:00\" (type 'string'), expected type 'datetime'");
});

test('chisel.validateType, uuid', (t) => {
    const obj = 'AED91C7B-DCFD-49B3-A483-DBC9EA2031A3';
    t.deepEqual(validateType({'builtin': 'uuid'}, obj), obj);
});

test('chisel.validateType, uuid lowercase', (t) => {
    const obj = 'aed91c7b-dcfd-49b3-a483-dbc9ea2031a3';
    t.deepEqual(validateType({'builtin': 'uuid'}, obj), obj);
});

test('chisel.validateType, uuid error', (t) => {
    let errorMessage = null;
    const obj = 0;
    try {
        validateType({'builtin': 'uuid'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 0 (type 'number'), expected type 'uuid'");
});

test('chisel.validateType, uuid error string', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'builtin': 'uuid'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'uuid'");
});

test('chisel.validateType, object', (t) => {
    const obj = {};
    t.deepEqual(validateType({'builtin': 'object'}, obj), obj);
});

test('chisel.validateType, object string', (t) => {
    const obj = 'abc';
    t.deepEqual(validateType({'builtin': 'object'}, obj), obj);
});

test('chisel.validateType, object int', (t) => {
    const obj = 7;
    t.deepEqual(validateType({'builtin': 'object'}, obj), obj);
});

test('chisel.validateType, object bool', (t) => {
    const obj = true;
    t.deepEqual(validateType({'builtin': 'object'}, obj), obj);
});

test('chisel.validateType, array', (t) => {
    const obj = [1, 2, 3];
    t.deepEqual(validateType({'array': {'type': {'builtin': 'int'}}}, obj), obj);
});

test('chisel.validateType, array nullable', (t) => {
    const obj = [1, null, 3];
    t.deepEqual(validateType({'array': {'type': {'builtin': 'int'}, 'attr': {'nullable': true}}}, obj), obj);

    let errorMessage = null;
    try {
        validateType({'array': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member '1', expected type 'int'");
});

test('chisel.validateType, array empty string', (t) => {
    const obj = '';
    t.deepEqual(validateType({'array': {'type': {'builtin': 'int'}}}, obj), []);
});

test('chisel.validateType, array attributes', (t) => {
    const obj = [1, 2, 3];
    t.deepEqual(validateType({'array': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj), obj);
});

test('chisel.validateType, array error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'array': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'array'");
});

test('chisel.validateType, array error value', (t) => {
    let errorMessage = null;
    const obj = [1, 'abc', 3];
    try {
        validateType({'array': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member '1', expected type 'int'");
});

test('chisel.validateType, array error value nested', (t) => {
    let errorMessage = null;
    const obj = [[1, 2], [1, 'abc', 3]];
    try {
        validateType({'array': {'type': {'array': {'type': {'builtin': 'int'}}}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member '1.1', expected type 'int'");
});

test('chisel.validateType, array attribute error', (t) => {
    let errorMessage = null;
    const obj = [1, 2, 5];
    try {
        validateType({'array': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 5 (type 'number') for member '2', expected type 'int' [< 5]");
});

test('chisel.validateType, dict', (t) => {
    const obj = {'a': 1, 'b': 2, 'c': 3};
    t.deepEqual(validateType({'dict': {'type': {'builtin': 'int'}}}, obj), obj);
});

test('chisel.validateType, dict nullable', (t) => {
    const obj = {'a': 1, 'b': null, 'c': 3};
    t.deepEqual(validateType({'dict': {'type': {'builtin': 'int'}, 'attr': {'nullable': true}}}, obj), obj);

    let errorMessage = null;
    try {
        validateType({'dict': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member 'b', expected type 'int'");
});

test('chisel.validateType, dict key nullable', (t) => {
    const obj = new Map();
    obj.set('a', 1);
    obj.set(null, 2);
    obj.set('c', 3);
    const obj2 = validateType({'dict': {'type': {'builtin': 'int'}, 'keyAttr': {'nullable': true}}}, obj);
    t.is(Array.from(obj2.keys()).length, 3);
    t.is(obj2.get('a'), 1);
    t.is(obj2.get(null), 2);
    t.is(obj2.get('c'), 3);

    let errorMessage = null;
    try {
        validateType({'dict': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'string'");
});

test('chisel.validateType, dict empty string', (t) => {
    const obj = '';
    t.deepEqual(validateType({'dict': {'type': {'builtin': 'int'}}}, obj), {});
});

test('chisel.validateType, dict attributes', (t) => {
    const obj = {'a': 1, 'b': 2, 'c': 3};
    t.deepEqual(validateType({'dict': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj), obj);
});

test('chisel.validateType, dict error', (t) => {
    let errorMessage = null;
    const obj = 'abc';
    try {
        validateType({'dict': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'dict'");
});

test('chisel.validateType, dict error value', (t) => {
    let errorMessage = null;
    const obj = {'a': 1, 'b': 'abc', 'c': 3};
    try {
        validateType({'dict': {'type': {'builtin': 'int'}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member 'b', expected type 'int'");
});

test('chisel.validateType, dict error value nested', (t) => {
    let errorMessage = null;
    const obj = [{'a': 1}, {'a': 1, 'b': 'abc', 'c': 3}];
    try {
        validateType({'array': {'type': {'dict': {'type': {'builtin': 'int'}}}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member '1.b', expected type 'int'");
});

test('chisel.validateType, dict attribute error', (t) => {
    let errorMessage = null;
    const obj = {'a': 1, 'b': 2, 'c': 5};
    try {
        validateType({'dict': {'type': {'builtin': 'int'}, 'attr': {'lt': 5}}}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 5 (type 'number') for member 'c', expected type 'int' [< 5]");
});

test('chisel.validateType, dict key type', (t) => {
    const types = {
        'MyEnum': {
            'enum': {
                'name': 'MyEnum',
                'values': [
                    {'name': 'A'},
                    {'name': 'B'}
                ]
            }
        },
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum'}}}
            }
        }
    };
    let errorMessage = null;

    let obj = {'A': 1, 'B': 2};
    t.deepEqual(chisel.validateType(types, 'MyTypedef', obj), obj);

    obj = {'A': 1, 'C': 2};
    try {
        chisel.validateType(types, 'MyTypedef', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"C\" (type 'string'), expected type 'MyEnum'");
});

test('chisel.validateType, dict key attr', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'lenLT': 10}}}
            }
        }
    };
    let errorMessage = null;

    let obj = {'abc': 1, 'abcdefghi': 2};
    t.deepEqual(chisel.validateType(types, 'MyTypedef', obj), obj);

    obj = {'abc': 1, 'abcdefghij': 2};
    try {
        chisel.validateType(types, 'MyTypedef', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abcdefghij\" (type 'string'), expected type 'string' [len < 10]");
});

test('chisel.validateType, enum', (t) => {
    const types = {
        'MyEnum': {
            'enum': {
                'name': 'MyEnum',
                'values': [
                    {'name': 'a'},
                    {'name': 'b'}
                ]
            }
        }
    };
    let errorMessage = null;

    let obj = 'a';
    t.is(chisel.validateType(types, 'MyEnum', obj), obj);

    obj = 'c';
    try {
        chisel.validateType(types, 'MyEnum', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"c\" (type 'string'), expected type 'MyEnum'");
});

test('chisel.validateType, typedef', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'gte': 5}
            }
        }
    };
    let errorMessage = null;

    let obj = 5;
    t.is(chisel.validateType(types, 'MyTypedef', obj), obj);

    obj = 4;
    try {
        chisel.validateType(types, 'MyTypedef', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 4 (type 'number'), expected type 'MyTypedef' [>= 5]");
});

test('chisel.validateType, typedef no attr', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'}
            }
        }
    };
    const obj = 5;
    t.is(chisel.validateType(types, 'MyTypedef', obj), obj);
});

test('chisel.validateType, typedef type error', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'}
            }
        }
    };
    let errorMessage = null;

    const obj = 'abc';
    try {
        chisel.validateType(types, 'MyTypedef', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'int'");
});

test('chisel.validateType, typedef attr eq', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'eq': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 5);
    try {
        chisel.validateType(types, 'MyTypedef', 7);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7 (type 'number'), expected type 'MyTypedef' [== 5]");
});

test('chisel.validateType, typedef attr nullable', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'nullable': true}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 5);
    chisel.validateType(types, 'MyTypedef', null);
    try {
        chisel.validateType(types, 'MyTypedef', 'abc');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'int'");
});

test('chisel.validateType, typedef attr lt', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'lt': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 3);
    try {
        chisel.validateType(types, 'MyTypedef', 5);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 5 (type 'number'), expected type 'MyTypedef' [< 5]");
    try {
        chisel.validateType(types, 'MyTypedef', 7);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7 (type 'number'), expected type 'MyTypedef' [< 5]");
});

test('chisel.validateType, typedef attr lte', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'lte': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 5);
    try {
        chisel.validateType(types, 'MyTypedef', 7);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7 (type 'number'), expected type 'MyTypedef' [<= 5]");
});

test('chisel.validateType, typedef attr gt', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'gt': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 7);
    try {
        chisel.validateType(types, 'MyTypedef', 3);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 3 (type 'number'), expected type 'MyTypedef' [> 5]");
    try {
        chisel.validateType(types, 'MyTypedef', 5);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 5 (type 'number'), expected type 'MyTypedef' [> 5]");
});

test('chisel.validateType, typedef attr gte', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'gte': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', 5);
    try {
        chisel.validateType(types, 'MyTypedef', 3);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 3 (type 'number'), expected type 'MyTypedef' [>= 5]");
});

test('chisel.validateType, typedef attr lenEq', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'lenEq': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5]);
    try {
        chisel.validateType(types, 'MyTypedef', [1, 2, 3]);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value [1,2,3] (type 'object'), expected type 'MyTypedef' [len == 5]");
});

test('chisel.validateType, typedef attr lenEq object', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'dict': {'type': {'builtin': 'int'}}},
                'attr': {'lenEq': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5});
    try {
        chisel.validateType(types, 'MyTypedef', {'a': 1, 'b': 2, 'c': 3});
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value {\"a\":1,\"b\":2,\"c\":3} (type 'object'), expected type 'MyTypedef' [len == 5]");
});

test('chisel.validateType, typedef attr lenLT', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'lenLT': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', [1, 2, 3]);
    try {
        chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5]);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value [1,2,3,4,5] (type 'object'), expected type 'MyTypedef' [len < 5]");
});

test('chisel.validateType, typedef attr lenLTE', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'lenLTE': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5]);
    try {
        chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5, 6, 7]);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value [1,2,3,4,5,6,7] (type 'object'), expected type 'MyTypedef' [len <= 5]");
});

test('chisel.validateType, typedef attr lenGT', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'lenGT': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5, 6, 7]);
    try {
        chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5]);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value [1,2,3,4,5] (type 'object'), expected type 'MyTypedef' [len > 5]");
});

test('chisel.validateType, typedef attr lenGTE', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'lenGTE': 5}
            }
        }
    };
    let errorMessage = null;
    chisel.validateType(types, 'MyTypedef', [1, 2, 3, 4, 5]);
    try {
        chisel.validateType(types, 'MyTypedef', [1, 2, 3]);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value [1,2,3] (type 'object'), expected type 'MyTypedef' [len >= 5]");
});

test('chisel.validateType, struct', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'string'}},
                    {'name': 'b', 'type': {'builtin': 'int'}},
                    {'name': 'c', 'type': {'builtin': 'float'}},
                    {'name': 'd', 'type': {'builtin': 'bool'}},
                    {'name': 'e', 'type': {'builtin': 'date'}},
                    {'name': 'f', 'type': {'builtin': 'datetime'}},
                    {'name': 'g', 'type': {'builtin': 'uuid'}},
                    {'name': 'h', 'type': {'builtin': 'object'}},
                    {'name': 'i', 'type': {'user': 'MyStruct2'}},
                    {'name': 'j', 'type': {'user': 'MyEnum'}},
                    {'name': 'k', 'type': {'user': 'MyTypedef'}}
                ]
            }
        },
        'MyStruct2': {
            'struct': {
                'name': 'MyStruct2',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'string'}},
                    {'name': 'b', 'type': {'builtin': 'int'}}
                ]
            }
        },
        'MyEnum': {
            'enum': {
                'name': 'MyEnum',
                'values': [
                    {'name': 'A'},
                    {'name': 'B'}
                ]
            }
        },
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'},
                'attr': {'gt': 0}
            }
        }
    };

    let obj = {
        'a': 'abc',
        'b': 7,
        'c': 7.1,
        'd': true,
        'e': new Date('2020-06-13'),
        'f': new Date('2020-06-13T13:25:00-07:00'),
        'g': 'a3597528-a253-4c76-bc2d-8da0026cc838',
        'h': {'foo': 'bar'},
        'i': {
            'a': 'abc',
            'b': 7
        },
        'j': 'A',
        'k': 1
    };
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    const objTransform = obj;
    obj = {
        'a': 'abc',
        'b': '7',
        'c': '7.1',
        'd': 'true',
        'e': '2020-06-13',
        'f': '2020-06-13T13:25:00-07:00',
        'g': 'a3597528-a253-4c76-bc2d-8da0026cc838',
        'h': {'foo': 'bar'},
        'i': {
            'a': 'abc',
            'b': '7'
        },
        'j': 'A',
        'k': '1'
    };
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), objTransform);
});

test('chisel.validateType, struct map', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'user': 'MyStruct2'}}
                ]
            }
        },
        'MyStruct2': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'c', 'type': {'builtin': 'string'}}
                ]
            }
        }
    };
    const obj = new Map();
    const objB = new Map();
    obj.set('a', 5);
    obj.set('b', objB);
    objB.set('c', 'abc');
    const obj2 = chisel.validateType(types, 'MyStruct', obj);
    t.is(obj2 instanceof Map, true);
    t.is(Array.from(obj2.keys()).length, 2);
    t.is(obj2.get('a'), 5);
    t.is(Array.from(obj2.get('b').keys()).length, 1);
    t.is(obj2.get('b') instanceof Map, true);
    t.is(obj2.get('b').get('c'), 'abc');
});

test('chisel.validateType, struct empty string', (t) => {
    const types = {
        'Empty': {
            'struct': {
                'name': 'Empty'
            }
        }
    };
    const obj = '';
    t.deepEqual(chisel.validateType(types, 'Empty', obj), {});
});

test('chisel.validateType, struct string error', (t) => {
    const types = {
        'Empty': {
            'struct': {
                'name': 'Empty'
            }
        }
    };
    let errorMessage = null;
    const obj = 'abc';
    try {
        chisel.validateType(types, 'Empty', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'Empty'");
});

test('chisel.validateType, struct union', (t) => {
    const types = {
        'MyUnion': {
            'struct': {
                'name': 'MyUnion',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'builtin': 'string'}}
                ],
                'union': true
            }
        }
    };
    let errorMessage = null;

    let obj = {'a': 7};
    t.deepEqual(chisel.validateType(types, 'MyUnion', obj), obj);

    obj = {'b': 'abc'};
    t.deepEqual(chisel.validateType(types, 'MyUnion', obj), obj);

    obj = {};
    try {
        chisel.validateType(types, 'MyUnion', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value {} (type 'object'), expected type 'MyUnion'");

    obj = {'c': 7};
    try {
        chisel.validateType(types, 'MyUnion', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member 'c'");
});

test('chisel.validateType, struct optional', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'builtin': 'string'}, 'optional': true},
                    {'name': 'c', 'type': {'builtin': 'float'}, 'optional': false}
                ]
            }
        }
    };
    let errorMessage = null;

    let obj = {'a': 7, 'b': 'abc', 'c': 7.1};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7, 'c': 7.1};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Required member 'c' missing");
});

test('chisel.validateType, struct nullable', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'nullable': true}},
                    {'name': 'c', 'type': {'builtin': 'string'}, 'attr': {'nullable': true}},
                    {'name': 'd', 'type': {'builtin': 'float'}, 'attr': {'nullable': false}}
                ]
            }
        }
    };
    let errorMessage = null;

    let obj = {'a': 7, 'b': 8, 'c': 'abc', 'd': 7.1};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7, 'b': null, 'c': null, 'd': 7.1};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7, 'b': null, 'c': 'null', 'd': 7.1};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7, 'b': 'null', 'c': null, 'd': 7.1};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"null\" (type 'string') for member 'b', expected type 'int'");

    obj = {'a': null, 'b': null, 'c': null, 'd': 7.1};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member 'a', expected type 'int'");

    obj = {'a': 7, 'b': null, 'c': null, 'd': null};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member 'd', expected type 'float'");

    obj = {'a': 7, 'c': null, 'd': 7.1};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Required member 'b' missing");
});

test('chisel.validateType, struct nullable attr', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'nullable': true, 'lt': 5}}
                ]
            }
        }
    };
    let errorMessage = null;

    let obj = {'a': 7, 'b': 4};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);

    obj = {'a': 7, 'b': 5};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 5 (type 'number') for member 'b', expected type 'int' [< 5]");

    obj = {'a': 7, 'b': null};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);
});

test('chisel.validateType, struct member attr', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                ]
            }
        }
    };
    const obj = {'a': 4};
    t.deepEqual(chisel.validateType(types, 'MyStruct', obj), obj);
});

test('chisel.validateType, struct member attr invalid', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': 7};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value 7 (type 'number') for member 'a', expected type 'int' [< 5]");
});

test('chisel.validateType, struct error invalid value', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = 'abc';
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string'), expected type 'MyStruct'");
});

test('chisel.validateType, struct error optional null value', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}, 'optional': true}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': null};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member 'a', expected type 'int'");
});

test('chisel.validateType, struct error member validation', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': 'abc'};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member 'a', expected type 'int'");
});

test('chisel.validateType, struct error nested member validation', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'user': 'MyStruct2'}}
                ]
            }
        },
        'MyStruct2': {
            'struct': {
                'name': 'MyStruct2',
                'members': [
                    {'name': 'b', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': {'b': 'abc'}};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value \"abc\" (type 'string') for member 'a.b', expected type 'int'");
});

test('chisel.validateType, struct error unknown member', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': 7, 'b': 8};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member 'b'");
});

test('chisel.validateType, struct error unknown member nested', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        },
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'user': 'MyStruct'}}}
            }
        }
    };
    let errorMessage = null;
    const obj = [{'a': 5}, {'a': 7, 'b': 'abc'}];
    try {
        chisel.validateType(types, 'MyTypedef', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member '1.b'");
});

test('chisel.validateType, struct error unknown member empty', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct'
            }
        }
    };
    let errorMessage = null;
    const obj = {'b': 8};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member 'b'");
});

test('chisel.validateType, struct error unknown member long', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {'a': 7};
    obj['b'.repeat(2000)] = 8;
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `Unknown member '${'b'.repeat(100)}'`);
});

test('chisel.validateType, struct error missing member', (t) => {
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}}
                ]
            }
        }
    };
    let errorMessage = null;
    const obj = {};
    try {
        chisel.validateType(types, 'MyStruct', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Required member 'a' missing");
});

test('chisel.validateType, action', (t) => {
    const types = {
        'MyAction': {
            'action': {
                'name': 'MyAction'
            }
        }
    };
    let errorMessage = null;
    const obj = {};
    try {
        chisel.validateType(types, 'MyAction', obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value {} (type 'object'), expected type 'MyAction'");
});

test('chisel.validateType, invalid model', (t) => {
    const types = {
        'MyBadBuiltin': {
            'typedef': {
                'name': 'MyBadBuiltin',
                'type': {'builtin': 'foobar'}
            }
        },
        'MyBadType': {
            'typedef': {
                'name': 'MyBadType',
                'type': {'bad_type_key': 'foobar'}
            }
        },
        'MyBadUser': {
            'typedef': {
                'name': 'MyBadUser',
                'type': {'user': 'MyBadUserKey'}
            }
        },
        'MyBadUserKey': {
            'bad_user_key': {}
        }
    };
    t.is(chisel.validateType(types, 'MyBadBuiltin', 'abc'), 'abc');
    t.is(chisel.validateType(types, 'MyBadType', 'abc'), 'abc');
    t.is(chisel.validateType(types, 'MyBadUser', 'abc'), 'abc');
});
