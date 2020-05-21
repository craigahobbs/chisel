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
                'action': {
                    'name': 'test',
                    'input': {'name': 'test_input', 'members': []},
                    'errors': {'name': 'test_error', 'values': []},
                    'output': {'name': 'test_output', 'members': []},
                    'path': {'name': 'test_path', 'members': []},
                    'query': {'name': 'test_query', 'members': []}
                },
                'urls': [
                    {'method': 'GET', 'url': '/test'}
                ]
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
                'action': {
                    'name': 'test2',
                    'input': {'name': 'test2_input', 'members': []},
                    'errors': {'name': 'test2_error', 'values': []},
                    'output': {'name': 'test2_output', 'members': []},
                    'path': {'name': 'test2_path', 'members': []},
                    'query': {'name': 'test2_query', 'members': []}
                },
                'urls': [
                    {'method': 'GET', 'url': '/test2'}
                ]
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
                'tag': 'p',
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'empty'}},
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

test('DocPage.requestPage, wsgiResponse', (t) => {
    window.location.hash = '#name=wsgiResponse';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.requestPage({
            'name': 'wsgiResponse',
            'urls': [{'method': 'POST', 'url': '/wsgiResponse'}],
            'action': {
                'name': 'wsgiResponse',
                'errors': {'name': 'wsgiResponse_error', 'values': []},
                'input': {'name': 'wsgiResponse_input', 'members': []},
                'path': {'name': 'wsgiResponse_path', 'members': []},
                'query': {'name': 'wsgiResponse_query', 'members': []}
            }
        }),
        [
            {
                'tag': 'p',
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'wsgiResponse'}},
            null,
            {'tag': 'p', 'attrs': {'class': 'chisel-note'}, 'elems': [
                {'tag': 'b', 'elems': {'text': 'Note: '}},
                {'text': 'The request is exposed at the following URL:'},
                {'tag': 'ul', 'elems': [
                    {'tag': 'li', 'elems': [{'tag': 'a', 'attrs': {'href': '/wsgiResponse'}, 'elems': {'text': 'POST /wsgiResponse'}}]}
                ]}
            ]},
            {'tag': 'p', 'attrs': {'class': 'chisel-note'}, 'elems': [
                {'tag': 'b', 'elems': {'text': 'Note: '}},
                {'text': 'The action has a non-default response. See documentation for details.'}
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
                'tag': 'p',
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'request'}},
            null,
            {'tag': 'p', 'attrs': {'class': 'chisel-note'}, 'elems': [
                {'tag': 'b', 'elems': {'text': 'Note: '}},
                {'text': 'The request is exposed at the following URL:'},
                {'tag': 'ul', 'elems': [
                    {'tag': 'li', 'elems': [{'tag': 'a', 'attrs': {'href': '/request'}, 'elems': {'text': '/request'}}]}
                ]}
            ]},
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

test('DocPage.structElem, empty', (t) => {
    window.location.hash = '#name=test';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.structElem({'name': 'TestStruct', 'members': []}, 'h2', 'struct TestStruct'),
        [
            {
                'tag': 'h2',
                'attrs': {'id': 'name=test&struct_TestStruct'},
                'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'struct TestStruct'}}
            },
            null,
            [
                {'tag': 'p', 'elems': {'text': 'The struct is empty.'}}
            ]
        ]
    );
});

test('DocPage.enumElem, empty', (t) => {
    window.location.hash = '#name=test';
    const docPage = new DocPage();
    docPage.updateParams();
    t.deepEqual(
        docPage.enumElem({'name': 'TestEnum', 'values': []}, 'h2', 'enum TestEnum'),
        [
            {
                'tag': 'h2',
                'attrs': {'id': 'name=test&enum_TestEnum'},
                'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'enum TestEnum'}}
            },
            null,
            [
                {'tag': 'p', 'elems': {'text': 'The enum is empty.'}}
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
            'doc': ' The test action.\n\n This is some more information.',
            'urls': [
                {'url': '/test'},
                {'method': 'GET', 'url': '/test'},
                {'method': 'GET', 'url': '/'}
            ],
            'action': {
                'name': 'test',
                'path': {
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
                },
                'query': {
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
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'string'}}},
                            'attr': {'len_gt': 0, 'len_lt': 10}
                        },
                        {
                            'name': 'qn',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'string'}}},
                            'attr': {'len_gte': 0, 'len_lte': 10}
                        },
                        {
                            'name': 'qo',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'string'}}},
                            'attr': {'len_eq': 10}
                        }
                    ]
                },
                'input': {
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
                },
                'output': {
                    'name': 'test_output',
                    'members': [
                        {'name': 'oa', 'type': {'typedef': 'PositiveInt'}},
                        {'name': 'ob', 'type': {'typedef': 'JustAString'}},
                        {'name': 'oc', 'type': {'struct': 'Struct1'}},
                        {'name': 'od', 'type': {'enum': 'Enum1'}},
                        {'name': 'oe', 'type': {'enum': 'Enum2'}},
                        {'name': 'of', 'type': {'dict': {'key_type': {'enum': 'Enum1'}, 'type': {'builtin': 'string'}}}},
                        {
                            'name': 'og',
                            'type': {'dict': {'key_type': {'typedef': 'JustAString'}, 'type': {'typedef': 'NonEmptyFloatArray'}}},
                            'attr': {'len_gt': 0}
                        }
                    ]
                },
                'errors': {
                    'name': 'test_error',
                    'values': [
                        {'value': 'Error1'},
                        {'value': 'Error2'}
                    ]
                }
            },
            'enums': [
                {
                    'name': 'Enum1',
                    'doc': ' An enum.',
                    'values': [
                        {'value': 'e1', 'doc': ' The Enum1 value "e1"'},
                        {'value': 'e2', 'doc': ' The Enum1 value "e 2"\n\n More info.'}
                    ]
                },
                {
                    'name': 'Enum2',
                    'doc': ' Another enum.\n\n More info.',
                    'values': [
                        {'value': 'e3'}
                    ]
                }
            ],
            'structs': [
                {
                    'name': 'Struct1',
                    'doc': ' A struct.',
                    'members': [
                        {'name': 'sa', 'type': {'builtin': 'int'}, 'doc': ' The struct member "sa"'},
                        {'name': 'sb', 'type': {'struct': 'Struct2'}, 'doc': ' The struct member "sb"\n\n More info.'}
                    ]
                },
                {
                    'name': 'Struct2',
                    'doc': ' Another struct, a union.\n\n More info.',
                    'members': [
                        {'name': 'sa', 'type': {'builtin': 'string'}},
                        {'name': 'sb', 'type': {'builtin': 'int'}}
                    ],
                    'union': true
                }
            ],
            'typedefs': [
                {'name': 'NonEmptyFloatArray', 'type': {'array': {'type': {'builtin': 'float'}}}, 'attr': {'len_gt': 0}},
                {
                    'name': 'JustAString',
                    'doc': ' Just a string.\n\n More info.',
                    'type': {'builtin': 'string'}
                },
                {'name': 'PositiveInt', 'type': {'builtin': 'int'}, 'attr': {'gt': 0.0}, 'doc': ' A positive integer.'}
            ]
        }),
        // =================
        // Begin requestPage
        // =================
        [
            {'tag': 'p', 'elems': {
                'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}
            }},
            {'tag': 'h1', 'elems': {'text': 'test'}},
            [
                {'tag': 'p', 'elems': {'text': ' The test action.'}},
                {'tag': 'p', 'elems': {'text': ' This is some more information.'}}
            ],
            {'tag': 'p', 'attrs': {'class': 'chisel-note'}, 'elems': [
                {'tag': 'b', 'elems': {'text': 'Note: '}},
                {'text': 'The request is exposed at the following URLs:'},
                {'tag': 'ul', 'elems': [
                    {'tag': 'li', 'elems': [{'attrs': {'href': '/test'}, 'elems': {'text': '/test'}, 'tag': 'a'}]},
                    {'tag': 'li', 'elems': [{'attrs': {'href': '/test'}, 'elems': {'text': 'GET /test'}, 'tag': 'a'}]},
                    {'tag': 'li', 'elems': [{'attrs': {'href': '/'}, 'elems': {'text': 'GET /'}, 'tag': 'a'}]}
                ]}
            ]},
            null,
            [
                {
                    'tag': 'h2',
                    'attrs': {'id': 'name=test&struct_test_path'},
                    'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Path Parameters'}}
                },
                null,
                {'tag': 'table', 'elems': [
                    {'tag': 'tr', 'elems': [
                        {'tag': 'th', 'elems': {'text': 'Name'}},
                        {'tag': 'th', 'elems': {'text': 'Type'}},
                        null,
                        {'tag': 'th', 'elems': {'text': 'Description'}}
                    ]},
                    [
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pa'}},
                            {'tag': 'td', 'elems': {'text': 'bool'}},
                            null,
                            {'tag': 'td', 'elems': [{'tag': 'p', 'elems': {'text': ' The url member "pa".'}}]}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pb'}},
                            {'tag': 'td', 'elems': {'text': 'date'}},
                            null,
                            {'tag': 'td', 'elems': [
                                {'tag': 'p', 'elems': {'text': ' The url member "pb".'}},
                                {'tag': 'p', 'elems': {'text': ' More info.'}}
                            ]}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pc'}},
                            {'tag': 'td', 'elems': {'text': 'datetime'}},
                            null,
                            {'tag': 'td'}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pd'}},
                            {'tag': 'td', 'elems': {'text': 'float'}},
                            null,
                            {'tag': 'td'}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pe'}},
                            {'tag': 'td', 'elems': {'text': 'int'}},
                            null,
                            {'tag': 'td'}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pf'}},
                            {'tag': 'td', 'elems': {'text': 'object'}},
                            null,
                            {'tag': 'td'}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'pg'}},
                            {'tag': 'td', 'elems': {'text': 'string'}},
                            null,
                            {'tag': 'td'}
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ph'}},
                            {'tag': 'td', 'elems': {'text': 'uuid'}},
                            null,
                            {'tag': 'td'}
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'tag': 'h2',
                    'attrs': {'id': 'name=test&struct_test_query'},
                    'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Query Parameters'}}
                },
                null,
                {'tag': 'table', 'elems': [
                    {'tag': 'tr', 'elems': [
                        {'tag': 'th', 'elems': {'text': 'Name'}},
                        {'tag': 'th', 'elems': {'text': 'Type'}},
                        {'tag': 'th', 'elems': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qa'}},
                            {'tag': 'td', 'elems': {'text': 'int'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qb'}},
                            {'tag': 'td', 'elems': {'text': 'int'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qc'}},
                            {'tag': 'td', 'elems': {'text': 'int'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qd'}},
                            {'tag': 'td', 'elems': {'text': 'float'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}>${chisel.nbsp}0.5`}},
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}<${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qe'}},
                            {'tag': 'td', 'elems': {'text': 'float'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}>=${chisel.nbsp}0.5`}},
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}<=${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qf'}},
                            {'tag': 'td', 'elems': {'text': 'float'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}==${chisel.nbsp}9.5`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qg'}},
                            {'tag': 'td', 'elems': {'text': 'string'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(value)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(value)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qh'}},
                            {'tag': 'td', 'elems': {'text': 'string'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(value)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(value)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qi'}},
                            {'tag': 'td', 'elems': {'text': 'string'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(value)${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qj'}},
                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qk'}},
                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ql'}},
                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': `${chisel.nbsp}[]`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qm'}},
                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}>${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}<${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qn'}},
                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}>=${chisel.nbsp}0`}},
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}<=${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'qo'}},
                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': `${chisel.nbsp}{}`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}==${chisel.nbsp}10`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'tag': 'h2',
                    'attrs': {'id': 'name=test&struct_test_input'},
                    'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Input Parameters'}}
                },
                null,
                {'tag': 'table', 'elems': [
                    {'tag': 'tr', 'elems': [
                        {'tag': 'th', 'elems': {'text': 'Name'}},
                        {'tag': 'th', 'elems': {'text': 'Type'}},
                        {'tag': 'th', 'elems': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ia'}},
                            {'tag': 'td', 'elems': {'text': 'int'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': 'optional'}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ib'}},
                            {'tag': 'td', 'elems': {'text': 'float'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': 'nullable'}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ic'}},
                            {'tag': 'td', 'elems': {'text': 'string'}},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': 'optional'}},
                                {'tag': 'li', 'elems': {'text': 'nullable'}}
                            ]}},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'id'}},
                            {'tag': 'td', 'elems': [{'text': 'string'}, {'text': `${chisel.nbsp}[]`}]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': 'optional'}},
                                {'tag': 'li', 'elems': {'text': 'nullable'}},
                                {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'tag': 'h2',
                    'attrs': {'id': 'name=test&struct_test_output'},
                    'elems': {'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Output Parameters'}, 'tag': 'a'}
                },
                null,
                {'tag': 'table', 'elems': [
                    {'tag': 'tr', 'elems': [
                        {'tag': 'th', 'elems': {'text': 'Name'}},
                        {'tag': 'th', 'elems': {'text': 'Type'}},
                        {'tag': 'th', 'elems': {'text': 'Attributes'}},
                        null
                    ]},
                    [
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'oa'}},
                            {'tag': 'td', 'elems': {
                                'tag': 'a',
                                'attrs': {'href': '#name=test&typedef_PositiveInt'},
                                'elems': {'text': 'PositiveInt'}
                            }},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'ob'}},
                            {'tag': 'td', 'elems': {
                                'tag': 'a',
                                'attrs': {'href': '#name=test&typedef_JustAString'},
                                'elems': {'text': 'JustAString'}
                            }},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'oc'}},
                            {'tag': 'td', 'elems': {
                                'tag': 'a',
                                'attrs': {'href': '#name=test&struct_Struct1'},
                                'elems': {'text': 'Struct1'}
                            }},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'od'}},
                            {'tag': 'td', 'elems': {
                                'tag': 'a',
                                'attrs': {'href': '#name=test&enum_Enum1'},
                                'elems': {'text': 'Enum1'}
                            }},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'oe'}},
                            {'tag': 'td', 'elems': {
                                'tag': 'a',
                                'attrs': {'href': '#name=test&enum_Enum2'},
                                'elems': {'text': 'Enum2'}
                            }},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'of'}},
                            {'tag': 'td', 'elems': [
                                [
                                    {'tag': 'a', 'attrs': {'href': '#name=test&enum_Enum1'}, 'elems': {'text': 'Enum1'}},
                                    {'text': `${chisel.nbsp}:${chisel.nbsp}`}
                                ],
                                {'text': 'string'}, {'text': `${chisel.nbsp}{}`}
                            ]},
                            {'tag': 'td'},
                            null
                        ]},
                        {'tag': 'tr', 'elems': [
                            {'tag': 'td', 'elems': {'text': 'og'}},
                            {'tag': 'td', 'elems': [
                                [
                                    {'tag': 'a', 'attrs': {'href': '#name=test&typedef_JustAString'}, 'elems': {'text': 'JustAString'}},
                                    {'text': `${chisel.nbsp}:${chisel.nbsp}`}
                                ],
                                {'tag': 'a', 'attrs': {'href': '#name=test&typedef_NonEmptyFloatArray'}, 'elems': {'text': 'NonEmptyFloatArray'}},
                                {'text': `${chisel.nbsp}{}`}
                            ]},
                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                {'tag': 'li', 'elems': {'text': `len(dict)${chisel.nbsp}>${chisel.nbsp}0`}}
                            ]}},
                            null
                        ]}
                    ]
                ]}
            ],
            [
                {
                    'tag': 'h2',
                    'attrs': {'id': 'name=test&enum_test_error'},
                    'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Error Codes'}}
                },
                null,
                {'tag': 'table', 'elems': [
                    {'tag': 'tr', 'elems': [{'tag': 'th', 'elems': {'text': 'Value'}}, null]},
                    [
                        {'tag': 'tr', 'elems': [{'tag': 'td', 'elems': {'text': 'Error1'}}, null]},
                        {'tag': 'tr', 'elems': [{'tag': 'td', 'elems': {'text': 'Error2'}}, null]}
                    ]
                ]}
            ],
            [
                {'tag': 'h2', 'elems': {'text': 'Typedefs'}},
                [
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&typedef_NonEmptyFloatArray'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef NonEmptyFloatArray'}}
                        },
                        null,
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [{'tag': 'th', 'elems': {'text': 'Type'}}, {'tag': 'th', 'elems': {'text': 'Attributes'}}]},
                            {'tag': 'tr', 'elems': [
                                {'tag': 'td', 'elems': [[{'text': 'float'}, {'text': `${chisel.nbsp}[]`}]]},
                                {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                    {'tag': 'li', 'elems': {'text': `len(array)${chisel.nbsp}>${chisel.nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ],
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&typedef_JustAString'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef JustAString'}}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' Just a string.'}},
                            {'tag': 'p', 'elems': {'text': ' More info.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [
                                {'tag': 'th', 'elems': {'text': 'Type'}},
                                null
                            ]},
                            {'tag': 'tr', 'elems': [
                                {'tag': 'td', 'elems': [{'text': 'string'}]},
                                null
                            ]}
                        ]}
                    ],
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&typedef_PositiveInt'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef PositiveInt'}}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' A positive integer.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [
                                {'tag': 'th', 'elems': {'text': 'Type'}},
                                {'tag': 'th', 'elems': {'text': 'Attributes'}}
                            ]},
                            {'tag': 'tr', 'elems': [
                                {'tag': 'td', 'elems': [{'text': 'int'}]},
                                {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-attr-list'}, 'elems': [
                                    {'tag': 'li', 'elems': {'text': `value${chisel.nbsp}>${chisel.nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ]
                ]
            ],
            [
                {'tag': 'h2', 'elems': {'text': 'Struct Types'}},
                [
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&struct_Struct1'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'struct Struct1'}}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' A struct.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [
                                {'tag': 'th', 'elems': {'text': 'Name'}},
                                {'tag': 'th', 'elems': {'text': 'Type'}},
                                null,
                                {'tag': 'th', 'elems': {'text': 'Description'}}
                            ]},
                            [
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'sa'}},
                                    {'tag': 'td', 'elems': {'text': 'int'}},
                                    null,
                                    {'tag': 'td', 'elems': [{'tag': 'p', 'elems': {'text': ' The struct member "sa"'}}]}
                                ]},
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'sb'}},
                                    {'tag': 'td', 'elems': {
                                        'tag': 'a', 'attrs': {'href': '#name=test&struct_Struct2'}, 'elems': {'text': 'Struct2'}
                                    }},
                                    null,
                                    {'tag': 'td', 'elems': [
                                        {'tag': 'p', 'elems': {'text': ' The struct member "sb"'}},
                                        {'tag': 'p', 'elems': {'text': ' More info.'}}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&struct_Struct2'},
                            'elems': {'attrs': {'class': 'linktarget'}, 'elems': {'text': 'union Struct2'}, 'tag': 'a'}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' Another struct, a union.'}},
                            {'tag': 'p', 'elems': {'text': ' More info.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [
                                {'tag': 'th', 'elems': {'text': 'Name'}},
                                {'tag': 'th', 'elems': {'text': 'Type'}},
                                null,
                                null
                            ]},
                            [
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'sa'}},
                                    {'tag': 'td', 'elems': {'text': 'string'}},
                                    null,
                                    null
                                ]},
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'sb'}},
                                    {'tag': 'td', 'elems': {'text': 'int'}},
                                    null,
                                    null
                                ]}
                            ]
                        ]}
                    ]
                ]
            ],
            [
                {'tag': 'h2', 'elems': {'text': 'Enum Types'}},
                [
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&enum_Enum1'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'enum Enum1'}}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' An enum.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [
                                {'tag': 'th', 'elems': {'text': 'Value'}},
                                {'tag': 'th', 'elems': {'text': 'Description'}}
                            ]},
                            [
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'e1'}},
                                    {'tag': 'td', 'elems': [{'tag': 'p', 'elems': {'text': ' The Enum1 value "e1"'}}]}
                                ]},
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'td', 'elems': {'text': 'e2'}},
                                    {'tag': 'td', 'elems': [
                                        {'tag': 'p', 'elems': {'text': ' The Enum1 value "e 2"'}},
                                        {'tag': 'p', 'elems': {'text': ' More info.'}}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'tag': 'h3',
                            'attrs': {'id': 'name=test&enum_Enum2'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'enum Enum2'}}
                        },
                        [
                            {'tag': 'p', 'elems': {'text': ' Another enum.'}},
                            {'tag': 'p', 'elems': {'text': ' More info.'}}
                        ],
                        {'tag': 'table', 'elems': [
                            {'tag': 'tr', 'elems': [{'tag': 'th', 'elems': {'text': 'Value'}}, null]},
                            [
                                {'tag': 'tr', 'elems': [{'tag': 'td', 'elems': {'text': 'e3'}}, null]}
                            ]
                        ]}
                    ]
                ]
            ]
        ]
    );
});
