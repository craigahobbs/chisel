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
