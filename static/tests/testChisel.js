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
    chisel.render(document.body, {'html': 'div'});
    t.is(document.body.innerHTML, '<div></div>');
    chisel.render(document.body, [{'html': 'div'}, {'html': 'div', 'attr': {'id': 'Id'}}]);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div>');
    chisel.render(document.body, {'html': 'div'}, false);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div><div></div>');
    chisel.render(document.body, null);
    t.is(document.body.innerHTML, '');
    chisel.render(document.body);
    t.is(document.body.innerHTML, '');
});

test('chisel.render, basic', (t) => {
    chisel.render(document.body, [
        {'html': 'h1', 'elem': {'text': 'Hello, World!'}},
        [
            {'html': 'p', 'elem': [{'text': 'Word'}]},
            {'html': 'p', 'elem': [{'text': 'Two'}, {'text': 'Words'}]},
            {'html': 'p', 'elem': []},
            {'html': 'p', 'elem': null}
        ],
        {'html': 'div', 'attr': {'id': 'Id', 'class': null}}
    ]);
    t.is(
        document.body.innerHTML,
        '<h1>Hello, World!</h1><p>Word</p><p>TwoWords</p><p></p><p></p><div id="Id"></div>'
    );
});

test('chisel.render, svg', (t) => {
    chisel.render(document.body, [
        {'svg': 'svg', 'ns': 'http://www.w3.org/2000/svg', 'attr': {'width': 600, 'height': 400}, 'elem': [
            {
                'svg': 'rect', 'ns': 'http://www.w3.org/2000/svg',
                'attr': {'x': 10, 'y': 10, 'width': 20, 'height': 20, 'style': 'fill: #ff0000;'}
            },
            {
                'svg': 'rect', 'ns': 'http://www.w3.org/2000/svg',
                'attr': {'x': 10, 'y': 10, 'width': 20, 'height': 20, 'style': 'fill: #00ff00;'}
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
        {'html': 'div', 'attr': {'_callback': callback}},
        {'html': 'div', 'attr': {'_callback': null}}
    ]);
    t.is(
        document.body.innerHTML,
        '<div></div><div></div>'
    );
    t.is(callbackCount, 1);
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
