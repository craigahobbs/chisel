import * as chisel from '../src/chisel.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


test('chisel.nbsp', (t) => {
    t.is(chisel.nbsp, String.fromCharCode(160));
});

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

test('chisel.svg', (t) => {
    t.deepEqual(
        chisel.svg('svg', {'width': 600, 'height': 400}),
        {'tag': 'svg', 'ns': 'http://www.w3.org/2000/svg', 'attrs': {'width': 600, 'height': 400}}
    );
});

test('chisel.text', (t) => {
    t.deepEqual(
        chisel.text('Hello'),
        {'text': 'Hello'}
    );
});

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

test('chisel.encodeParams', (t) => {
    t.is(
        chisel.encodeParams({
            'foo': 17,
            'bar': 19.33,
            'bonk': 'abc',
            ' th&ud ': ' ou&ch ',
            'fever': null
        }),
        '%20th%26ud%20=%20ou%26ch%20&bar=19.33&bonk=abc&foo=17'
    );
});

test('chisel.decodeParams', (t) => {
    t.deepEqual(
        chisel.decodeParams('%20th%26ud%20=%20ou%26ch%20&bar=19.33&bonk=abc&foo=17&empty'),
        {
            ' th&ud ': ' ou&ch ',
            'bar': '19.33',
            'bonk': 'abc',
            'empty': '',
            'foo': '17'
        }
    );
});

test('chisel.decodeParams, default', (t) => {
    window.location.hash = '#%20th%26ud%20=%20ou%26ch%20&bar=19.33&bonk=abc&foo=17&empty';
    t.deepEqual(
        chisel.decodeParams(),
        {
            ' th&ud ': ' ou&ch ',
            'bar': '19.33',
            'bonk': 'abc',
            'empty': '',
            'foo': '17'
        }
    );
});
