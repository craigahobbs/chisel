// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/* eslint-disable id-length */

import test from 'ava';
import {validateElements} from '../../src/elementModel/model.js';


test('validateElements', (t) => {
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
    validateElements(elements);
    t.pass();
});


test('validateElements, error element type', (t) => {
    const elements = {
        'html': 'html',
        'elem': [0]
    };
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid element 0 (type 'number')");
});


test('validateElements, error element model validation', (t) => {
    const elements = {
        'html': 'html',
        'unknown': 'abc'
    };
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Unknown member 'unknown'");
});


test('validateElements, error missing element key', (t) => {
    const elements = {};
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Missing element key {} (type 'object')");
});


test('validateElements, null callback value', (t) => {
    const elements = {'html': 'span', 'attr': {'style': null}, 'callback': null};
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid value null (type 'object') for member 'callback', expected type 'object'");
});


test('validateElements, invalid callback value', (t) => {
    const elements = {'html': 'span', 'attr': {'style': null}, 'callback': 0};
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, "Invalid element callback function 0 (type 'number')");
});


test('validateElements, error text element with attr', (t) => {
    const elements = {'text': 'abc', 'attr': null};
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, 'Invalid text element member "attr" "abc" (type \'string\')');
});


test('validateElements, error text element with elem', (t) => {
    const elements = {'text': 'abc', 'elem': null};
    let errorMessage = null;
    try {
        validateElements(elements);
    } catch ({message}) {
        errorMessage = message;
    }
    t.is(errorMessage, 'Invalid text element member "elem" "abc" (type \'string\')');
});
