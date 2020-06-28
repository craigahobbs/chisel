import * as chisel from '../src/chisel.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


//
// chisel constant tests
//

test('chisel.nbsp', (t) => {
    t.is(chisel.nbsp, String.fromCharCode(160));
});


//
// chisel.render tests
//

test('chisel.render', (t) => {
    document.body.innerHTML = '';
    chisel.render(document.body, {'tag': 'div'});
    t.is(document.body.innerHTML, '<div></div>');
    chisel.render(document.body, [{'tag': 'div'}, {'tag': 'div', 'attrs': {'id': 'Id'}}]);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div>');
    chisel.render(document.body, {'tag': 'div'}, false);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div><div></div>');
    chisel.render(document.body, null);
    t.is(document.body.innerHTML, '');
    chisel.render(document.body);
    t.is(document.body.innerHTML, '');
});

test('chisel.render, basic', (t) => {
    chisel.render(document.body, [
        {'tag': 'h1', 'elems': {'text': 'Hello, World!'}},
        [
            {'tag': 'p', 'elems': [{'text': 'Word'}]},
            {'tag': 'p', 'elems': [{'text': 'Two'}, {'text': 'Words'}]},
            {'tag': 'p', 'elems': []},
            {'tag': 'p', 'elems': null}
        ],
        {'tag': 'div', 'attrs': {'id': 'Id', 'class': null}}
    ]);
    t.is(
        document.body.innerHTML,
        '<h1>Hello, World!</h1><p>Word</p><p>TwoWords</p><p></p><p></p><div id="Id"></div>'
    );
});

test('chisel.render, svg', (t) => {
    chisel.render(document.body, [
        {'tag': 'svg', 'ns': 'http://www.w3.org/2000/svg', 'attrs': {'width': 600, 'height': 400}, 'elems': [
            {
                'tag': 'rect', 'ns': 'http://www.w3.org/2000/svg',
                'attrs': {'x': 10, 'y': 10, 'width': 20, 'height': 20, 'style': 'fill: #ff0000;'}
            },
            {
                'tag': 'rect', 'ns': 'http://www.w3.org/2000/svg',
                'attrs': {'x': 10, 'y': 10, 'width': 20, 'height': 20, 'style': 'fill: #00ff00;'}
            }
        ]}
    ]);
    t.is(
        document.body.innerHTML,
        '<svg width="600" height="400">' +
            '<rect x="10" y="10" width="20" height="20" style="fill: #ff0000;"></rect>' +
            '<rect x="10" y="10" width="20" height="20" style="fill: #00ff00;"></rect>' +
            '</svg>'
    );
});

test('chisel.render, element callback', (t) => {
    let callbackCount = 0;
    const callback = (element) => {
        t.true(typeof element !== 'undefined');
        callbackCount += 1;
    };
    chisel.render(document.body, [
        {'tag': 'div', 'attrs': {'_callback': callback}},
        {'tag': 'div', 'attrs': {'_callback': null}}
    ]);
    t.is(
        document.body.innerHTML,
        '<div></div><div></div>'
    );
    t.is(callbackCount, 1);
});


//
// chisel.elem tests
//

test('chisel.elem', (t) => {
    t.deepEqual(
        chisel.elem('p'),
        {'tag': 'p'}
    );
});

test('chisel.elem, attrs', (t) => {
    t.deepEqual(
        chisel.elem('p', {'id': 'Id'}),
        {'tag': 'p', 'attrs': {'id': 'Id'}}
    );
});

test('chisel.elem, elems', (t) => {
    t.deepEqual(
        chisel.elem('p', null, chisel.elem('div')),
        {'tag': 'p', 'elems': {'tag': 'div'}}
    );
});

test('chisel.elem, attrs and elems', (t) => {
    t.deepEqual(
        chisel.elem('p', {'id': 'Id'}, [chisel.elem('div')]),
        {'tag': 'p', 'attrs': {'id': 'Id'}, 'elems': [{'tag': 'div'}]}
    );
});

test('chisel.elem, namespace', (t) => {
    t.deepEqual(
        chisel.elem('svg', null, null, 'http://www.w3.org/2000/svg'),
        {'tag': 'svg', 'ns': 'http://www.w3.org/2000/svg'}
    );
});


//
// chisel.svg tests
//

test('chisel.svg', (t) => {
    t.deepEqual(
        chisel.svg('svg', {'width': 600, 'height': 400}),
        {'tag': 'svg', 'ns': 'http://www.w3.org/2000/svg', 'attrs': {'width': 600, 'height': 400}}
    );
});


//
// chisel.elem tests
//

test('chisel.text', (t) => {
    t.deepEqual(
        chisel.text('Hello'),
        {'text': 'Hello'}
    );
});


//
// chisel.href tests
//

test('chisel.href', (t) => {
    t.is(
        chisel.href(),
        'blank#'
    );
});

test('chisel.href, hash', (t) => {
    t.is(
        chisel.href({'width': 600, 'height': 400, 'id': null, 'alpha': 'abc'}),
        'blank#alpha=abc&height=400&width=600'
    );
});

test('chisel.href, empty hash', (t) => {
    t.is(
        chisel.href({}),
        'blank#'
    );
});

test('chisel.href, query', (t) => {
    t.is(
        chisel.href(null, {'width': 600, 'height': 400, 'id': null, 'alpha': 'abc'}),
        'blank?alpha=abc&height=400&width=600'
    );
});

test('chisel.href, empty query', (t) => {
    t.is(
        chisel.href(null, {}),
        'blank'
    );
});

test('chisel.href, pathname', (t) => {
    t.is(
        chisel.href(null, null, 'static'),
        'static#'
    );
});

test('chisel.href, all', (t) => {
    t.is(
        chisel.href(
            {'width': 600, 'height': 400, 'id': null, 'alpha': 'abc'},
            {'width': 600, 'height': 400, 'id': null, 'alpha': 'abc'},
            'static'
        ),
        'static?alpha=abc&height=400&width=600#alpha=abc&height=400&width=600'
    );
});


//
// chisel.encodeParams tests
//

test('chisel.encodeParams', (t) => {
    t.is(
        chisel.encodeParams({
            'foo': 17,
            'bar': 19.33,
            'bonk': 'abc',
            ' th&ud ': ' ou&ch ',
            'blue': new Date('2020-06-24'),
            'fever': null,
            'zap': [
                {'a': 5},
                {'b': 7}
            ]
        }),
        '%20th%26ud%20=%20ou%26ch%20&bar=19.33&blue=2020-06-24T00%3A00%3A00.000Z&bonk=abc&foo=17&zap.0.a=5&zap.1.b=7'
    );
});

test('chisel.encodeParams, null', (t) => {
    t.is(chisel.encodeParams(null), '');
    t.is(chisel.encodeParams({'a': null, 'b': 'abc'}), 'b=abc');
});

test('chisel.encodeParams, bool', (t) => {
    t.is(chisel.encodeParams(true), 'true');
});

test('chisel.encodeParams, number', (t) => {
    t.is(chisel.encodeParams(5.1), '5.1');
});

test('chisel.encodeParams, date', (t) => {
    t.is(chisel.encodeParams(new Date('2020-06-24')), '2020-06-24T00%3A00%3A00.000Z');
});

test('chisel.encodeParams, array', (t) => {
    t.is(chisel.encodeParams([1, 2, []]), '0=1&1=2&2=');
});

test('chisel.encodeParams, empty array', (t) => {
    t.is(chisel.encodeParams([]), '');
});

test('chisel.encodeParams, empty array/array', (t) => {
    t.is(chisel.encodeParams([[]]), '0=');
});

test('chisel.encodeParams, object', (t) => {
    t.is(chisel.encodeParams({'a': 5, 'b': 'a&b', 'c': {}}), 'a=5&b=a%26b&c=');
});

test('chisel.encodeParams, empty object', (t) => {
    t.is(chisel.encodeParams({}), '');
});

test('chisel.encodeParams, empty object/object', (t) => {
    t.is(chisel.encodeParams({'a': {}}), 'a=');
});


//
// chisel.decodeParams tests
//

test('chisel.decodeParams, default', (t) => {
    window.location.hash = '_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6';
    t.deepEqual(
        chisel.decodeParams(),
        {'a': '7', '_a': '7', 'b': {'c': '+x y + z', 'd': ['2', '-4', '6']}}
    );
});

test('chisel.decodeParams, complex dict', (t) => {
    t.deepEqual(
        chisel.decodeParams('_a=7&a=7&b.c=%2Bx%20y%20%2B%20z&b.d.0=2&b.d.1=-4&b.d.2=6'),
        {'a': '7', '_a': '7', 'b': {'c': '+x y + z', 'd': ['2', '-4', '6']}}
    );
});

test('chisel.decodeParams, array of dicts', (t) => {
    t.deepEqual(
        chisel.decodeParams('foo.0.bar=17&foo.0.thud=blue&foo.1.boo=bear'),
        {'foo': [{'bar': '17', 'thud': 'blue'}, {'boo': 'bear'}]}
    );
});

test('chisel.decodeParams, top-level array', (t) => {
    t.deepEqual(
        chisel.decodeParams('0=1&1=2&2=3'),
        ['1', '2', '3']
    );
});

test('chisel.decodeParams, empty query string', (t) => {
    t.deepEqual(
        chisel.decodeParams(''),
        {}
    );
});

test('chisel.decodeParams, empty string value', (t) => {
    t.deepEqual(
        chisel.decodeParams('b='),
        {'b': ''}
    );
});

test('chisel.decodeParams, empty string value at end', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&b='),
        {'a': '7', 'b': ''}
    );
});

test('chisel.decodeParams, empty string value at start', (t) => {
    t.deepEqual(
        chisel.decodeParams('b=&a=7'),
        {'a': '7', 'b': ''}
    );
});

test('chisel.decodeParams, empty string value in middle', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&b=&c=9'),
        {'a': '7', 'b': '', 'c': '9'}
    );
});

test('chisel.decodeParams, decode keys and values', (t) => {
    t.deepEqual(
        chisel.decodeParams('a%2eb.c=7%20+%207%20%3d%2014'),
        {'a.b': {'c': '7 + 7 = 14'}}
    );
});

test('chisel.decodeParams, decode unicode string', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=abc%EA%80%80&b.0=c&b.1=d'),
        {'a': 'abc\ua000', 'b': ['c', 'd']}
    );
});

test('chisel.decodeParams, keys and values with special characters', (t) => {
    t.deepEqual(
        chisel.decodeParams('a%26b%3Dc%2ed=a%26b%3Dc.d'),
        {'a&b=c.d': 'a&b=c.d'}
    );
});

test('chisel.decodeParams, non-initial-zero array-looking index', (t) => {
    t.deepEqual(
        chisel.decodeParams('a.1=0'),
        {'a': {'1': '0'}}
    );
});

test('chisel.decodeParams, dictionary first, then array-looking zero index', (t) => {
    t.deepEqual(
        chisel.decodeParams('a.b=0&a.0=0'),
        {'a': {'b': '0', '0': '0'}}
    );
});

test('chisel.decodeParams, empty string key', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&=b'),
        {'a': '7', '': 'b'}
    );
});

test('chisel.decodeParams, empty string key and value', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&='),
        {'a': '7', '': ''}
    );
});

test('chisel.decodeParams, empty string key and value with space', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7& = '),
        {'a': '7', ' ': ' '}
    );
});

test('chisel.decodeParams, empty string key with no equal', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&'),
        {'a': '7'}
    );
});

test('chisel.decodeParams, two empty string key/values', (t) => {
    t.deepEqual(
        chisel.decodeParams('&'),
        {}
    );
});

test('chisel.decodeParams, multiple empty string key/values', (t) => {
    t.deepEqual(
        chisel.decodeParams('&&'),
        {}
    );
});

test('chisel.decodeParams, empty string sub-key', (t) => {
    t.deepEqual(
        chisel.decodeParams('a.=5'),
        {'a': {'': '5'}}
    );
});

test('chisel.decodeParams, anchor tag', (t) => {
    t.deepEqual(
        chisel.decodeParams('a=7&b'),
        {'a': '7'}
    );
});

test('chisel.decodeParams, key with no equal', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a=7&b&c=11');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid key/value pair 'b'");
});

test('chisel.decodeParams, key with no equal - long key/value', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams(`a=7&${'b'.repeat(2000)}&c=11`);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `Invalid key/value pair '${'b'.repeat(100)}'`);
});

test('chisel.decodeParams, two empty string keys with no equal', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a&b');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid key/value pair 'a'");
});

test('chisel.decodeParams, multiple empty string keys with no equal', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a&b&c');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid key/value pair 'a'");
});

test('chisel.decodeParams, duplicate keys', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('abc=21&ab=19&abc=17');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Duplicate key 'abc'");
});

test('chisel.decodeParams, duplicate keys - long key/value', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams(`${'a'.repeat(2000)}=21&ab=19&${'a'.repeat(2000)}=17`);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `Duplicate key '${'a'.repeat(100)}'`);
});

test('chisel.decodeParams, duplicate index', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a.0=0&a.1=1&a.0=2');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Duplicate key 'a.0'");
});

test('chisel.decodeParams, index too large', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a.0=0&a.1=1&a.3=3');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid array index '3' in key 'a.3'");
});

test('chisel.decodeParams, index too large - long key/value', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams(`${'a'.repeat(2000)}.0=0&${'a'.repeat(2000)}.1=1&${'a'.repeat(2000)}.3=3`);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `Invalid array index '3' in key '${'a'.repeat(100)}'`);
});

test('chisel.decodeParams, negative index', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a.0=0&a.1=1&a.-3=3');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid array index '-3' in key 'a.-3'");
});

test('chisel.decodeParams, invalid index', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a.0=0&a.1asdf=1');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid array index '1asdf' in key 'a.1asdf'");
});

test('chisel.decodeParams, first list, then dict', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams('a.0=0&a.b=0');
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid array index 'b' in key 'a.b'");
});

test('chisel.decodeParams, first list, then dict - long key/value', (t) => {
    let errorMessage = null;
    try {
        chisel.decodeParams(`${'a'.repeat(2000)}.0=0&${'a'.repeat(2000)}.b=0`);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, `Invalid array index 'b' in key '${'a'.repeat(100)}'`);
});


//
// chisel.validateType tests
//

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

test('chisel.validateType, float error null', (t) => {
    let errorMessage = null;
    const obj = null;
    try {
        validateType({'builtin': 'float'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'float'");
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
    const obj = null;
    try {
        validateType({'builtin': 'bool'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'bool'");
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
    const obj = null;
    try {
        validateType({'builtin': 'date'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'date'");
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
    const obj = null;
    try {
        validateType({'builtin': 'datetime'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'datetime'");
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
    const obj = null;
    try {
        validateType({'builtin': 'uuid'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'uuid'");
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

test('chisel.validateType, object error', (t) => {
    let errorMessage = null;
    const obj = null;
    try {
        validateType({'builtin': 'object'}, obj);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object'), expected type 'object'");
});

test('chisel.validateType, array', (t) => {
    const obj = [1, 2, 3];
    t.deepEqual(validateType({'array': {'type': {'builtin': 'int'}}}, obj), obj);
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
                'type': {'dict': {'type': {'builtin': 'int'}, 'key_type': {'user': 'MyEnum'}}}
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
                'type': {'dict': {'type': {'builtin': 'int'}, 'key_type': {'builtin': 'string'}, 'key_attr': {'len_lt': 10}}}
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

test('chisel.validateType, typedef attr len_eq', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'len_eq': 5}
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

test('chisel.validateType, typedef attr len_eq object', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'dict': {'type': {'builtin': 'int'}}},
                'attr': {'len_eq': 5}
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

test('chisel.validateType, typedef attr len_lt', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'len_lt': 5}
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

test('chisel.validateType, typedef attr len_lte', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'len_lte': 5}
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

test('chisel.validateType, typedef attr len_gt', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'len_gt': 5}
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

test('chisel.validateType, typedef attr len_gte', (t) => {
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'array': {'type': {'builtin': 'int'}}},
                'attr': {'len_gte': 5}
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
                    {'name': 'b', 'type': {'builtin': 'int'}, 'nullable': true},
                    {'name': 'c', 'type': {'builtin': 'string'}, 'nullable': true},
                    {'name': 'd', 'type': {'builtin': 'float'}, 'nullable': false}
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
                    {'name': 'b', 'type': {'builtin': 'int'}, 'attr': {'lt': 5}, 'nullable': true}
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
    t.is(chisel.validateType(types, 'MyBadBuiltin', null), null);
    t.is(chisel.validateType(types, 'MyBadType', null), null);
    t.is(chisel.validateType(types, 'MyBadUser', null), null);
});
