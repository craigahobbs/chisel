import * as chisel from '../src/chisel.js';
import test from 'ava';

/* eslint-disable id-length */


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
