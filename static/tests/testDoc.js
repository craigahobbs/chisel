import {DocPage} from '../src/doc.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


test('DocPage.errorPage', (t) => {
    t.deepEqual(
        DocPage.errorPage({}),
        {'text': 'An unexpected error occurred'}
    );
});

test('DocPage.errorPage, error', (t) => {
    t.deepEqual(
        DocPage.errorPage({'error': 'Ouch!'}),
        {'text': 'Error: Ouch!'}
    );
});

test('DocPage.indexPage', (t) => {
    t.deepEqual(
        DocPage.indexPage('The Title', {
            'groups': {
                'B Group': ['name3', 'name4'],
                'C Group': ['name5'],
                'A Group': ['name2', 'name1']
            }
        }),
        [
            {'tag': 'h1', 'elems': {'text': 'The Title'}},
            [
                [
                    {'tag': 'h2', 'elems': {'text': 'A Group'}},
                    {'tag': 'ul', 'attrs': {'class': 'chisel-request-list'}, 'elems': {'tag': 'li', 'elems': {'tag': 'ul', 'elems': [
                        {'tag': 'li', 'elems': {'tag': 'a', 'attrs': {'href': 'blank#name=name1'}, 'elems': {'text': 'name1'}}},
                        {'tag': 'li', 'elems': {'tag': 'a', 'attrs': {'href': 'blank#name=name2'}, 'elems': {'text': 'name2'}}}
                    ]}}}
                ],
                [
                    {'tag': 'h2', 'elems': {'text': 'B Group'}},
                    {'tag': 'ul', 'attrs': {'class': 'chisel-request-list'}, 'elems': {'tag': 'li', 'elems': {'tag': 'ul', 'elems': [
                        {'tag': 'li', 'elems': {'tag': 'a', 'attrs': {'href': 'blank#name=name3'}, 'elems': {'text': 'name3'}}},
                        {'tag': 'li', 'elems': {'tag': 'a', 'attrs': {'href': 'blank#name=name4'}, 'elems': {'text': 'name4'}}}
                    ]}}}
                ],
                [
                    {'tag': 'h2', 'elems': {'text': 'C Group'}},
                    {'tag': 'ul', 'attrs': {'class': 'chisel-request-list'}, 'elems': {'tag': 'li', 'elems': {'tag': 'ul', 'elems': [
                        {'tag': 'li', 'elems': {'tag': 'a', 'attrs': {'href': 'blank#name=name5'}, 'elems': {'text': 'name5'}}}
                    ]}}}
                ]
            ]
        ]
    );
});
