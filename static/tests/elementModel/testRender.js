// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/* eslint-disable id-length */

import browserEnv from 'browser-env';
import {renderElements} from '../../src/elementModel/render.js';
import test from 'ava';
import {validateElements} from '../../src/elementModel/model.js';


// Add browser globals
browserEnv(['document']);


test('renderElements', (t) => {
    document.body.innerHTML = '';
    renderElements(document.body, {'html': 'div'});
    t.is(document.body.innerHTML, '<div></div>');
    renderElements(document.body, [{'html': 'div'}, {'html': 'div', 'attr': {'id': 'Id'}}]);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div>');
    renderElements(document.body, {'html': 'div'}, false);
    t.is(document.body.innerHTML, '<div></div><div id="Id"></div><div></div>');
    renderElements(document.body, null);
    t.is(document.body.innerHTML, '');
    renderElements(document.body);
    t.is(document.body.innerHTML, '');
});


test('renderElements, basic', (t) => {
    renderElements(document.body, [
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


test('renderElements, non-string attribute value', (t) => {
    const elements = {'html': 'span', 'attr': {'style': 0}};
    validateElements(elements);
    renderElements(document.body, elements);
    t.is(
        document.body.innerHTML,
        '<span style="0"></span>'
    );
});


test('renderElements, svg', (t) => {
    renderElements(document.body, [
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


test('renderElements, element callback', (t) => {
    let callbackCount = 0;
    const callback = (element) => {
        t.true(typeof element !== 'undefined');
        callbackCount += 1;
    };
    renderElements(document.body, [
        {'html': 'div', 'callback': callback}
    ]);
    t.is(
        document.body.innerHTML,
        '<div></div>'
    );
    t.is(callbackCount, 1);
});
