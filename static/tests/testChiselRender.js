import * as chisel from '../src/chisel.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


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
        {'svg': 'svg', 'attr': {'width': '600', 'height': '400'}, 'elem': [
            {
                'svg': 'rect',
                'attr': {'x': '10', 'y': '10', 'width': '20', 'height': '20', 'style': 'fill: #ff0000;'}
            },
            {
                'svg': 'rect',
                'attr': {'x': '10', 'y': '10', 'width': '20', 'height': '20', 'style': 'fill: #00ff00;'}
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

test('chisel.validateElements', (t) => {
    const elements = {
        'html': 'html',
        'elem': [
            {
                'html': 'h1',
                'elem': {'text': 'Title'}
            },
            {
                'html': 'p',
                'attr': null,
                'elem': [
                    {'text': 'This is some '},
                    {'html': 'span', 'attr': {'style': 'font-weight: bold;'}, 'elem': {'text': 'bolded text!'}}
                ]
            }
        ]
    };
    chisel.validateElements(elements);
    t.pass();
});

test('chisel.validateElements, error element type', (t) => {
    const elements = {
        'html': 'html',
        'elem': [0]
    };
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid element 0 (type 'number')");
});

test('chisel.validateElements, error element model validation', (t) => {
    const elements = {
        'html': 'html',
        'unknown': 'abc'
    };
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member 'unknown'");
});

test('chisel.validateElements, error missing element key', (t) => {
    const elements = {};
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Missing element key {} (type 'object')");
});

test('chisel.validateElements, invalid attribute value', (t) => {
    const elements = {'html': 'span', 'attr': {'style': 0, '_callback': null}};
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid element attribute value 0 (type 'number')");
});

test('chisel.validateElements, invalid callback attribute value', (t) => {
    const elements = {'html': 'span', 'attr': {'style': null, '_callback': 0}};
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid element attribute callback 0 (type 'number')");
});

test('chisel.validateElements, error text element with attr', (t) => {
    const elements = {'text': 'abc', 'attr': null};
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, 'Invalid text element member "attr" "abc" (type \'string\')');
});

test('chisel.validateElements, error text element with elem', (t) => {
    const elements = {'text': 'abc', 'elem': null};
    let errorMessage = null;
    try {
        chisel.validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, 'Invalid text element member "elem" "abc" (type \'string\')');
});
