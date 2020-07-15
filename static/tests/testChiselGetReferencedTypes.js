import * as chisel from '../src/chisel.js';
import test from 'ava';

/* eslint-disable id-length */


test('chisel.getReferencedTypes', (t) => {
    const types = {
        'MyAction': {
            'action': {
                'name': 'MyAction',
                'path': 'MyAction_path',
                'query': 'MyAction_query',
                'input': 'MyAction_input',
                'output': 'MyAction_output',
                'errors': 'MyAction_errors'
            }
        },
        'MyAction_path': {
            'struct': {
                'name': 'MyAction_path',
                'members': [
                    {'name': 'a', 'type': {'builtin': 'string'}}
                ]
            }
        },
        'MyAction_query': {
            'struct': {
                'name': 'MyAction_query',
                'members': [
                    {'name': 'b', 'type': {'array': {'type': {'user': 'MyEnum'}}}}
                ]
            }
        },
        'MyAction_input': {
            'struct': {
                'name': 'MyAction_input',
                'members': [
                    {'name': 'c', 'type': {'dict': {'type': {'user': 'MyStruct'}}}}
                ]
            }
        },
        'MyAction_output': {
            'struct': {
                'name': 'MyAction_output',
                'members': [
                    {'name': 'd', 'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum2'}}}}
                ]
            }
        },
        'MyAction_errors': {
            'enum': {
                'name': 'MyAction_errors',
                'values': [
                    {'name': 'A'}
                ]
            }
        },
        'MyEnum': {'enum': {'name': 'MyEnum'}},
        'MyEnum2': {'enum': {'name': 'MyEnum2'}},
        'MyEnumNoref': {'enum': {'name': 'MyEnumNoref'}},
        'MyStruct': {
            'struct': {
                'name': 'MyStruct',
                'members': [
                    {'name': 'a', 'type': {'user': 'MyTypedef'}},
                    {'name': 'b', 'type': {'user': 'MyStructEmpty'}}
                ]
            }
        },
        'MyStructEmpty': {'struct': {'name': 'MyStructEmpty'}},
        'MyStructNoref': {'struct': {'name': 'MyStructNoref'}},
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'user': 'MyTypedef2'}
            }
        },
        'MyTypedef2': {
            'typedef': {
                'name': 'MyTypedef2',
                'type': {'builtin': 'int'}
            }
        },
        'MyTypedefNoref': {
            'typedef': {
                'name': 'MyTypedefNoref',
                'type': {'builtin': 'int'}
            }
        }
    };

    const referencedTypes = {...types};
    delete referencedTypes.MyEnumNoref;
    delete referencedTypes.MyStructNoref;
    delete referencedTypes.MyTypedefNoref;

    t.deepEqual(chisel.getReferencedTypes(types, 'MyAction'), referencedTypes);
});


test('chisel.getReferencedTypes, empty action', (t) => {
    const types = {
        'MyAction': {
            'action': {
                'name': 'MyAction'
            }
        },
        'MyTypedefNoref': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'}
            }
        }
    };

    const referencedTypes = {...types};
    delete referencedTypes.MyTypedefNoref;

    t.deepEqual(chisel.getReferencedTypes(types, 'MyAction'), referencedTypes);
});

test('chisel.getReferencedTypes, circular', (t) => {
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
                    {'name': 'a', 'type': {'user': 'MyStruct'}}
                ]
            }
        }
    };
    t.deepEqual(chisel.getReferencedTypes(types, 'MyStruct'), types);
});
