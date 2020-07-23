import * as chisel from '../src/chisel.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


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
