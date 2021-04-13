// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/main/LICENSE

/* eslint-disable id-length */
/* eslint-disable max-len */

import {DocPage} from '../doc/doc.js';
import browserEnv from 'browser-env';
import test from 'ava';


// Add browser globals
browserEnv(['document', 'window']);


// Mock for window.fetch
class WindowFetchMock {
    static reset(responses) {
        window.fetch = WindowFetchMock.fetch;
        WindowFetchMock.calls = [];
        WindowFetchMock.responses = responses;
    }

    static fetch(resource, init) {
        const response = WindowFetchMock.responses.shift();
        WindowFetchMock.calls.push([resource, init]);
        return {
            'then': (resolve) => {
                if (response.error) {
                    return {
                        'then': () => ({
                            'catch': (reject) => {
                                reject(new Error('Unexpected error'));
                            }
                        })
                    };
                }
                try {
                    resolve({
                        'ok': 'ok' in response ? response.ok : true,
                        'statusText': 'statusText' in response ? response.statusText : 'OK',
                        'json': () => {
                            WindowFetchMock.calls.push('resource response.json');
                        }
                    });
                    return {
                        'then': (resolve2) => {
                            resolve2(response.json);
                            return {
                                // eslint-disable-next-line func-names
                                'catch': function() {
                                    // Do nothing
                                }
                            };
                        }
                    };
                } catch (error) {
                    return {
                        'then': () => ({
                            'catch': (reject) => {
                                reject(error);
                            }
                        })
                    };
                }
            }
        };
    }
}


test('DocPage.run', (t) => {
    window.location.hash = '#name=MyAction';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'name': 'MyAction',
                'types': {
                    'MyAction': {
                        'action': {
                            'name': 'MyAction'
                        }
                    }
                }
            }
        },
        {
            'json': {
                'name': 'MyAction2',
                'types': {
                    'MyAction2': {
                        'action': {
                            'name': 'MyAction2'
                        }
                    }
                }
            }
        }
    ]);

    // Run the application
    const docPage = DocPage.run();
    t.is(document.title, 'MyAction');
    t.not(document.body.innerHTML.search('<a class="linktarget">MyAction</a>'), -1);
    t.is(document.body.innerHTML.search('<a class="linktarget">MyAction2</a>'), -1);

    // Step
    window.location.hash = '#name=MyAction2';
    docPage.windowHashChangeArgs[1]();
    t.is(document.title, 'MyAction2');
    t.is(document.body.innerHTML.search('<a class="linktarget">MyAction</a>'), -1);
    t.not(document.body.innerHTML.search('<a class="linktarget">MyAction2</a>'), -1);

    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request?name=MyAction', undefined],
        'resource response.json',
        ['doc_request?name=MyAction2', undefined],
        'resource response.json'
    ]);

    // Uninit
    docPage.uninit();

    // Uninit, again
    docPage.uninit();
});


test('DocPage.render, command help', (t) => {
    window.location.hash = '#cmd.help=1';
    document.body.innerHTML = '';
    WindowFetchMock.reset([]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'Documentation');
    t.true(document.body.innerHTML.startsWith('<h1 id="cmd.help=1&amp;type_Documentation"><a class="linktarget">Documentation</a></h1>'));
    t.deepEqual(WindowFetchMock.calls, []);
});


test('DocPage.render, index', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'title': 'My APIs',
                'groups': {
                    'Documentation': ['chisel_doc_index', 'chisel_doc_request'],
                    'Redirects': ['redirect_doc'],
                    'Statics': ['static_chisel_js', 'static_doc_css', 'static_doc_html', 'static_doc_js']
                }
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'My APIs');
    t.true(document.body.innerHTML.startsWith('<h1>My APIs</h1>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined],
        'resource response.json'
    ]);
});


test('DocPage.render, validation error', (t) => {
    const docPage = new DocPage();
    const indexResponse = {
        'title': 'My APIs',
        'groups': {
            'My Group': ['my_api', 'my_api2']
        }
    };

    // Do the index render
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'json': indexResponse}]);
    docPage.render();
    t.not(docPage.params, null);
    t.is(document.title, 'My APIs');
    t.true(document.body.innerHTML.startsWith('<h1>My APIs</h1>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined],
        'resource response.json'
    ]);

    // Fail validation
    window.location.hash = '#name=';
    WindowFetchMock.reset([]);
    docPage.render();
    t.is(docPage.params, null);
    t.is(document.body.innerHTML, "<p>Error: Invalid value \"\" (type 'string') for member 'name', expected type 'string' [len &gt; 0]</p>");
    t.deepEqual(WindowFetchMock.calls, []);
});


test('DocPage.render, index error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'ok': false,
            'statusText': 'Internal Server Error',
            'json': {}
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, '<p>Error: Could not fetch index: Internal Server Error</p>');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined]
    ]);
});


test('DocPage.render, index unexpected error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'error': true}]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, '<p>Error: Unexpected error</p>');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined]
    ]);
});


test('DocPage.render, request', (t) => {
    window.location.hash = '#name=simple';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'name': 'simple',
                'action': {
                    'name': 'simple',
                    'input': {'members': [], 'name': 'simple_input'},
                    'errors': {'name': 'simple_error', 'values': []},
                    'output': {'members': [{'name': 'sum', 'type': {'builtin': 'int'}}], 'name': 'simple_output'},
                    'path': {'members': [], 'name': 'simple_path'},
                    'query': {
                        'name': 'simple_query',
                        'members': [
                            {'name': 'a', 'type': {'builtin': 'int'}},
                            {'name': 'b', 'type': {'builtin': 'int'}}
                        ]
                    }
                },
                'urls': [
                    {'method': 'GET', 'url': '/simple'}
                ]
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'simple');
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request?name=simple', undefined],
        'resource response.json'
    ]);
});


test('DocPage.render, request error', (t) => {
    window.location.hash = '#name=test';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'ok': false,
            'statusText': 'Bad Request',
            'json': {
                'error': 'UnknownName'
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, "<p>Error: Could not fetch request 'test': Bad Request</p>");
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request?name=test', undefined]
    ]);
});

test('DocPage.render, request unexpected error', (t) => {
    window.location.hash = '#name=test';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'error': true}]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, '<p>Error: Unexpected error</p>');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request?name=test', undefined]
    ]);
});


test('DocPage.render, request avoid re-render', (t) => {
    window.location.hash = '#name=test';
    document.body.innerHTML = '';

    // Do the render
    const docPage = new DocPage();
    WindowFetchMock.reset([
        {
            'json': {
                'name': 'test',
                'urls': [
                    {'method': 'GET', 'url': '/test'}
                ],
                'types': {
                    'test': {
                        'action': {
                            'name': 'test'
                        }
                    }
                }
            }
        }
    ]);
    docPage.render();
    t.is(document.title, 'test');
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request?name=test', undefined],
        'resource response.json'
    ]);

    // Call render again with same name - it should not re-render since its already rendered
    WindowFetchMock.reset([]);
    document.body.innerHTML = '';
    docPage.render();
    t.is(document.body.innerHTML, '');
    t.deepEqual(WindowFetchMock.calls, []);

    // Verify render when name is changed
    window.location.hash = '#name=test2';
    WindowFetchMock.reset([
        {
            'json': {
                'name': 'test2',
                'urls': [
                    {'method': 'GET', 'url': '/test2'}
                ],
                'types': {
                    'test2': {
                        'action': {
                            'name': 'test2'
                        }
                    }
                }
            }
        }
    ]);
    docPage.render();
    t.true(document.body.innerHTML.startsWith('<p>'));
});
