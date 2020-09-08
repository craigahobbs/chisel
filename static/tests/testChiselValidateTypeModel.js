import * as chisel from '../src/chisel.js';
import test from 'ava';

/* eslint-disable id-length */


test('chisel.getTypeModel', (t) => {
    const types = chisel.getTypeModel();
    const types2 = chisel.getTypeModel();
    t.deepEqual(types, types2);
    t.is(types, types2);
});


test('chisel.validateTypeModel', (t) => {
    const types = chisel.getTypeModel();
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, type validation error', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {}
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Required member 'types.MyStruct.struct.name' missing");
});


test('chisel.validateTypeModel, inconsistent struct type name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct2'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Inconsistent type name 'MyStruct2' for 'MyStruct'");
});


test('chisel.validateTypeModel, unknown struct member type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'user': 'UnknownType'}}
                    ]
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown type 'UnknownType' from 'MyStruct' member 'a'");
});


test('chisel.validateTypeModel, duplicate struct member name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'string'}},
                        {'name': 'b', 'type': {'builtin': 'int'}},
                        {'name': 'a', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Redefinition of 'MyStruct' member 'a'");
});


test('chisel.validateTypeModel, empty enum', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum'
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, inconsistent enum type name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum2'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Inconsistent type name 'MyEnum2' for 'MyEnum'");
});


test('chisel.validateTypeModel, duplicate enum value name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyEnum': {
                'enum': {
                    'name': 'MyEnum',
                    'values': [
                        {'name': 'A'},
                        {'name': 'B'},
                        {'name': 'A'}
                    ]
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Redefinition of 'MyEnum' value 'A'");
});


test('chisel.validateTypeModel, array', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}}}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, array attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}, 'attr': {'gt': 0}}}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, array attributes error', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'builtin': 'int'}, 'attr': {'lenGT': 0}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid attribute 'len > 0' from 'MyTypedef'");
});


test('chisel.validateTypeModel, unknown array type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'array': {'type': {'user': 'Unknown'}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown type 'Unknown' from 'MyTypedef'");
});


test('chisel.validateTypeModel, dict', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}}}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, dict key type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'MyEnum'}}}
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
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, dict attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'attr': {'gt': 0}}}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, dict key attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'lenGT': 0}}}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, dict invalid attribute', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'attr': {'lenGT': 0}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid attribute 'len > 0' from 'MyTypedef'");
});


test('chisel.validateTypeModel, dict invalid key attribute', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'builtin': 'string'}, 'keyAttr': {'gt': 0}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid attribute '> 0' from 'MyTypedef'");
});


test('chisel.validateTypeModel, unknown dict type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'user': 'Unknown'}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown type 'Unknown' from 'MyTypedef'");
});


test('chisel.validateTypeModel, unknown dict key type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'dict': {'type': {'builtin': 'int'}, 'keyType': {'user': 'Unknown'}}}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `\
Unknown type 'Unknown' from 'MyTypedef'
Invalid dictionary key type from 'MyTypedef'`);
});


test('chisel.validateTypeModel, invalid user type attribute', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyStruct'},
                    'attr': {'lt': 0}
                }
            },
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid attribute '< 0' from 'MyTypedef'");
});


test('chisel.validateTypeModel, nullable user type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyStruct'},
                    'attr': {'nullable': true}
                }
            },
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
    };
    t.deepEqual(chisel.validateTypeModel(types), types);
});


test('chisel.validateTypeModel, typedef attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyTypedef2'},
                    'attr': {'gt': 0}
                }
            },
            'MyTypedef2': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'builtin': 'int'}
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, inconsistent typedef type name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'builtin': 'int'}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Inconsistent type name 'MyTypedef2' for 'MyTypedef'");
});


test('chisel.validateTypeModel, unknown typedef type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyTypedef': {
                'typedef': {
                    'name': 'MyTypedef',
                    'type': {'user': 'MyTypedef2'}
                }
            },
            'MyTypedef2': {
                'typedef': {
                    'name': 'MyTypedef2',
                    'type': {'user': 'MyTypedef3'}
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown type 'MyTypedef3' from 'MyTypedef2'");
});


test('chisel.validateTypeModel, action empty struct', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction_query'
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query'
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, inconsistent action type name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction2'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Inconsistent type name 'MyAction2' for 'MyAction'");
});


test('chisel.validateTypeModel, action unknown type', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'Unknown'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown type 'Unknown' from 'MyAction'");
});


test('chisel.validateTypeModel, action action', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction2'
                }
            },
            'MyAction2': {
                'action': {
                    'name': 'MyAction2'
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid reference to action 'MyAction2' from 'MyAction'");
});


test('chisel.validateTypeModel, duplicate action member name', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction_query',
                    'input': 'MyAction_input'
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'int'}}
                    ]
                }
            },
            'MyAction_input': {
                'struct': {
                    'name': 'MyAction_input',
                    'members': [
                        {'name': 'b', 'type': {'builtin': 'int'}},
                        {'name': 'c', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `\
Redefinition of 'MyAction_query' member 'c'
Redefinition of 'MyAction_input' member 'c'`);
});


test('chisel.validateTypeModel, member attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'gt': 0, 'lte': 10}}
                    ]
                }
            }
        }
    };
    t.deepEqual(types, chisel.validateTypeModel(types));
});


test('chisel.validateTypeModel, invalid member attributes', (t) => {
    const types = {
        'title': 'Title',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}, 'attr': {'gt': 0, 'lte': 10, 'lenGT': 0, 'lenLTE': 10}}
                    ]
                }
            }
        }
    };
    let errorMessage = null;
    try {
        chisel.validateTypeModel(types);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `\
Invalid attribute 'len <= 10' from 'MyStruct' member 'a'
Invalid attribute 'len > 0' from 'MyStruct' member 'a'`);
});
