# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

import json

from chisel import Action, Application, Request, create_doc_requests

from . import TestCase # pylint: disable=no-name-in-module


class TestGetDocRequests(TestCase):

    def test_default(self):
        self.assertListEqual(
            [
                {
                    'name': request.name,
                    'urls': request.urls
                }
                for request in create_doc_requests()
            ],
            [
                {
                    'name': 'chisel_doc_index',
                    'urls': (('GET', '/doc/doc_index'),)
                },
                {
                    'name': 'chisel_doc_request',
                    'urls': (('GET', '/doc/doc_request'),)
                },
                {
                    'name': 'redirect_doc',
                    'urls': (('GET', '/doc'),)
                },
                {
                    'name': 'static_doc_html',
                    'urls': (('GET', '/doc/'), ('GET', '/doc/index.html'))
                },
                {
                    'name': 'static_doc_js',
                    'urls': (('GET', '/doc/doc.js'),)
                },
                {
                    'name': 'static_doc_css',
                    'urls': (('GET', '/doc/doc.css'),)
                },
                {
                    'name': 'static_chisel_js',
                    'urls': (('GET', '/doc/chisel.js'),)
                }
            ]
        )

    def test_no_request_api(self):
        self.assertListEqual(
            [
                {
                    'name': request.name,
                    'urls': request.urls
                }
                for request in create_doc_requests(request_api=False)
            ],
            [
                {
                    'name': 'redirect_doc',
                    'urls': (('GET', '/doc'),)
                },
                {
                    'name': 'static_doc_html',
                    'urls': (('GET', '/doc/'), ('GET', '/doc/index.html'))
                },
                {
                    'name': 'static_doc_js',
                    'urls': (('GET', '/doc/doc.js'),)
                },
                {
                    'name': 'static_doc_css',
                    'urls': (('GET', '/doc/doc.css'),)
                },
                {
                    'name': 'static_chisel_js',
                    'urls': (('GET', '/doc/chisel.js'),)
                }
            ]
        )

    def test_no_static(self):
        self.assertListEqual(
            [
                {
                    'name': request.name,
                    'urls': request.urls
                }
                for request in create_doc_requests(doc=False)
            ],
            [
                {
                    'name': 'chisel_doc_index',
                    'urls': (('GET', '/doc/doc_index'),)
                },
                {
                    'name': 'chisel_doc_request',
                    'urls': (('GET', '/doc/doc_request'),)
                }
            ]
        )

    def test_no_static_css(self):
        self.assertListEqual(
            [
                {
                    'name': request.name,
                    'urls': request.urls,
                }
                for request in create_doc_requests(doc_css=False)
            ],
            [
                {
                    'name': 'chisel_doc_index',
                    'urls': (('GET', '/doc/doc_index'),)
                },
                {
                    'name': 'chisel_doc_request',
                    'urls': (('GET', '/doc/doc_request'),)
                },
                {
                    'name': 'redirect_doc',
                    'urls': (('GET', '/doc'),)
                },
                {
                    'name': 'static_doc_html',
                    'urls': (('GET', '/doc/'), ('GET', '/doc/index.html'))
                },
                {
                    'name': 'static_doc_js',
                    'urls': (('GET', '/doc/doc.js'),)
                },
                {
                    'name': 'static_chisel_js',
                    'urls': (('GET', '/doc/chisel.js'),)
                }
            ]
        )

    def test_none(self):
        self.assertListEqual(
            [
                {
                    'name': request.name,
                    'urls': request.urls,
                }
                for request in create_doc_requests(request_api=False, doc=False)
            ],
            []
        )


class TestIndex(TestCase):

    def test_doc_index(self):
        app = Application()
        app.add_requests(create_doc_requests())

        status, _, response = app.request('GET', '/doc/doc_index')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'groups': {
                'Documentation': [
                    'chisel_doc_index',
                    'chisel_doc_request'
                ],
                'Redirects': [
                    'redirect_doc'
                ],
                'Statics': [
                    'static_chisel_js',
                    'static_doc_css',
                    'static_doc_html',
                    'static_doc_js'
                ]
            }
        })


class TestRequest(TestCase):

    def test_types(self):
        app = Application()
        app.add_requests(create_doc_requests())
        app.add_request(Action(None, name='my_action', spec='''\
# Enum doc.
#
# Another enum paragraph.
enum MyEnum

    # Enum value doc.
    #
    # Another enum value paragraph.
    V1

    # Enum value2 doc.
    V2

    #- Enum value3 with no doc.
    V3

#- Enum with values or doc
enum MyEnum2

# Struct doc.
#
# Another doc paragraph.
struct MyStruct

    # Struct member doc.
    int m1

    # Struct member2 doc.
    int m2

    #- Struct member3 with no doc.
    int m3

#- Struct with no members or doc
struct MyStruct2

# Typedef doc.
#
# Another typedef paragraph.
typedef MyEnum : MyStruct{} MyTypedef

#- Typedef with no doc.
typedef int MyTypedef2

# Union doc.
#
# Another doc paragraph.
union MyUnion

    # Union member doc.
    int m1

    # Union member2 doc.
    float m2

    #- Union member2 with no doc.
    string m3

# Action doc.
#
# Another doc paragraph.
action my_action
    url
        POST /my_action/{a}

    path
        # Action path member doc.
        MyEnum2 m1

        # Action path member2 doc.
        MyStruct2 m2

        #- Action path member3 with no doc.
        MyTypedef2 m3

    query
        # Action path member doc.
        MyEnum2 m4

        # Action path member2 doc.
        MyStruct2 m5

        #- Action path member3 with no doc.
        MyTypedef2 m6

    input
        # Action path member doc.
        MyEnum2 m7

        # Action path member2 doc.
        MyStruct2 m8

        #- Action path member3 with no doc.
        MyTypedef2 m9

    output
        # Action output member doc.
        bool m1

        # Action output member2 doc.
        date m2

        #- Action output member3 with no doc.
        datetime m3
        float m4
        int m5
        object m6
        string m7
        uuid m8
        int[] m9
        int{} m10
        MyEnum m11
        MyEnum[] m12
        MyEnum{} m13
        MyEnum : int m14
        MyStruct m15
        MyStruct[] m16
        MyStruct{} m17
        MyTypedef m18
        MyUnion m19
'''))
        app.add_request(Action(None, name='my_action2', spec='''\
action my_action2
'''))
        app.add_request(Request(None, name='my_request', doc='Request doc.'))
        app.add_request(Request(None, name='my_request2'))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {
                    'name': 'my_action_error',
                    'values': []
                },
                'input': {
                    'members': [
                        {
                            'doc': [' Action path member doc.'],
                            'name': 'm7',
                            'type': {'enum': 'MyEnum2'}
                        },
                        {
                            'doc': [' Action path member2 doc.'],
                            'name': 'm8',
                            'type': {'struct': 'MyStruct2'}
                        },
                        {
                            'name': 'm9',
                            'type': {'typedef': 'MyTypedef2'}
                        }
                    ],
                    'name': 'my_action_input'
                },
                'name': 'my_action',
                'output': {
                    'members': [
                        {
                            'doc': [' Action output member doc.'],
                            'name': 'm1',
                            'type': {'builtin': 'bool'}
                        },
                        {
                            'doc': [' Action output member2 doc.'],
                            'name': 'm2',
                            'type': {'builtin': 'date'}
                        },
                        {
                            'name': 'm3',
                            'type': {'builtin': 'datetime'}
                        },
                        {
                            'name': 'm4',
                            'type': {'builtin': 'float'}
                        },
                        {
                            'name': 'm5',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'name': 'm6',
                            'type': {'builtin': 'object'}
                        },
                        {
                            'name': 'm7',
                            'type': {'builtin': 'string'}
                        },
                        {
                            'name': 'm8',
                            'type': {'builtin': 'uuid'}
                        },
                        {
                            'name': 'm9',
                            'type': {'array': {'type': {'builtin': 'int'}}}
                        },
                        {
                            'name': 'm10',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'int'}}}
                        },
                        {
                            'name': 'm11',
                            'type': {'enum': 'MyEnum'}
                        },
                        {
                            'name': 'm12',
                            'type': {'array': {'type': {'enum': 'MyEnum'}}}
                        },
                        {
                            'name': 'm13',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'enum': 'MyEnum'}}}
                        },
                        {
                            'name': 'm14',
                            'type': {'enum': 'MyEnum'}
                        },
                        {
                            'name': 'm15',
                            'type': {'struct': 'MyStruct'}
                        },
                        {
                            'name': 'm16',
                            'type': {'array': {'type': {'struct': 'MyStruct'}}}
                        },
                        {
                            'name': 'm17',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'struct': 'MyStruct'}}}
                        },
                        {
                            'name': 'm18',
                            'type': {'typedef': 'MyTypedef'}
                        },
                        {
                            'name': 'm19',
                            'type': {'struct': 'MyUnion'}
                        }
                    ],
                    'name': 'my_action_output'
                },
                'path': {
                    'members': [
                        {
                            'doc': [' Action path member doc.'],
                            'name': 'm1',
                            'type': {'enum': 'MyEnum2'}
                        },
                        {
                            'doc': [' Action path member2 doc.'],
                            'name': 'm2',
                            'type': {'struct': 'MyStruct2'}
                        },
                        {
                            'name': 'm3',
                            'type': {'typedef': 'MyTypedef2'}
                        }
                    ],
                    'name': 'my_action_path'
                },
                'query': {
                    'members': [
                        {
                            'doc': [' Action path member doc.'],
                            'name': 'm4',
                            'type': {'enum': 'MyEnum2'}
                        },
                        {
                            'doc': [' Action path member2 doc.'],
                            'name': 'm5',
                            'type': {'struct': 'MyStruct2'}
                        },
                        {
                            'name': 'm6',
                            'type': {'typedef': 'MyTypedef2'}
                        }
                    ],
                    'name': 'my_action_query'
                }
            },
            'doc': [' Action doc.', '', ' Another doc paragraph.'],
            'enums': [
                {
                    'doc': [' Enum doc.', '', ' Another enum paragraph.'],
                    'name': 'MyEnum',
                    'values': [
                        {
                            'doc': [' Enum value doc.', '', ' Another enum value paragraph.'],
                            'value': 'V1'
                        },
                        {
                            'doc': [' Enum value2 doc.'],
                            'value': 'V2'
                        },
                        {
                            'value': 'V3'
                        }
                    ]
                },
                {
                    'name': 'MyEnum2',
                    'values': []
                }
            ],
            'name': 'my_action',
            'structs': [
                {
                    'doc': [
                        ' Struct doc.',
                        '',
                        ' Another doc paragraph.'
                    ],
                    'members': [
                        {
                            'doc': [' Struct member doc.'],
                            'name': 'm1',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'doc': [' Struct member2 doc.'],
                            'name': 'm2',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'name': 'm3',
                            'type': {'builtin': 'int'}
                        }
                    ],
                    'name': 'MyStruct'
                },
                {
                    'members': [],
                    'name': 'MyStruct2'
                },
                {
                    'doc': [' Union doc.', '', ' Another doc paragraph.'],
                    'members': [
                        {
                            'doc': [' Union member doc.'],
                            'name': 'm1',
                            'optional': True,
                            'type': {'builtin': 'int'}
                        },
                        {
                            'doc': [' Union member2 doc.'],
                            'name': 'm2',
                            'optional': True,
                            'type': {'builtin': 'float'}
                        },
                        {
                            'name': 'm3',
                            'optional': True,
                            'type': {'builtin': 'string'}
                        }
                    ],
                    'name': 'MyUnion',
                    'union': True
                }
            ],
            'typedefs': [
                {
                    'doc': [' Typedef doc.', '', ' Another typedef paragraph.'],
                    'name': 'MyTypedef',
                    'type': {'dict': {'key_type': {'enum': 'MyEnum'}, 'type': {'struct': 'MyStruct'}}}
                },
                {
                    'name': 'MyTypedef2',
                    'type': {'builtin': 'int'}
                }
            ],
            'urls': [{'method': 'POST', 'url': '/my_action/{a}'}]
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action2')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {'name': 'my_action2_error', 'values': []},
                'input': {'members': [], 'name': 'my_action2_input'},
                'name': 'my_action2',
                'output': {'members': [], 'name': 'my_action2_output'},
                'path': {'members': [], 'name': 'my_action2_path'},
                'query': {'members': [], 'name': 'my_action2_query'}
            },
            'name': 'my_action2',
            'urls': [{'method': 'POST', 'url': '/my_action2'}]
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_request')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'doc': ['Request doc.'],
            'name': 'my_request',
            'urls': [{'url': '/my_request'}]
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_request2')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'name': 'my_request2',
            'urls': [{'url': '/my_request2'}]
        })

    def test_attr(self):
        app = Application()
        app.add_requests(create_doc_requests())
        app.add_request(Action(None, name='my_action', spec='''\
typedef int{len > 0} IntDict

action my_action
    output
        int(> 0, < 100) m1
        int(>= 0, <= 100) m2
        int(== 100) m3
        string(len > 0, len < 100) m4
        string(len >= 0, len <= 100) m5
        string(len == 100) m6
        int[len > 0, len < 100] m7
        int[len >= 0, len <= 100] m8
        int[len == 100] m9
        int(> 0)[] m10
        int{len > 0, len < 100} m11
        int{len >= 0, len <= 100} m12
        int{len == 100} m13
        string(len > 0) : string(len > 1){} m14
        IntDict m15
        optional float m16
        nullable string m17
        optional nullable bool m18
        optional int m19
'''))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {'name': 'my_action_error', 'values': []},
                'input': {'members': [], 'name': 'my_action_input'},
                'name': 'my_action',
                'output': {
                    'members': [
                        {
                            'attr': {'gt': 0.0, 'lt': 100.0},
                            'name': 'm1',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'attr': {'gte': 0.0, 'lte': 100.0},
                            'name': 'm2',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'attr': {'eq': 100.0},
                            'name': 'm3',
                            'type': {'builtin': 'int'}
                        },
                        {
                            'attr': {'len_gt': 0, 'len_lt': 100},
                            'name': 'm4',
                            'type': {'builtin': 'string'}
                        },
                        {
                            'attr': {'len_gte': 0, 'len_lte': 100},
                            'name': 'm5',
                            'type': {'builtin': 'string'}
                        },
                        {
                            'attr': {'len_eq': 100},
                            'name': 'm6',
                            'type': {'builtin': 'string'}
                        },
                        {
                            'attr': {'len_gt': 0, 'len_lt': 100},
                            'name': 'm7',
                            'type': {'array': {'type': {'builtin': 'int'}}}
                        },
                        {
                            'attr': {'len_gte': 0, 'len_lte': 100},
                            'name': 'm8',
                            'type': {'array': {'type': {'builtin': 'int'}}}
                        },
                        {
                            'attr': {'len_eq': 100},
                            'name': 'm9',
                            'type': {'array': {'type': {'builtin': 'int'}}}
                        },
                        {
                            'name': 'm10',
                            'type': {'array': {'attr': {'gt': 0.0}, 'type': {'builtin': 'int'}}}
                        },
                        {
                            'attr': {'len_gt': 0, 'len_lt': 100},
                            'name': 'm11',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'int'}}}
                        },
                        {
                            'attr': {'len_gte': 0, 'len_lte': 100},
                            'name': 'm12',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'int'}}}
                        },
                        {
                            'attr': {'len_eq': 100},
                            'name': 'm13',
                            'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'int'}}}
                        },
                        {
                            'name': 'm14',
                            'type': {
                                'dict': {
                                    'attr': {'len_gt': 1},
                                    'key_attr': {'len_gt': 0},
                                    'key_type': {'builtin': 'string'},
                                    'type': {'builtin': 'string'}
                                }
                            }
                        },
                        {
                            'name': 'm15',
                            'type': {'typedef': 'IntDict'}
                        },
                        {
                            'name': 'm16',
                            'optional': True,
                            'type': {'builtin': 'float'}
                        },
                        {
                            'name': 'm17',
                            'nullable': True,
                            'type': {'builtin': 'string'}
                        },
                        {
                            'name': 'm18',
                            'nullable': True,
                            'optional': True,
                            'type': {'builtin': 'bool'}
                        },
                        {
                            'name': 'm19',
                            'optional': True,
                            'type': {'builtin': 'int'}
                        }
                    ],
                    'name': 'my_action_output'
                },
                'path': {'members': [], 'name': 'my_action_path'},
                'query': {'members': [], 'name': 'my_action_query'}
            },
            'name': 'my_action',
            'typedefs': [
                {
                    'attr': {'len_gt': 0},
                    'name': 'IntDict',
                    'type': {'dict': {'key_type': {'builtin': 'string'}, 'type': {'builtin': 'int'}}}
                }
            ],
            'urls': [{'method': 'POST', 'url': '/my_action'}]
        })

    def test_unkown_name(self):
        app = Application()
        app.add_requests(create_doc_requests())

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '400 Bad Request')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'error': 'UnknownName'
        })

    def test_requests(self):
        app = Application()
        app.add_request(Action(None, name='my_action', spec='''\
action my_action
'''))
        app.add_request(Action(None, name='my_action2', spec='''\
action my_action2
'''))
        app.add_requests(create_doc_requests({'my_action': app.requests['my_action']}))

        status, _, response = app.request('GET', '/doc/doc_index')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'groups': {
                'Uncategorized': [
                    'my_action'
                ]
            }
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {'name': 'my_action_error', 'values': []},
                'input': {'members': [], 'name': 'my_action_input'},
                'name': 'my_action',
                'output': {'members': [], 'name': 'my_action_output'},
                'path': {'members': [], 'name': 'my_action_path'},
                'query': {'members': [], 'name': 'my_action_query'}
            },
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}]
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action2')
        self.assertEqual(status, '400 Bad Request')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'error': 'UnknownName'
        })

    def test_wsgi_response(self):
        app = Application()
        app.add_requests(create_doc_requests())
        app.add_request(Action(None, name='my_action', wsgi_response=True, spec='''\
action my_action
'''))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {'name': 'my_action_error', 'values': []},
                'input': {'members': [], 'name': 'my_action_input'},
                'name': 'my_action',
                'path': {'members': [], 'name': 'my_action_path'},
                'query': {'members': [], 'name': 'my_action_query'}
            },
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}]
        })

    def test_base_action_type(self):
        app = Application()
        app.add_requests(create_doc_requests())
        app.add_request(Action(None, name='my_action', spec='''\
struct PathBase
    int m1

struct QueryBase
    float m2

struct InputBase
    string m3

struct OutputBase
    bool m4

action my_action
    path (PathBase)
    query (QueryBase)
    input (InputBase)
    output (OutputBase)
'''))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'action': {
                'errors': {'name': 'my_action_error', 'values': []},
                'input': {
                    'members': [
                        {'name': 'm3', 'type': {'builtin': 'string'}}
                    ],
                    'name': 'my_action_input'
                },
                'name': 'my_action',
                'output': {
                    'members': [
                        {'name': 'm4', 'type': {'builtin': 'bool'}}
                    ],
                    'name': 'my_action_output'
                },
                'path': {
                    'members': [
                        {'name': 'm1', 'type': {'builtin': 'int'}}
                    ],
                    'name': 'my_action_path'
                },
                'query': {
                    'members': [
                        {'name': 'm2', 'type': {'builtin': 'float'}}
                    ],
                    'name': 'my_action_query'
                }
            },
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}]
        })
