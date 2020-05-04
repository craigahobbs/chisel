import {DocPage} from '../src/doc.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */


// Add browser globals
browserEnv(['document', 'window']);


test('DocPage.render', (t) => {
    t.not(DocPage, null);
});
