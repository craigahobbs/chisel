import * as chisel from '../src/chisel.js';
import {DocPage} from '../src/doc.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */
/* eslint-disable max-len */


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
                                reject();
                            }
                        })
                    };
                }
                resolve({
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
            }
        };
    }
}


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
    t.is(document.body.innerHTML, "Error: Invalid value \"\" (type 'string') for member 'name', expected type 'string' [len &gt; 0]");
    t.deepEqual(WindowFetchMock.calls, []);
});

test('DocPage.render, index error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'error': 'UnexpectedError'
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.body.innerHTML, 'Error: UnexpectedError');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined],
        'resource response.json'
    ]);
});

test('DocPage.render, index unexpected error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'error': true}]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.body.innerHTML, 'An unexpected error occurred.');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_index', undefined]
    ]);
});

test('DocPage.render, request', (t) => {
    window.location.hash = '#name=test';
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
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request/test', undefined],
        'resource response.json'
    ]);
});

test('DocPage.render, request url', (t) => {
    window.location.hash = '#url=https%3A%2F%2Fcraigahobbs.github.io%2Fchisel%2Fdoc%2Fdoc_request%2Fchisel_doc_request';
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
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['https://craigahobbs.github.io/chisel/doc/doc_request/chisel_doc_request', undefined],
        'resource response.json'
    ]);
});

test('DocPage.render, request error', (t) => {
    window.location.hash = '#name=test';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'error': 'UnknownName'
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.body.innerHTML, 'Error: UnknownName');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request/test', undefined],
        'resource response.json'
    ]);
});

test('DocPage.render, request unexpected error', (t) => {
    window.location.hash = '#name=test';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'error': true}]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.body.innerHTML, 'An unexpected error occurred.');
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request/test', undefined]
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
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['doc_request/test', undefined],
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

test('DocPage.errorPage', (t) => {
    t.deepEqual(
        DocPage.errorPage(),
        {'text': 'An unexpected error occurred.'}
    );
});

test('DocPage.errorPage, error', (t) => {
    t.deepEqual(
        DocPage.errorPage('Ouch!'),
        {'text': 'Error: Ouch!'}
    );
});

test('DocPage.indexPage', (t) => {
    t.deepEqual(
        DocPage.indexPage({
            'title': 'The Title',
            'groups': {
                'B Group': ['name3', 'name4'],
                'C Group': ['name5'],
                'A Group': ['name2', 'name1']
            }
        }),
        [
            {'html': 'h1', 'elem': {'text': 'The Title'}},
            [
                [
                    {'html': 'h2', 'elem': {'text': 'A Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-request-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name1'}, 'elem': {'text': 'name1'}}},
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name2'}, 'elem': {'text': 'name2'}}}
                    ]}}}
                ],
                [
                    {'html': 'h2', 'elem': {'text': 'B Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-request-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name3'}, 'elem': {'text': 'name3'}}},
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name4'}, 'elem': {'text': 'name4'}}}
                    ]}}}
                ],
                [
                    {'html': 'h2', 'elem': {'text': 'C Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-request-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name5'}, 'elem': {'text': 'name5'}}}
                    ]}}}
                ]
            ]
        ]
    );
});

test('DocPage.requestPage, empty', (t) => {
    window.location.hash = '#name=empty';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.requestPage({
            'name': 'empty',
            'urls': [],
            'action': {
                'name': 'empty',
                'errors': {'name': 'empty_error', 'values': []},
                'input': {'name': 'empty_input', 'members': []},
                'output': {'name': 'empty_output', 'members': []},
                'path': {'name': 'empty_path', 'members': []},
                'query': {'name': 'empty_query', 'members': []}
            }
        }),
        [
            {
                'html': 'p',
                'elem': {'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}}
            },
            {'html': 'h1', 'elem': {'text': 'empty'}},
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null
        ]
    );
});

test('DocPage.requestPage, request', (t) => {
    window.location.hash = '#name=request';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.requestPage({
            'name': 'request',
            'urls': [{'url': '/request'}]
        }),
        [
            {
                'html': 'p',
                'elem': {'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}}
            },
            {'html': 'h1', 'elem': {'text': 'request'}},
            null,
            null,
            {'html': 'p', 'attr': {'class': 'chisel-note'}, 'elem': [
                {'html': 'b', 'elem': {'text': 'Note: '}},
                {'text': 'The request is exposed at the following URL:'},
                {'html': 'ul', 'elem': [
                    {'html': 'li', 'elem': [{'html': 'a', 'attr': {'href': '/request'}, 'elem': {'text': '/request'}}]}
                ]}
            ]},
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null
        ]
    );
});

test('DocPage.structElem, empty', (t) => {
    window.location.hash = '#name=test';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.structElem({'name': 'TestStruct'}, 'h2', 'struct TestStruct'),
        [
            {
                'html': 'h2',
                'attr': {'id': 'name=test&type_TestStruct'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'struct TestStruct'}}
            },
            null,
            [
                {'html': 'p', 'elem': {'text': 'The struct is empty.'}}
            ]
        ]
    );
});

test('DocPage.enumElem, empty', (t) => {
    window.location.hash = '#name=test';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.enumElem({'name': 'TestEnum'}, 'h2', 'enum TestEnum'),
        [
            {
                'html': 'h2',
                'attr': {'id': 'name=test&type_TestEnum'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum TestEnum'}}
            },
            null,
            [
                {'html': 'p', 'elem': {'text': 'The enum is empty.'}}
            ]
        ]
    );
});

test('DocPage.requestPage', (t) => {
    window.location.hash = '#name=test';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.requestPage({
            'name': 'test',
            'urls': [
                {'url': '/test'},
                {'method': 'GET', 'url': '/test'},
                {'method': 'GET', 'url': '/'}
            ],
            'types': {
                'test': {
                    'action': {
                        'name': 'test',
                        'doc': ' The test action.\n\n This is some more information.',
                        'path': 'test_path',
                        'query': 'test_query',
                        'input': 'test_input',
                        'output': 'test_output',
                        'errors': 'test_errors'
                    }
                },
                'test_path': {
                    'struct': {
                        'name': 'test_path',
                        'members': [
                            {'name': 'pa', 'type': {'builtin': 'bool'}, 'doc': ' The url member "pa".'},
                            {'name': 'pb', 'type': {'builtin': 'date'}, 'doc': ' The url member "pb".\n\n\n More info.\n'},
                            {'name': 'pc', 'type': {'builtin': 'datetime'}},
                            {'name': 'pd', 'type': {'builtin': 'float'}},
                            {'name': 'pe', 'type': {'builtin': 'int'}},
                            {'name': 'pf', 'type': {'builtin': 'object'}},
                            {'name': 'pg', 'type': {'builtin': 'string'}},
                            {'name': 'ph', 'type': {'builtin': 'uuid'}}
                        ]
                    }
                },
                'test_query': {
                    'struct': {
                        'name': 'test_query',
                        'members': [
                            {'name': 'qa', 'type': {'builtin': 'int'}, 'attr': {'gt': 0.0, 'lt': 10.0}},
                            {'name': 'qb', 'type': {'builtin': 'int'}, 'attr': {'gte': 0.0, 'lte': 10.0}},
                            {'name': 'qc', 'type': {'builtin': 'int'}, 'attr': {'eq': 10.0}},
                            {'name': 'qd', 'type': {'builtin': 'float'}, 'attr': {'gt': 0.5, 'lt': 9.5}},
                            {'name': 'qe', 'type': {'builtin': 'float'}, 'attr': {'gte': 0.5, 'lte': 9.5}},
                            {'name': 'qf', 'type': {'builtin': 'float'}, 'attr': {'eq': 9.5}},
                            {'name': 'qg', 'type': {'builtin': 'string'}, 'attr': {'len_gt': 0, 'len_lt': 10}},
                            {'name': 'qh', 'type': {'builtin': 'string'}, 'attr': {'len_gte': 0, 'len_lte': 10}},
                            {'name': 'qi', 'type': {'builtin': 'string'}, 'attr': {'len_eq': 10}},
                            {'name': 'qj', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'len_gt': 0, 'len_lt': 10}},
                            {'name': 'qk', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'len_gte': 0, 'len_lte': 10}},
                            {'name': 'ql', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'len_gte': 0, 'len_lte': 10}},
                            {
                                'name': 'qm',
                                'type': {'dict': {'type': {'builtin': 'string'}}},
                                'attr': {'len_gt': 0, 'len_lt': 10}
                            },
                            {
                                'name': 'qn',
                                'type': {'dict': {'type': {'builtin': 'string'}}},
                                'attr': {'len_gte': 0, 'len_lte': 10}
                            },
                            {
                                'name': 'qo',
                                'type': {'dict': {'type': {'builtin': 'string'}}},
                                'attr': {'len_eq': 10}
                            }
                        ]
                    }
                },
                'test_input': {
                    'struct': {
                        'name': 'test_input',
                        'members': [
                            {'name': 'ia', 'optional': true, 'type': {'builtin': 'int'}},
                            {'name': 'ib', 'nullable': true, 'type': {'builtin': 'float'}},
                            {'name': 'ic', 'nullable': true, 'optional': true, 'type': {'builtin': 'string'}},
                            {
                                'name': 'id',
                                'nullable': true,
                                'optional': true,
                                'type': {'array': {'attr': {'len_gt': 5}, 'type': {'builtin': 'string'}}},
                                'attr': {'len_gt': 0}
                            }
                        ]
                    }
                },
                'test_output': {
                    'struct': {
                        'name': 'test_output',
                        'members': [
                            {'name': 'oa', 'type': {'user': 'PositiveInt'}},
                            {'name': 'ob', 'type': {'user': 'JustAString'}},
                            {'name': 'oc', 'type': {'user': 'Struct1'}},
                            {'name': 'od', 'type': {'user': 'Enum1'}},
                            {'name': 'oe', 'type': {'user': 'Enum2'}},
                            {'name': 'of', 'type': {'dict': {'key_type': {'user': 'Enum1'}, 'type': {'builtin': 'string'}}}},
                            {
                                'name': 'og',
                                'type': {'dict': {'key_type': {'user': 'JustAString'}, 'type': {'user': 'NonEmptyFloatArray'}}},
                                'attr': {'len_gt': 0}
                            }
                        ]
                    }
                },
                'test_errors': {
                    'enum': {
                        'name': 'test_errors',
                        'values': [
                            {'name': 'Error1'},
                            {'name': 'Error2'}
                        ]
                    }
                },
                'Enum1': {
                    'enum': {
                        'name': 'Enum1',
                        'doc': ' An enum.',
                        'values': [
                            {'name': 'e1', 'doc': ' The Enum1 value "e1"'},
                            {'name': 'e2', 'doc': ' The Enum1 value "e 2"\n\n More info.'}
                        ]
                    }
                },
                'Enum2': {
                    'enum': {
                        'name': 'Enum2',
                        'doc': ' Another enum.\n\n More info.',
                        'values': [
                            {'name': 'e3'}
                        ]
                    }
                },
                'Struct1': {
                    'struct': {
                        'name': 'Struct1',
                        'doc': ' A struct.',
                        'members': [
                            {'name': 'sa', 'type': {'builtin': 'int'}, 'doc': ' The struct member "sa"'},
                            {'name': 'sb', 'type': {'user': 'Struct2'}, 'doc': ' The struct member "sb"\n\n More info.'}
                        ]
                    }
                },
                'Struct2': {
                    'struct': {
                        'name': 'Struct2',
                        'doc': ' Another struct, a union.\n\n More info.',
                        'members': [
                            {'name': 'sa', 'type': {'builtin': 'string'}},
                            {'name': 'sb', 'type': {'builtin': 'int'}}
                        ],
                        'union': true
                    }
                },
                'NonEmptyFloatArray': {
                    'typedef': {
                        'name': 'NonEmptyFloatArray',
                        'type': {'array': {'type': {'builtin': 'float'}}},
                        'attr': {'len_gt': 0}
                    }
                },
                'JustAString': {
                    'typedef': {
                        'name': 'JustAString',
                        'doc': ' Just a string.\n\n More info.',
                        'type': {'builtin': 'string'}
                    }
                },
                'PositiveInt': {
                    'typedef': {
                        'name': 'PositiveInt',
                        'doc': ' A positive integer.',
                        'type': {'builtin': 'int'},
                        'attr': {'gt': 0.0}
                    }
                }
            }
        }),
        [
            {'html': 'p', 'elem': {
                'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}
            }},
            {'html': 'h1', 'elem': {'text': 'test'}},
            null,
            [
                {'html': 'p', 'elem': {'text': ' The test action.'}},
                {'html': 'p', 'elem': {'text': ' This is some more information.'}}
            ],
            {'html': 'p', 'attr': {'class': 'chisel-note'}, 'elem': [
                {'html': 'b', 'elem': {'text': 'Note: '}},
                {'text': 'The request is exposed at the following URLs:'},
                {'html': 'ul', 'elem': [
                    {'html': 'li', 'elem': [{'attr': {'href': '/test'}, 'elem': {'text': '/test'}, 'html': 'a'}]},
                    {'html': 'li', 'elem': [{'attr': {'href': '/test'}, 'elem': {'text': 'GET /test'}, 'html': 'a'}]},
                    {'html': 'li', 'elem': [{'attr': {'href': '/'}, 'elem': {'text': 'GET /'}, 'html': 'a'}]}
                ]}
            ]},
            [
                {
                    'html': 'h2',
                    'attr': {'id': 'name=test&type_test_path'},
                    'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Path Parameters'}}
                },
                null,
                {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Name'}},
                        {'html': 'th', 'elem': {'text': 'Type'}},
                        null,
                        {'html': 'th', 'elem': {'text': 'Description'}}
                    ]},
                    [
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pa'}},
                            {'html': 'td', 'elem': {'text': 'bool'}},
                            null,
                            {'html': 'td', 'elem': [{'html': 'p', 'elem': {'text': ' The url member "pa".'}}]}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pb'}},
                            {'html': 'td', 'elem': {'text': 'date'}},
                            null,
                            {'html': 'td', 'elem': [
                                {'html': 'p', 'elem': {'text': ' The url member "pb".'}},
                                {'html': 'p', 'elem': {'text': ' More info.'}}
                            ]}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pc'}},
                            {'html': 'td', 'elem': {'text': 'datetime'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pd'}},
                            {'html': 'td', 'elem': {'text': 'float'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pe'}},
                            {'html': 'td', 'elem': {'text': 'int'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pf'}},
                            {'html': 'td', 'elem': {'text': 'object'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'pg'}},
                            {'html': 'td', 'elem': {'text': 'string'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ph'}},
                            {'html': 'td', 'elem': {'text': 'uuid'}},
                            null,
                            {'html': 'td', 'elem': null}
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'html': 'h2',
                    'attr': {'id': 'name=test&type_test_query'},
                    'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Query Parameters'}}
                },
                null,
                {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Name'}},
                        {'html': 'th', 'elem': {'text': 'Type'}},
                        {'html': 'th', 'elem': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qa'}},
                            {'html': 'td', 'elem': {'text': 'int'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qb'}},
                            {'html': 'td', 'elem': {'text': 'int'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qc'}},
                            {'html': 'td', 'elem': {'text': 'int'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qd'}},
                            {'html': 'td', 'elem': {'text': 'float'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}>${chisel.nbsp}0.5`}},
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}<${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qe'}},
                            {'html': 'td', 'elem': {'text': 'float'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}>=${chisel.nbsp}0.5`}},
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}<=${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qf'}},
                            {'html': 'td', 'elem': {'text': 'float'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `value${chisel.nbsp}==${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qg'}},
                            {'html': 'td', 'elem': {'text': 'string'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(value)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(value)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qh'}},
                            {'html': 'td', 'elem': {'text': 'string'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(value)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(value)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qi'}},
                            {'html': 'td', 'elem': {'text': 'string'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(value)${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qj'}},
                            {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qk'}},
                            {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ql'}},
                            {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qm'}},
                            {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qn'}},
                            {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'qo'}},
                            {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'html': 'h2',
                    'attr': {'id': 'name=test&type_test_input'},
                    'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Input Parameters'}}
                },
                null,
                {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Name'}},
                        {'html': 'th', 'elem': {'text': 'Type'}},
                        {'html': 'th', 'elem': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ia'}},
                            {'html': 'td', 'elem': {'text': 'int'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': 'optional'}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ib'}},
                            {'html': 'td', 'elem': {'text': 'float'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': 'nullable'}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ic'}},
                            {'html': 'td', 'elem': {'text': 'string'}},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': 'optional'}},
                                {'html': 'li', 'elem': {'text': 'nullable'}}
                            ]}},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'id'}},
                            {'html': 'td', 'elem': [{'text': 'string'}, {'text': `${chisel.nbsp}[]`}]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': 'optional'}},
                                {'html': 'li', 'elem': {'text': 'nullable'}},
                                {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'html': 'h2',
                    'attr': {'id': 'name=test&type_test_output'},
                    'elem': {'attr': {'class': 'linktarget'}, 'elem': {'text': 'Output Parameters'}, 'html': 'a'}
                },
                null,
                {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [
                        {'html': 'th', 'elem': {'text': 'Name'}},
                        {'html': 'th', 'elem': {'text': 'Type'}},
                        {'html': 'th', 'elem': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'oa'}},
                            {'html': 'td', 'elem': {
                                'html': 'a',
                                'attr': {'href': '#name=test&type_PositiveInt'},
                                'elem': {'text': 'PositiveInt'}
                            }},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'ob'}},
                            {'html': 'td', 'elem': {
                                'html': 'a',
                                'attr': {'href': '#name=test&type_JustAString'},
                                'elem': {'text': 'JustAString'}
                            }},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'oc'}},
                            {'html': 'td', 'elem': {
                                'html': 'a',
                                'attr': {'href': '#name=test&type_Struct1'},
                                'elem': {'text': 'Struct1'}
                            }},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'od'}},
                            {'html': 'td', 'elem': {
                                'html': 'a',
                                'attr': {'href': '#name=test&type_Enum1'},
                                'elem': {'text': 'Enum1'}
                            }},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'oe'}},
                            {'html': 'td', 'elem': {
                                'html': 'a',
                                'attr': {'href': '#name=test&type_Enum2'},
                                'elem': {'text': 'Enum2'}
                            }},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'of'}},
                            {'html': 'td', 'elem': [
                                [
                                    {'html': 'a', 'attr': {'href': '#name=test&type_Enum1'}, 'elem': {'text': 'Enum1'}},
                                    {'text': `${chisel.nbsp}:${chisel.nbsp}`}
                                ],
                                {'text': 'string'}, {'text': `${chisel.nbsp}{}`}
                            ]},
                            {'html': 'td', 'elem': null},
                            null
                        ]},
                        {'html': 'tr', 'elem': [
                            {'html': 'td', 'elem': {'text': 'og'}},
                            {'html': 'td', 'elem': [
                                [
                                    {'html': 'a', 'attr': {'href': '#name=test&type_JustAString'}, 'elem': {'text': 'JustAString'}},
                                    {'text': `${chisel.nbsp}:${chisel.nbsp}`}
                                ],
                                {'html': 'a', 'attr': {'href': '#name=test&type_NonEmptyFloatArray'}, 'elem': {'text': 'NonEmptyFloatArray'}},
                                {'text': `${chisel.nbsp}{}`}
                            ]},
                            {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                {'html': 'li', 'elem': {'text': `len(dict)${chisel.nbsp}>${chisel.nbsp}0`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'html': 'h2',
                    'attr': {'id': 'name=test&type_test_errors'},
                    'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Error Codes'}}
                },
                null,
                {'html': 'table', 'elem': [
                    {'html': 'tr', 'elem': [{'html': 'th', 'elem': {'text': 'Value'}}, null]},
                    [
                        {'html': 'tr', 'elem': [{'html': 'td', 'elem': {'text': 'Error1'}}, null]},
                        {'html': 'tr', 'elem': [{'html': 'td', 'elem': {'text': 'Error2'}}, null]}
                    ]
                ]}
            ],
            [
                {'html': 'h2', 'elem': {'text': 'Typedefs'}},
                [
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_JustAString'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef JustAString'}}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' Just a string.'}},
                            {'html': 'p', 'elem': {'text': ' More info.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Type'}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'string'}},
                                null
                            ]}
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_NonEmptyFloatArray'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef NonEmptyFloatArray'}}
                        },
                        null,
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [{'html': 'th', 'elem': {'text': 'Type'}}, {'html': 'th', 'elem': {'text': 'Attributes'}}]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': [{'text': 'float'}, {'text': `${chisel.nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_PositiveInt'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef PositiveInt'}}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' A positive integer.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Type'}},
                                {'html': 'th', 'elem': {'text': 'Attributes'}}
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'int'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${chisel.nbsp}>${chisel.nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ]
                ]
            ],
            [
                {'html': 'h2', 'elem': {'text': 'Struct Types'}},
                [
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_Struct1'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'struct Struct1'}}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' A struct.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Name'}},
                                {'html': 'th', 'elem': {'text': 'Type'}},
                                null,
                                {'html': 'th', 'elem': {'text': 'Description'}}
                            ]},
                            [
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'sa'}},
                                    {'html': 'td', 'elem': {'text': 'int'}},
                                    null,
                                    {'html': 'td', 'elem': [{'html': 'p', 'elem': {'text': ' The struct member "sa"'}}]}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'sb'}},
                                    {'html': 'td', 'elem': {
                                        'html': 'a', 'attr': {'href': '#name=test&type_Struct2'}, 'elem': {'text': 'Struct2'}
                                    }},
                                    null,
                                    {'html': 'td', 'elem': [
                                        {'html': 'p', 'elem': {'text': ' The struct member "sb"'}},
                                        {'html': 'p', 'elem': {'text': ' More info.'}}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_Struct2'},
                            'elem': {'attr': {'class': 'linktarget'}, 'elem': {'text': 'union Struct2'}, 'html': 'a'}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' Another struct, a union.'}},
                            {'html': 'p', 'elem': {'text': ' More info.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Name'}},
                                {'html': 'th', 'elem': {'text': 'Type'}},
                                null,
                                null
                            ]},
                            [
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'sa'}},
                                    {'html': 'td', 'elem': {'text': 'string'}},
                                    null,
                                    null
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'sb'}},
                                    {'html': 'td', 'elem': {'text': 'int'}},
                                    null,
                                    null
                                ]}
                            ]
                        ]}
                    ]
                ]
            ],
            [
                {'html': 'h2', 'elem': {'text': 'Enum Types'}},
                [
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_Enum1'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum Enum1'}}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' An enum.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Value'}},
                                {'html': 'th', 'elem': {'text': 'Description'}}
                            ]},
                            [
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'e1'}},
                                    {'html': 'td', 'elem': [{'html': 'p', 'elem': {'text': ' The Enum1 value "e1"'}}]}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'e2'}},
                                    {'html': 'td', 'elem': [
                                        {'html': 'p', 'elem': {'text': ' The Enum1 value "e 2"'}},
                                        {'html': 'p', 'elem': {'text': ' More info.'}}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=test&type_Enum2'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum Enum2'}}
                        },
                        [
                            {'html': 'p', 'elem': {'text': ' Another enum.'}},
                            {'html': 'p', 'elem': {'text': ' More info.'}}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [{'html': 'th', 'elem': {'text': 'Value'}}, null]},
                            [
                                {'html': 'tr', 'elem': [{'html': 'td', 'elem': {'text': 'e3'}}, null]}
                            ]
                        ]}
                    ]
                ]
            ]
        ]
    );
});
