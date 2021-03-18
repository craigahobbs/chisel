// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/* eslint-disable id-length */
/* eslint-disable max-len */

import {DocPage} from '../src/doc.js';
import browserEnv from 'browser-env';
import {nbsp} from '../src/elementModel/util.js';
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


test('DocPage.run, type model URL', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'title': 'All the Types',
                'types': {
                    'MyStruct': {
                        'struct': {
                            'name': 'MyStruct'
                        }
                    }
                }
            }
        }
    ]);

    // Run the application
    const docPage = new DocPage('types.json');
    docPage.render();
    t.is(document.title, 'All the Types');
    t.true(document.body.innerHTML.startsWith('<h1>All the Types</h1>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['types.json', undefined],
        'resource response.json'
    ]);
});


test('DocPage.run, type model URL error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'ok': false,
            'statusText': 'Not Found',
            'json': {}
        }
    ]);

    // Run the application
    const docPage = new DocPage('types.json');
    docPage.render();
    t.is(document.title, 'Error');
    t.true(document.body.innerHTML.startsWith("<p>Error: Could not fetch type mode 'types.json': Not Found</p>"));
    t.deepEqual(WindowFetchMock.calls, [
        ['types.json', undefined]
    ]);
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


test('DocPage.render, request with url', (t) => {
    window.location.hash = '#name=MyAction&url=types.json';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'title': 'My Type Model',
                'types': {
                    'MyAction': {
                        'action': {
                            'name': 'MyAction',
                            'query': 'MyAction_query',
                            'urls': [
                                {'method': 'GET', 'path': '/simple'}
                            ]
                        }
                    },
                    'MyAction_query': {
                        'struct': {
                            'name': 'MyAction_query',
                            'members': [
                                {'name': 'a', 'type': {'builtin': 'int'}},
                                {'name': 'b', 'type': {'builtin': 'int'}}
                            ]
                        }
                    }
                }
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage();
    docPage.render();
    t.is(document.title, 'MyAction');
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, [
        ['types.json', undefined],
        'resource response.json'
    ]);
});


test('DocPage.render, request with type model', (t) => {
    window.location.hash = '#name=MyAction';
    document.body.innerHTML = '';
    WindowFetchMock.reset([]);
    const typeModel = {
        'title': 'My Type Model',
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'query': 'MyAction_query',
                    'urls': [
                        {'method': 'GET', 'path': '/simple'}
                    ]
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query',
                    'members': [
                        {'name': 'a', 'type': {'builtin': 'int'}},
                        {'name': 'b', 'type': {'builtin': 'int'}}
                    ]
                }
            }
        }
    };

    // Do the render
    const docPage = new DocPage(typeModel);
    docPage.render();
    t.is(document.title, 'MyAction');
    t.true(document.body.innerHTML.startsWith('<p>'));
    t.deepEqual(WindowFetchMock.calls, []);
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


test('DocPage.render, type model URL index', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([
        {
            'json': {
                'title': 'All the Types',
                'types': {
                    'MyAction': {
                        'action': {
                            'name': 'MyAction'
                        }
                    },
                    'MyAction2': {
                        'action': {
                            'name': 'MyAction2',
                            'docGroup': 'Stuff'
                        }
                    },
                    'MyStruct': {
                        'struct': {
                            'name': 'MyStruct'
                        }
                    },
                    'MyStruct2': {
                        'struct': {
                            'name': 'MyStruct2',
                            'docGroup': 'Stuff'
                        }
                    },
                    'MyEnum': {
                        'enum': {
                            'name': 'MyEnum'
                        }
                    },
                    'MyEnum2': {
                        'enum': {
                            'name': 'MyEnum2',
                            'docGroup': 'Stuff'
                        }
                    },
                    'MyTypedef': {
                        'typedef': {
                            'name': 'MyTypedef',
                            'type': {'builtin': 'int'}
                        }
                    },
                    'MyTypedef2': {
                        'typedef': {
                            'name': 'MyTypedef2',
                            'docGroup': 'Stuff',
                            'type': {'builtin': 'int'}
                        }
                    }
                }
            }
        }
    ]);

    // Do the render
    const docPage = new DocPage('types.json');
    docPage.render();
    t.is(document.title, 'All the Types');
    t.deepEqual(
        document.body.innerHTML,
        '<h1>All the Types</h1>' +
            '<h2>Enumerations</h2><ul class="chisel-index-list"><li><ul>' +
            '<li><a href="blank#name=MyEnum">MyEnum</a></li>' +
            '</ul></li></ul>' +
            '<h2>Structs</h2><ul class="chisel-index-list"><li><ul>' +
            '<li><a href="blank#name=MyStruct">MyStruct</a></li>' +
            '</ul></li></ul>' +
            '<h2>Stuff</h2><ul class="chisel-index-list"><li><ul>' +
            '<li><a href="blank#name=MyAction2">MyAction2</a></li>' +
            '<li><a href="blank#name=MyEnum2">MyEnum2</a></li>' +
            '<li><a href="blank#name=MyStruct2">MyStruct2</a></li>' +
            '<li><a href="blank#name=MyTypedef2">MyTypedef2</a></li>' +
            '</ul></li></ul>' +
            '<h2>Typedefs</h2><ul class="chisel-index-list"><li><ul>' +
            '<li><a href="blank#name=MyTypedef">MyTypedef</a></li>' +
            '</ul></li></ul>' +
            '<h2>Uncategorized</h2><ul class="chisel-index-list"><li><ul>' +
            '<li><a href="blank#name=MyAction">MyAction</a></li></ul></li>' +
            '</ul>'
    );
    t.deepEqual(WindowFetchMock.calls, [
        ['types.json', undefined],
        'resource response.json'
    ]);
});


test('DocPage.render, type model unknown type', (t) => {
    window.location.hash = '#name=Unknown';
    document.body.innerHTML = '';
    WindowFetchMock.reset([]);
    const typeModel = {
        'title': 'All the Types',
        'types': {
            'MyStruct': {
                'struct': {
                    'name': 'MyStruct'
                }
            }
        }
    };

    // Do the render
    const docPage = new DocPage(typeModel);
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, "<p>Error: Unknown type name 'Unknown'</p>");
    t.deepEqual(WindowFetchMock.calls, []);
});


test('DocPage.render, type model URL index error', (t) => {
    window.location.hash = '#';
    document.body.innerHTML = '';
    WindowFetchMock.reset([{'error': true}]);

    // Do the render
    const docPage = new DocPage('types.json');
    docPage.render();
    t.is(document.title, 'Error');
    t.is(document.body.innerHTML, '<p>Error: Unexpected error</p>');
    t.deepEqual(WindowFetchMock.calls, [
        ['types.json', undefined]
    ]);
});


test('DocPage.errorPage', (t) => {
    t.deepEqual(
        DocPage.errorPage('Ouch!'),
        {'html': 'p', 'elem': {'text': 'Error: Ouch!'}}
    );
});


test('DocPage.indexPage', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('#');
    const index = {
        'title': 'The Title',
        'groups': {
            'B Group': ['name3', 'name4'],
            'C Group': ['name5'],
            'A Group': ['name2', 'name1']
        }
    };
    t.deepEqual(
        docPage.indexPage(index),
        [
            {'html': 'h1', 'elem': {'text': 'The Title'}},
            [
                [
                    {'html': 'h2', 'elem': {'text': 'A Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-index-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name1'}, 'elem': {'text': 'name1'}}},
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name2'}, 'elem': {'text': 'name2'}}}
                    ]}}}
                ],
                [
                    {'html': 'h2', 'elem': {'text': 'B Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-index-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name3'}, 'elem': {'text': 'name3'}}},
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name4'}, 'elem': {'text': 'name4'}}}
                    ]}}}
                ],
                [
                    {'html': 'h2', 'elem': {'text': 'C Group'}},
                    {'html': 'ul', 'attr': {'class': 'chisel-index-list'}, 'elem': {'html': 'li', 'elem': {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': {'html': 'a', 'attr': {'href': 'blank#name=name5'}, 'elem': {'text': 'name5'}}}
                    ]}}}
                ]
            ]
        ]
    );
});


test('DocPage.userTypeElem, empty struct', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=test');
    const types = {
        'MyStruct': {
            'struct': {
                'name': 'MyStruct'
            }
        }
    };
    t.deepEqual(
        docPage.userTypeElem(types, 'MyStruct', null, 'h1'),
        [
            {
                'html': 'h1',
                'attr': {'id': 'name=test&type_MyStruct'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'struct MyStruct'}}
            },
            null,
            [
                {'html': 'p', 'elem': [{'text': 'The struct is empty.'}]}
            ]
        ]
    );
});


test('DocPage.userTypeElem, empty enum', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=test');
    const types = {
        'MyEnum': {
            'enum': {
                'name': 'MyEnum'
            }
        }
    };
    t.deepEqual(
        docPage.userTypeElem(types, 'MyEnum', null, 'h1'),
        [
            {
                'html': 'h1',
                'attr': {'id': 'name=test&type_MyEnum'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum MyEnum'}}
            },
            null,
            null,
            [
                {'html': 'p', 'elem': [{'text': 'The enum is empty.'}]}
            ]
        ]
    );
});


test('DocPage.userTypeElem, empty typedef', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=test');
    const types = {
        'MyTypedef': {
            'typedef': {
                'name': 'MyTypedef',
                'type': {'builtin': 'int'}
            }
        }
    };
    t.deepEqual(
        docPage.userTypeElem(types, 'MyTypedef', null, 'h1'),
        [
            {
                'html': 'h1',
                'attr': {'id': 'name=test&type_MyTypedef'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef MyTypedef'}}
            },
            null,
            {
                'html': 'table',
                'elem': [
                    {
                        'html': 'tr',
                        'elem': [
                            {'html': 'th', 'elem': {'text': 'Type'}},
                            null
                        ]
                    },
                    {
                        'html': 'tr',
                        'elem': [
                            {'html': 'td', 'elem': {'text': 'int'}},
                            null
                        ]
                    }
                ]
            }
        ]
    );
});


const emptyActionErrorElements = [
    {
        'html': 'h2',
        'attr': {'id': 'name=MyAction&type_MyAction_errors'},
        'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Error Codes'}}
    },
    null,
    [
        {'html': 'p', 'elem': [{'text': 'If an application error occurs, the response is of the form:'}]},
        {'html': 'pre', 'elem': {'html': 'code', 'elem': [
            {'text': '{\n'},
            {'text': '    "error": "<code>",\n'},
            {'text': '    "message": "<message>"\n'},
            {'text': '}\n'}
        ]}},
        {'html': 'p', 'elem': [{'text': '"message" is optional. "<code>" is one of the following values:'}]}
    ],
    {
        'html': 'table',
        'elem': [
            {'html': 'tr', 'elem': [
                {'html': 'th', 'elem': {'text': 'Value'}},
                {'html': 'th', 'elem': {'text': 'Description'}}
            ]},
            [
                {'html': 'tr', 'elem': [
                    {'html': 'td', 'elem': {'text': 'UnexpectedError'}},
                    {'html': 'td', 'elem': [
                        {'html': 'p', 'elem': [{'text': 'An unexpected error occurred while processing the request'}]}
                    ]}
                ]}
            ]
        ]
    }
];


test('DocPage.userTypeElem, empty action with URLs', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=MyAction');
    const types = {
        'MyAction': {
            'action': {
                'name': 'MyAction',
                'urls': [
                    {},
                    {'method': 'GET'},
                    {'path': '/my_action'},
                    {'method': 'GET', 'path': '/my_alias'}
                ]
            }
        }
    };
    t.deepEqual(
        docPage.userTypeElem(types, 'MyAction', null, 'h1'),
        [
            {
                'html': 'h1',
                'attr': {'id': 'name=MyAction&type_MyAction'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'action MyAction'}}
            },
            null,
            {
                'html': 'p',
                'attr': {'class': 'chisel-note'},
                'elem': [
                    {'html': 'b', 'elem': {'text': 'Note: '}},
                    {'text': 'The request is exposed at the following URLs:'},
                    {
                        'html': 'ul',
                        'elem': [
                            {'html': 'li', 'elem': [{'html': 'a', 'attr': {'href': '/MyAction'}, 'elem': {'text': '/MyAction'}}]},
                            {'html': 'li', 'elem': [{'attr': {'href': '/MyAction'}, 'elem': {'text': 'GET /MyAction'}, 'html': 'a'}]},
                            {'html': 'li', 'elem': [{'attr': {'href': '/my_action'}, 'elem': {'text': '/my_action'}, 'html': 'a'}]},
                            {'html': 'li', 'elem': [{'attr': {'href': '/my_alias'}, 'elem': {'text': 'GET /my_alias'}, 'html': 'a'}]}
                        ]
                    }
                ]
            },
            null,
            null,
            null,
            null,
            emptyActionErrorElements
        ]
    );
    t.deepEqual(
        docPage.userTypeElem(types, 'MyAction', [{'method': 'GET', 'url': '/my_action'}], 'h1'),
        [
            {
                'html': 'h1',
                'attr': {'id': 'name=MyAction&type_MyAction'},
                'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'action MyAction'}}
            },
            null,
            {
                'html': 'p',
                'attr': {'class': 'chisel-note'},
                'elem': [
                    {'html': 'b', 'elem': {'text': 'Note: '}},
                    {'text': 'The request is exposed at the following URL:'},
                    {
                        'html': 'ul',
                        'elem': [
                            {'html': 'li', 'elem': [{'attr': {'href': '/my_action'}, 'elem': {'text': 'GET /my_action'}, 'html': 'a'}]}
                        ]
                    }
                ]
            },
            null,
            null,
            null,
            null,
            emptyActionErrorElements
        ]
    );
});


test('DocPage.userTypeElem, unknown', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=test');
    const types = {
        'MyTypedef': {}
    };
    t.deepEqual(
        docPage.userTypeElem(types, 'MyTypedef', null, 'h1'),
        null
    );
});


test('DocPage.requestPage, request', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=request');
    t.deepEqual(
        docPage.requestPage({'name': 'request', 'doc': 'This is my request', 'urls': [{'url': '/request'}]}),
        [
            {
                'html': 'p',
                'elem': {'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}}
            },
            [
                {'html': 'h1', 'elem': {'text': 'request'}},
                [
                    {'html': 'p', 'elem': [{'text': 'This is my request'}]}
                ],
                {'html': 'p', 'attr': {'class': 'chisel-note'}, 'elem': [
                    {'html': 'b', 'elem': {'text': 'Note: '}},
                    {'text': 'The request is exposed at the following URL:'},
                    {'html': 'ul', 'elem': [
                        {'html': 'li', 'elem': [{'html': 'a', 'attr': {'href': '/request'}, 'elem': {'text': '/request'}}]}
                    ]}
                ]}
            ],
            null
        ]
    );
});


test('DocPage.requestPage, request with no doc or urls', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=request');
    t.deepEqual(
        docPage.requestPage({'name': 'request'}),
        [
            {
                'html': 'p',
                'elem': {'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}}
            },
            [
                {'html': 'h1', 'elem': {'text': 'request'}},
                null,
                null
            ],
            null
        ]
    );
});


test('DocPage.requestPage', (t) => {
    const docPage = new DocPage();
    docPage.updateParams('name=MyAction');
    const request = {
        'name': 'MyAction',
        'urls': [
            {'url': '/test'},
            {'method': 'GET', 'url': '/test'},
            {'method': 'GET', 'url': '/'}
        ],
        'types': {
            'MyAction': {
                'action': {
                    'name': 'MyAction',
                    'doc': 'The test action.\n\nThis is some more information.',
                    'path': 'MyAction_path',
                    'query': 'MyAction_query',
                    'input': 'MyAction_input',
                    'output': 'MyAction_output',
                    'errors': 'MyAction_errors'
                }
            },
            'MyAction_path': {
                'struct': {
                    'name': 'MyAction_path',
                    'members': [
                        {'name': 'pa', 'type': {'builtin': 'bool'}, 'doc': 'The url member "pa".'},
                        {'name': 'pb', 'type': {'builtin': 'date'}, 'doc': 'The url member "pb".\n\n\nMore info.\n'},
                        {'name': 'pc', 'type': {'builtin': 'datetime'}},
                        {'name': 'pd', 'type': {'builtin': 'float'}},
                        {'name': 'pe', 'type': {'builtin': 'int'}},
                        {'name': 'pf', 'type': {'builtin': 'object'}},
                        {'name': 'pg', 'type': {'builtin': 'string'}},
                        {'name': 'ph', 'type': {'builtin': 'uuid'}}
                    ]
                }
            },
            'MyAction_query': {
                'struct': {
                    'name': 'MyAction_query',
                    'members': [
                        {'name': 'qa', 'type': {'builtin': 'int'}, 'attr': {'gt': 0.0, 'lt': 10.0}},
                        {'name': 'qb', 'type': {'builtin': 'int'}, 'attr': {'gte': 0.0, 'lte': 10.0}},
                        {'name': 'qc', 'type': {'builtin': 'int'}, 'attr': {'eq': 10.0}},
                        {'name': 'qd', 'type': {'builtin': 'float'}, 'attr': {'gt': 0.5, 'lt': 9.5}},
                        {'name': 'qe', 'type': {'builtin': 'float'}, 'attr': {'gte': 0.5, 'lte': 9.5}},
                        {'name': 'qf', 'type': {'builtin': 'float'}, 'attr': {'eq': 9.5}},
                        {'name': 'qg', 'type': {'builtin': 'string'}, 'attr': {'lenGT': 0, 'lenLT': 10}},
                        {'name': 'qh', 'type': {'builtin': 'string'}, 'attr': {'lenGTE': 0, 'lenLTE': 10}},
                        {'name': 'qi', 'type': {'builtin': 'string'}, 'attr': {'lenEq': 10}},
                        {'name': 'qj', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'lenGT': 0, 'lenLT': 10}},
                        {'name': 'qk', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'lenGTE': 0, 'lenLTE': 10}},
                        {'name': 'ql', 'type': {'array': {'type': {'builtin': 'int'}}}, 'attr': {'lenGTE': 0, 'lenLTE': 10}},
                        {
                            'name': 'qm',
                            'type': {'dict': {'type': {'builtin': 'string'}}},
                            'attr': {'lenGT': 0, 'lenLT': 10}
                        },
                        {
                            'name': 'qn',
                            'type': {'dict': {'type': {'builtin': 'string'}}},
                            'attr': {'lenGTE': 0, 'lenLTE': 10}
                        },
                        {
                            'name': 'qo',
                            'type': {'dict': {'type': {'builtin': 'string'}}},
                            'attr': {'lenEq': 10}
                        }
                    ]
                }
            },
            'MyAction_input': {
                'struct': {
                    'name': 'MyAction_input',
                    'members': [
                        {'name': 'ia', 'optional': true, 'type': {'builtin': 'int'}},
                        {'name': 'ib', 'type': {'builtin': 'float'}, 'attr': {'nullable': true}},
                        {'name': 'ic', 'optional': true, 'type': {'builtin': 'string'}, 'attr': {'nullable': true}},
                        {
                            'name': 'id',
                            'optional': true,
                            'type': {'array': {'attr': {'lenGT': 5}, 'type': {'builtin': 'string'}}},
                            'attr': {'nullable': true, 'lenGT': 0}
                        }
                    ]
                }
            },
            'MyAction_output': {
                'struct': {
                    'name': 'MyAction_output',
                    'members': [
                        {'name': 'oa', 'type': {'user': 'PositiveInt'}},
                        {'name': 'ob', 'type': {'user': 'JustAString'}},
                        {'name': 'oc', 'type': {'user': 'Struct1'}},
                        {'name': 'od', 'type': {'user': 'Enum1'}},
                        {'name': 'oe', 'type': {'user': 'Enum2'}},
                        {'name': 'of', 'type': {'dict': {'keyType': {'user': 'Enum1'}, 'type': {'builtin': 'string'}}}},
                        {
                            'name': 'og',
                            'type': {'dict': {'keyType': {'user': 'JustAString'}, 'type': {'user': 'NonEmptyFloatArray'}}},
                            'attr': {'lenGT': 0}
                        }
                    ]
                }
            },
            'MyAction_errors': {
                'enum': {
                    'name': 'MyAction_errors',
                    'values': [
                        {'name': 'Error1'},
                        {'name': 'Error2'}
                    ]
                }
            },
            'Enum1': {
                'enum': {
                    'name': 'Enum1',
                    'doc': 'An enum.',
                    'values': [
                        {'name': 'e1', 'doc': 'The Enum1 value "e1"'},
                        {'name': 'e2', 'doc': 'The Enum1 value "e 2"\n\nMore info.'}
                    ]
                }
            },
            'Enum2': {
                'enum': {
                    'name': 'Enum2',
                    'doc': 'Another enum.\n\nMore info.',
                    'values': [
                        {'name': 'e3'}
                    ]
                }
            },
            'Struct1': {
                'struct': {
                    'name': 'Struct1',
                    'doc': 'A struct.',
                    'members': [
                        {'name': 'sa', 'type': {'builtin': 'int'}, 'doc': 'The struct member "sa"'},
                        {'name': 'sb', 'type': {'user': 'Struct2'}, 'doc': 'The struct member "sb"\n\nMore info.'}
                    ]
                }
            },
            'Struct2': {
                'struct': {
                    'name': 'Struct2',
                    'doc': 'Another struct, a union.\n\nMore info.',
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
                    'attr': {'lenGT': 0}
                }
            },
            'JustAString': {
                'typedef': {
                    'name': 'JustAString',
                    'doc': 'Just a string.\n\nMore info.',
                    'type': {'builtin': 'string'}
                }
            },
            'PositiveInt': {
                'typedef': {
                    'name': 'PositiveInt',
                    'doc': 'A positive integer.',
                    'type': {'builtin': 'int'},
                    'attr': {'gt': 0.0}
                }
            }
        }
    };
    t.deepEqual(
        docPage.requestPage(request),
        [
            {
                'html': 'p',
                'elem': {'html': 'a', 'attr': {'href': 'blank#'}, 'elem': {'text': 'Back to documentation index'}}
            },
            [
                {
                    'html': 'h1',
                    'attr': {'id': 'name=MyAction&type_MyAction'},
                    'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'MyAction'}}
                },
                [
                    {'html': 'p', 'elem': [{'text': 'The test action.'}]},
                    {'html': 'p', 'elem': [{'text': 'This is some more information.'}]}
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
                        'attr': {'id': 'name=MyAction&type_MyAction_path'},
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
                                {'html': 'td', 'elem': [{'html': 'p', 'elem': [{'text': 'The url member "pa".'}]}]}
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'pb'}},
                                {'html': 'td', 'elem': {'text': 'date'}},
                                null,
                                {'html': 'td', 'elem': [
                                    {'html': 'p', 'elem': [{'text': 'The url member "pb".'}]},
                                    {'html': 'p', 'elem': [{'text': 'More info.'}]}
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
                        'attr': {'id': 'name=MyAction&type_MyAction_query'},
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
                                    {'html': 'li', 'elem': {'text': `value${nbsp}>${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `value${nbsp}<${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qb'}},
                                {'html': 'td', 'elem': {'text': 'int'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}>=${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `value${nbsp}<=${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qc'}},
                                {'html': 'td', 'elem': {'text': 'int'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}==${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qd'}},
                                {'html': 'td', 'elem': {'text': 'float'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}>${nbsp}0.5`}},
                                    {'html': 'li', 'elem': {'text': `value${nbsp}<${nbsp}9.5`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qe'}},
                                {'html': 'td', 'elem': {'text': 'float'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}>=${nbsp}0.5`}},
                                    {'html': 'li', 'elem': {'text': `value${nbsp}<=${nbsp}9.5`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qf'}},
                                {'html': 'td', 'elem': {'text': 'float'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}==${nbsp}9.5`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qg'}},
                                {'html': 'td', 'elem': {'text': 'string'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(value)${nbsp}>${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(value)${nbsp}<${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qh'}},
                                {'html': 'td', 'elem': {'text': 'string'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(value)${nbsp}>=${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(value)${nbsp}<=${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qi'}},
                                {'html': 'td', 'elem': {'text': 'string'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(value)${nbsp}==${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qj'}},
                                {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}>${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}<${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qk'}},
                                {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}>=${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}<=${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'ql'}},
                                {'html': 'td', 'elem': [{'text': 'int'}, {'text': `${nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}>=${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}<=${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qm'}},
                                {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${nbsp}{}`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}>${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}<${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qn'}},
                                {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${nbsp}{}`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}>=${nbsp}0`}},
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}<=${nbsp}10`}}
                                ]}},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'qo'}},
                                {'html': 'td', 'elem': [null, {'text': 'string'}, {'text': `${nbsp}{}`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}==${nbsp}10`}}
                                ]}},
                                null
                            ]}
                        ]
                    ]}
                ],
                [
                    {
                        'html': 'h2',
                        'attr': {'id': 'name=MyAction&type_MyAction_input'},
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
                                {'html': 'td', 'elem': [{'text': 'string'}, {'text': `${nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': 'optional'}},
                                    {'html': 'li', 'elem': {'text': 'nullable'}},
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}>${nbsp}0`}}
                                ]}},
                                null
                            ]}
                        ]
                    ]}
                ],
                [
                    {
                        'html': 'h2',
                        'attr': {'id': 'name=MyAction&type_MyAction_output'},
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
                                    'attr': {'href': '#name=MyAction&type_PositiveInt'},
                                    'elem': {'text': 'PositiveInt'}
                                }},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'ob'}},
                                {'html': 'td', 'elem': {
                                    'html': 'a',
                                    'attr': {'href': '#name=MyAction&type_JustAString'},
                                    'elem': {'text': 'JustAString'}
                                }},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'oc'}},
                                {'html': 'td', 'elem': {
                                    'html': 'a',
                                    'attr': {'href': '#name=MyAction&type_Struct1'},
                                    'elem': {'text': 'Struct1'}
                                }},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'od'}},
                                {'html': 'td', 'elem': {
                                    'html': 'a',
                                    'attr': {'href': '#name=MyAction&type_Enum1'},
                                    'elem': {'text': 'Enum1'}
                                }},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'oe'}},
                                {'html': 'td', 'elem': {
                                    'html': 'a',
                                    'attr': {'href': '#name=MyAction&type_Enum2'},
                                    'elem': {'text': 'Enum2'}
                                }},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'of'}},
                                {'html': 'td', 'elem': [
                                    [
                                        {'html': 'a', 'attr': {'href': '#name=MyAction&type_Enum1'}, 'elem': {'text': 'Enum1'}},
                                        {'text': `${nbsp}:${nbsp}`}
                                    ],
                                    {'text': 'string'}, {'text': `${nbsp}{}`}
                                ]},
                                {'html': 'td', 'elem': null},
                                null
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'og'}},
                                {'html': 'td', 'elem': [
                                    [
                                        {'html': 'a', 'attr': {'href': '#name=MyAction&type_JustAString'}, 'elem': {'text': 'JustAString'}},
                                        {'text': `${nbsp}:${nbsp}`}
                                    ],
                                    {'html': 'a', 'attr': {'href': '#name=MyAction&type_NonEmptyFloatArray'}, 'elem': {'text': 'NonEmptyFloatArray'}},
                                    {'text': `${nbsp}{}`}
                                ]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(dict)${nbsp}>${nbsp}0`}}
                                ]}},
                                null
                            ]}
                        ]
                    ]}
                ],
                [
                    {
                        'html': 'h2',
                        'attr': {'id': 'name=MyAction&type_MyAction_errors'},
                        'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'Error Codes'}}
                    },
                    null,
                    [
                        {
                            'html': 'p',
                            'elem': [{'text': 'If an application error occurs, the response is of the form:'}]
                        },
                        {
                            'html': 'pre',
                            'elem': {
                                'html': 'code',
                                'elem': [
                                    {'text': '{\n'},
                                    {'text': '    "error": "<code>",\n'},
                                    {'text': '    "message": "<message>"\n'},
                                    {'text': '}\n'}
                                ]
                            }
                        },
                        {
                            'html': 'p',
                            'elem': [{'text': '"message" is optional. "<code>" is one of the following values:'}]
                        }
                    ],
                    {
                        'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Value'}},
                                {'html': 'th', 'elem': {'text': 'Description'}}
                            ]},
                            [
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'UnexpectedError'}},
                                    {'html': 'td', 'elem': [
                                        {'html': 'p', 'elem': [{'text': 'An unexpected error occurred while processing the request'}]}
                                    ]}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'Error1'}},
                                    {'html': 'td', 'elem': null}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'Error2'}},
                                    {'html': 'td', 'elem': null}
                                ]}
                            ]
                        ]
                    }
                ]
            ],
            [
                {'html': 'hr'},
                {'html': 'h2', 'elem': {'text': 'Referenced Types'}},
                [
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_Enum1'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum Enum1'}}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'An enum.'}]}
                        ],
                        null,
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Value'}},
                                {'html': 'th', 'elem': {'text': 'Description'}}
                            ]},
                            [
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'e1'}},
                                    {'html': 'td', 'elem': [{'html': 'p', 'elem': [{'text': 'The Enum1 value "e1"'}]}]}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'e2'}},
                                    {'html': 'td', 'elem': [
                                        {'html': 'p', 'elem': [{'text': 'The Enum1 value "e 2"'}]},
                                        {'html': 'p', 'elem': [{'text': 'More info.'}]}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_Enum2'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'enum Enum2'}}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'Another enum.'}]},
                            {'html': 'p', 'elem': [{'text': 'More info.'}]}
                        ],
                        null,
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [{'html': 'th', 'elem': {'text': 'Value'}}, null]},
                            [
                                {'html': 'tr', 'elem': [{'html': 'td', 'elem': {'text': 'e3'}}, null]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_JustAString'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef JustAString'}}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'Just a string.'}]},
                            {'html': 'p', 'elem': [{'text': 'More info.'}]}
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
                            'attr': {'id': 'name=MyAction&type_NonEmptyFloatArray'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef NonEmptyFloatArray'}}
                        },
                        null,
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [{'html': 'th', 'elem': {'text': 'Type'}}, {'html': 'th', 'elem': {'text': 'Attributes'}}]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': [{'text': 'float'}, {'text': `${nbsp}[]`}]},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `len(array)${nbsp}>${nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_PositiveInt'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'typedef PositiveInt'}}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'A positive integer.'}]}
                        ],
                        {'html': 'table', 'elem': [
                            {'html': 'tr', 'elem': [
                                {'html': 'th', 'elem': {'text': 'Type'}},
                                {'html': 'th', 'elem': {'text': 'Attributes'}}
                            ]},
                            {'html': 'tr', 'elem': [
                                {'html': 'td', 'elem': {'text': 'int'}},
                                {'html': 'td', 'elem': {'html': 'ul', 'attr': {'class': 'chisel-attr-list'}, 'elem': [
                                    {'html': 'li', 'elem': {'text': `value${nbsp}>${nbsp}0`}}
                                ]}}
                            ]}
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_Struct1'},
                            'elem': {'html': 'a', 'attr': {'class': 'linktarget'}, 'elem': {'text': 'struct Struct1'}}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'A struct.'}]}
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
                                    {'html': 'td', 'elem': [{'html': 'p', 'elem': [{'text': 'The struct member "sa"'}]}]}
                                ]},
                                {'html': 'tr', 'elem': [
                                    {'html': 'td', 'elem': {'text': 'sb'}},
                                    {'html': 'td', 'elem': {
                                        'html': 'a', 'attr': {'href': '#name=MyAction&type_Struct2'}, 'elem': {'text': 'Struct2'}
                                    }},
                                    null,
                                    {'html': 'td', 'elem': [
                                        {'html': 'p', 'elem': [{'text': 'The struct member "sb"'}]},
                                        {'html': 'p', 'elem': [{'text': 'More info.'}]}
                                    ]}
                                ]}
                            ]
                        ]}
                    ],
                    [
                        {
                            'html': 'h3',
                            'attr': {'id': 'name=MyAction&type_Struct2'},
                            'elem': {'attr': {'class': 'linktarget'}, 'elem': {'text': 'union Struct2'}, 'html': 'a'}
                        },
                        [
                            {'html': 'p', 'elem': [{'text': 'Another struct, a union.'}]},
                            {'html': 'p', 'elem': [{'text': 'More info.'}]}
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
            ]
        ]
    );
});
