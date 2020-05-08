import {DocPage} from '../src/doc.js';
import {XMLHttpRequestMock} from './testChisel.js';
import browserEnv from 'browser-env';
import test from 'ava';

/* eslint-disable id-length */
/* eslint-disable max-len */


// Add browser globals
browserEnv(['document', 'window']);


test('DocPage.render, index', (t) => {
    window.location.hash = '#';
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';

    // Do the render. Verify the XHR API call and that no render occurs (that happens on XHR callback)
    const docPage = new DocPage();
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    const [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_index']],
        ['send', []]
    ]);

    // Verify that the page doesn't render while loading
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');

    // Render the index page
    xhr.readyState = xhr.DONE;
    xhr.status = 200;
    xhr.response = {
        'title': 'My APIs',
        'groups': {
            'Documentation': ['chisel_doc_index', 'chisel_doc_request'],
            'Redirects': ['redirect_doc'],
            'Statics': ['static_chisel_js', 'static_doc_css', 'static_doc_html', 'static_doc_js']
        }
    };
    xhr.onreadystatechange();
    t.true(docPage.rendered);
    t.true(document.body.innerHTML.startsWith('<h1>My APIs</h1>'));
});

test('DocPage.render, index error', (t) => {
    window.location.hash = '#';
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';

    // Do the render. Verify the XHR API call and that no render occurs (that happens on XHR callback)
    const docPage = new DocPage();
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    const [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_index']],
        ['send', []]
    ]);

    // Verify that the page doesn't render while loading
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');

    // Render the index page
    xhr.readyState = xhr.DONE;
    xhr.status = 500;
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, 'An unexpected error occurred.');
});

test('DocPage.render, request', (t) => {
    window.location.hash = '#name=test';
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';

    // Do the render. Verify the XHR API call and that no render occurs (that happens on XHR callback)
    const docPage = new DocPage();
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    const [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_request?name=test']],
        ['send', []]
    ]);

    // Verify that the page doesn't render while loading
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');

    // Render the request page
    xhr.readyState = xhr.DONE;
    xhr.status = 200;
    xhr.response = {
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
    };
    xhr.onreadystatechange();
    t.true(docPage.rendered);
    t.true(document.body.innerHTML.startsWith('<div class="chisel-header">'));
});

test('DocPage.render, request error', (t) => {
    window.location.hash = '#name=test';
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';

    // Do the render. Verify the XHR API call and that no render occurs (that happens on XHR callback)
    const docPage = new DocPage();
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    const [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_request?name=test']],
        ['send', []]
    ]);

    // Verify that the page doesn't render while loading
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');

    // Render the request page
    xhr.readyState = xhr.DONE;
    xhr.status = 400;
    xhr.response = {'error': 'UnknownName'};
    xhr.onreadystatechange();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, 'Error: UnknownName');
});

test('DocPage.render, request avoid re-render', (t) => {
    window.location.hash = '#name=test';
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';

    // Do the render. Verify the XHR API call and that no render occurs (that happens on XHR callback)
    const docPage = new DocPage();
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    let [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_request?name=test']],
        ['send', []]
    ]);

    // Render the request page
    xhr.readyState = xhr.DONE;
    xhr.status = 200;
    xhr.response = {
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
    };
    xhr.onreadystatechange();
    t.true(docPage.rendered);
    t.true(document.body.innerHTML.startsWith('<div class="chisel-header">'));

    // Call render again with same name - it should not re-render since its already rendered
    XMLHttpRequestMock._reset();
    document.body.innerHTML = '';
    docPage.render();
    t.true(docPage.rendered);
    t.is(document.body.innerHTML, '');
    t.is(XMLHttpRequestMock._xhrs.length, 0);

    // Verify render when name is changed
    window.location.hash = '#name=test2';
    docPage.render();
    t.false(docPage.rendered);
    t.is(document.body.innerHTML, '');
    [xhr] = XMLHttpRequestMock._xhrs;
    t.is(xhr.readyState, xhr.LOADING);
    t.is(xhr.response, null);
    t.deepEqual(xhr._calls, [
        ['open', ['get', 'doc_request?name=test2']],
        ['send', []]
    ]);

    // Render the request page
    xhr.readyState = xhr.DONE;
    xhr.status = 200;
    xhr.response = {
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
    };
    xhr.onreadystatechange();
    t.true(docPage.rendered);
    t.true(document.body.innerHTML.startsWith('<div class="chisel-header">'));
});

test('DocPage.errorPage', (t) => {
    t.deepEqual(
        DocPage.errorPage({}),
        {'text': 'An unexpected error occurred.'}
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
                'tag': 'div',
                'attrs': {'class': 'chisel-header'},
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'empty'}},
            null,
            {'tag': 'div', 'attrs': {'class': 'chisel-notes'}, 'elems': [
                null,
                null,
                [
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=empty&struct_empty_path'},
                            'elems': {'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Path Parameters'}, 'tag': 'a'}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no path parameters.'}}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=empty&struct_empty_query'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Query Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no query parameters.'}}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=empty&struct_empty_input'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Input Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no input parameters.'}}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=empty&struct_empty_output'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Output Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no output parameters.'}}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=empty&enum_empty_error'},
                            'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Error Codes'}}]
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action returns no custom error codes.'}}
                        ]
                    ],
                    null,
                    null,
                    null
                ]
            ]}
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
                'query': {'name': 'wsgiResponse_query', 'members': [
                    {'name': 'a', 'type': {'builtin': 'int'}},
                    {'name': 'b', 'type': {'builtin': 'string'}}
                ]}
            }
        }),
        [
            {
                'tag': 'div',
                'attrs': {'class': 'chisel-header'},
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'wsgiResponse'}},
            null,
            {'tag': 'div', 'attrs': {'class': 'chisel-notes'}, 'elems': [
                {'tag': 'div', 'elems': [
                    {'tag': 'p', 'elems': [
                        {'tag': 'b', 'elems': {'text': 'Note: '}},
                        {'text': 'The request is exposed at the following URL:'},
                        {'tag': 'ul', 'elems': [
                            {'tag': 'li', 'elems': [{'tag': 'a', 'attrs': {'href': '/wsgiResponse'}, 'elems': {'text': 'POST /wsgiResponse'}}]}
                        ]}
                    ]}
                ]},
                {'tag': 'div', 'elems': [
                    {'tag': 'p', 'elems': [
                        {'tag': 'b', 'elems': {'text': 'Note: '}},
                        {'text': 'The action has a non-default response. See documentation for details.'}
                    ]}
                ]},
                [
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=wsgiResponse&struct_wsgiResponse_path'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Path Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no path parameters.'}}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=wsgiResponse&struct_wsgiResponse_query'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Query Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'table', 'elems': [
                                {'tag': 'tr', 'elems': [
                                    {'tag': 'th', 'elems': {'text': 'Name'}},
                                    {'tag': 'th', 'elems': {'text': 'Type'}},
                                    null,
                                    null
                                ]},
                                [
                                    {'tag': 'tr', 'elems': [
                                        {'tag': 'td', 'elems': {'text': 'a'}},
                                        {'tag': 'td', 'elems': {'text': 'int'}},
                                        null,
                                        null
                                    ]},
                                    {'tag': 'tr', 'elems': [
                                        {'tag': 'td', 'elems': {'text': 'b'}},
                                        {'tag': 'td', 'elems': {'text': 'string'}},
                                        null,
                                        null
                                    ]}
                                ]
                            ]}
                        ]
                    ],
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=wsgiResponse&struct_wsgiResponse_input'},
                            'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Input Parameters'}}
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action has no input parameters.'}}
                        ]
                    ],
                    null,
                    [
                        {
                            'tag': 'h2',
                            'attrs': {'id': 'name=wsgiResponse&enum_wsgiResponse_error'},
                            'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Error Codes'}}]
                        },
                        null,
                        [
                            {'tag': 'p', 'elems': {'text': 'The action returns no custom error codes.'}}
                        ]
                    ],
                    null,
                    null,
                    null
                ]
            ]}
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
                'tag': 'div',
                'attrs': {'class': 'chisel-header'},
                'elems': {'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}}
            },
            {'tag': 'h1', 'elems': {'text': 'request'}},
            null,
            {'tag': 'div', 'attrs': {'class': 'chisel-notes'}, 'elems': [
                {'tag': 'div', 'elems': [
                    {'tag': 'p', 'elems': [
                        {'tag': 'b', 'elems': {'text': 'Note: '}},
                        {'text': 'The request is exposed at the following URL:'},
                        {'tag': 'ul', 'elems': [
                            {'tag': 'li', 'elems': [{'tag': 'a', 'attrs': {'href': '/request'}, 'elems': {'text': '/request'}}]}
                        ]}
                    ]}
                ]},
                null,
                null
            ]}
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
            'doc': [' The test action.', '', ' This is some more information.'],
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
                        {'name': 'pa', 'type': {'builtin': 'bool'}, 'doc': [' The url member "pa".']},
                        {'name': 'pb', 'type': {'builtin': 'date'}, 'doc': [' The url member "pb".', '', ' More info.', '']},
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
                    'doc': [' An enum.'],
                    'values': [
                        {'value': 'e1', 'doc': [' The Enum1 value "e1"']},
                        {'value': 'e2', 'doc': [' The Enum1 value "e 2"', '', ' More info.']}
                    ]
                },
                {
                    'name': 'Enum2',
                    'doc': [' Another enum.', '', ' More info.'],
                    'values': [
                        {'value': 'e3'}
                    ]
                }
            ],
            'structs': [
                {
                    'name': 'Struct1',
                    'doc': [' A struct.'],
                    'members': [
                        {'name': 'sa', 'type': {'builtin': 'int'}, 'doc': [' The struct member "sa"']},
                        {'name': 'sb', 'type': {'struct': 'Struct2'}, 'doc': [' The struct member "sb"', '', ' More info.']}
                    ]
                },
                {
                    'name': 'Struct2',
                    'doc': [' Another struct, a union.', '', ' More info.'],
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
                    'doc': [' Just a string.', '', ' More info.'],
                    'type': {'builtin': 'string'}
                },
                {'name': 'PositiveInt', 'type': {'builtin': 'int'}, 'attr': {'gt': 0.0}, 'doc': [' A positive integer.']}
            ]
        }),
        // =================
        // Begin requestPage
        // =================
        [
            {'tag': 'div', 'attrs': {'class': 'chisel-header'}, 'elems': {
                'tag': 'a', 'attrs': {'href': 'blank#'}, 'elems': {'text': 'Back to documentation index'}
            }},
            {'tag': 'h1', 'elems': {'text': 'test'}},
            [
                {'tag': 'p', 'elems': {'text': ' The test action.'}},
                {'tag': 'p', 'elems': {'text': ' This is some more information.'}}
            ],
            {
                'attrs': {'class': 'chisel-notes'},
                'elems': [
                    {'tag': 'div', 'elems': [
                        {'tag': 'p', 'elems': [
                            {'tag': 'b', 'elems': {'text': 'Note: '}},
                            {'text': 'The request is exposed at the following URLs:'},
                            {'tag': 'ul', 'elems': [
                                {'tag': 'li', 'elems': [{'attrs': {'href': '/test'}, 'elems': {'text': '/test'}, 'tag': 'a'}]},
                                {'tag': 'li', 'elems': [{'attrs': {'href': '/test'}, 'elems': {'text': 'GET /test'}, 'tag': 'a'}]},
                                {'tag': 'li', 'elems': [{'attrs': {'href': '/'}, 'elems': {'text': 'GET /'}, 'tag': 'a'}]}
                            ]}
                        ]}
                    ]},
                    null,
                    [
                        [
                            {
                                'tag': 'h2',
                                'attrs': {'id': 'name=test&struct_test_path'},
                                'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Path Parameters'}}
                            },
                            null,
                            [
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
                            ]
                        ],
                        [
                            {
                                'tag': 'h2',
                                'attrs': {'id': 'name=test&struct_test_query'},
                                'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Query Parameters'}}
                            },
                            null,
                            [
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
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' > 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' < 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qb'}},
                                            {'tag': 'td', 'elems': {'text': 'int'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' >= 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' <= 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qc'}},
                                            {'tag': 'td', 'elems': {'text': 'int'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' == 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qd'}},
                                            {'tag': 'td', 'elems': {'text': 'float'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}, 'tag': 'span'},
                                                        {'text': ' > 0.5'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' < 9.5'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qe'}},
                                            {'tag': 'td', 'elems': {'text': 'float'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' >= 0.5'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' <= 9.5'}
                                                    ]
                                                    }
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qf'}},
                                            {'tag': 'td', 'elems': {'text': 'float'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' == 9.5'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qg'}},
                                            {'tag': 'td', 'elems': {'text': 'string'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(value)'}},
                                                        {'text': ' > 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(value)'}},
                                                        {'text': ' < 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qh'}},
                                            {'tag': 'td', 'elems': {'text': 'string'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(value)'}},
                                                        {'text': ' >= 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(value)'}},
                                                        {'text': ' <= 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qi'}},
                                            {'tag': 'td', 'elems': {'text': 'string'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(value)'}},
                                                        {'text': ' == 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qj'}},
                                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': ' []'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' > 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' < 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qk'}},
                                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': ' []'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' >= 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}, 'tag': 'span'},
                                                        {'text': ' <= 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'ql'}},
                                            {'tag': 'td', 'elems': [{'text': 'int'}, {'text': ' []'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' >= 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}, 'tag': 'span'},
                                                        {'text': ' <= 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qm'}},
                                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': ' {}'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}, 'tag': 'span'},
                                                        {'text': ' > 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}, 'tag': 'span'},
                                                        {'text': ' < 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qn'}},
                                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': ' {}'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}},
                                                        {'text': ' >= 0'}
                                                    ]},
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}, 'tag': 'span'},
                                                        {'text': ' <= 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'qo'}},
                                            {'tag': 'td', 'elems': [null, {'text': 'string'}, {'text': ' {}'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}, 'tag': 'span'},
                                                        {'text': ' == 10'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]}
                                    ]
                                ]}
                            ]
                        ],
                        [
                            {
                                'tag': 'h2',
                                'attrs': {'id': 'name=test&struct_test_input'},
                                'elems': {'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Input Parameters'}}
                            },
                            null,
                            [
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
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                {'tag': 'li', 'elems': [
                                                    {'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'optional'}, 'tag': 'span'},
                                                    null
                                                ]},
                                                null,
                                                []
                                            ]}
                                            },
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'ib'}},
                                            {'tag': 'td', 'elems': {'text': 'float'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                {'tag': 'li', 'elems': [
                                                    {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'nullable'}},
                                                    null
                                                ]},
                                                []
                                            ]}
                                            },
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'ic'}},
                                            {'tag': 'td', 'elems': {'text': 'string'}},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                {'tag': 'li', 'elems': [
                                                    {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'optional'}},
                                                    null
                                                ]},
                                                {'tag': 'li', 'elems': [
                                                    {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'nullable'}},
                                                    null
                                                ]},
                                                []
                                            ]}},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'id'}},
                                            {'tag': 'td', 'elems': [{'text': 'string'}, {'text': ' []'}]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                {'tag': 'li', 'elems': [
                                                    {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'optional'}},
                                                    null
                                                ]},
                                                {'tag': 'li', 'elems': [
                                                    {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'nullable'}},
                                                    null
                                                ]},
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' > 0'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]}
                                    ]
                                ]}
                            ]
                        ],
                        [
                            {
                                'tag': 'h2',
                                'attrs': {'id': 'name=test&struct_test_output'},
                                'elems': {'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Output Parameters'}, 'tag': 'a'}
                            },
                            null,
                            [
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
                                                    {'text': ' : '}
                                                ],
                                                {'text': 'string'}, {'text': ' {}'}
                                            ]},
                                            {'tag': 'td'},
                                            null
                                        ]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': {'text': 'og'}},
                                            {'tag': 'td', 'elems': [
                                                [
                                                    {'tag': 'a', 'attrs': {'href': '#name=test&typedef_JustAString'}, 'elems': {'text': 'JustAString'}},
                                                    {'text': ' : '}
                                                ],
                                                {'tag': 'a', 'attrs': {'href': '#name=test&typedef_NonEmptyFloatArray'}, 'elems': {'text': 'NonEmptyFloatArray'}},
                                                {'text': ' {}'}
                                            ]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(dict)'}},
                                                        {'text': ' > 0'}
                                                    ]}
                                                ]
                                            ]}},
                                            null
                                        ]}
                                    ]
                                ]}
                            ]
                        ],
                        [
                            {
                                'tag': 'h2',
                                'attrs': {'id': 'name=test&enum_test_error'},
                                'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'Error Codes'}}]
                            },
                            null,
                            [
                                {'tag': 'table', 'elems': [
                                    {'tag': 'tr', 'elems': [{'tag': 'th', 'elems': {'text': 'Value'}}, null]},
                                    [
                                        {'tag': 'tr', 'elems': [{'tag': 'td', 'elems': {'text': 'Error1'}}, null]},
                                        {'tag': 'tr', 'elems': [{'tag': 'td', 'elems': {'text': 'Error2'}}, null]}
                                    ]
                                ]}
                            ]
                        ],
                        [
                            {'tag': 'h2', 'elems': {'text': 'Typedefs'}},
                            [
                                [
                                    {
                                        'tag': 'h3',
                                        'attrs': {'id': 'name=test&typedef_NonEmptyFloatArray'},
                                        'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef NonEmptyFloatArray'}}]
                                    },
                                    null,
                                    {'tag': 'table', 'elems': [
                                        {'tag': 'tr', 'elems': [{'tag': 'th', 'elems': {'text': 'Type'}}, {'tag': 'th', 'elems': {'text': 'Attributes'}}]},
                                        {'tag': 'tr', 'elems': [
                                            {'tag': 'td', 'elems': [[{'text': 'float'}, {'text': ' []'}]]},
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'len(array)'}},
                                                        {'text': ' > 0'}
                                                    ]}
                                                ]
                                            ]}}
                                        ]}
                                    ]}
                                ],
                                [
                                    {
                                        'tag': 'h3',
                                        'attrs': {'id': 'name=test&typedef_JustAString'},
                                        'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef JustAString'}}]
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
                                        'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'typedef PositiveInt'}}]
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
                                            {'tag': 'td', 'elems': {'tag': 'ul', 'attrs': {'class': 'chisel-constraint-list'}, 'elems': [
                                                null,
                                                null,
                                                [
                                                    {'tag': 'li', 'elems': [
                                                        {'tag': 'span', 'attrs': {'class': 'chisel-emphasis'}, 'elems': {'text': 'value'}},
                                                        {'text': ' > 0'}
                                                    ]}
                                                ]
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
                                    [
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
                                    ]
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
                                    [
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
                            ]
                        ],
                        [
                            {'tag': 'h2', 'elems': {'text': 'Enum Types'}},
                            [
                                [
                                    {
                                        'tag': 'h3',
                                        'attrs': {'id': 'name=test&enum_Enum1'},
                                        'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'enum Enum1'}}]
                                    },
                                    [
                                        {'tag': 'p', 'elems': {'text': ' An enum.'}}
                                    ],
                                    [
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
                                    ]
                                ],
                                [
                                    {
                                        'tag': 'h3',
                                        'attrs': {'id': 'name=test&enum_Enum2'},
                                        'elems': [{'tag': 'a', 'attrs': {'class': 'linktarget'}, 'elems': {'text': 'enum Enum2'}}]
                                    },
                                    [
                                        {'tag': 'p', 'elems': {'text': ' Another enum.'}},
                                        {'tag': 'p', 'elems': {'text': ' More info.'}}
                                    ],
                                    [
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
                    ]
                ],
                'tag': 'div'
            }
        ]
    );
});
