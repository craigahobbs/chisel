# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# pylint: disable=missing-docstring

import json
from unittest import TestCase

from chisel import Action, Application, Request, create_doc_requests


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
                    'name': 'static_doc_css',
                    'urls': (('GET', '/doc/doc.css'),)
                },
                {
                    'name': 'static_doc_svg',
                    'urls': (('GET', '/doc/doc.svg'),)
                },
                {
                    'name': 'static_doc_js',
                    'urls': (('GET', '/doc/doc.js'),)
                },
                {
                    'name': 'static_schema_markdown_doc_js',
                    'urls': (('GET', '/doc/schema-markdown/doc.js'),)
                },
                {
                    'name': 'static_schema_markdown_element_js',
                    'urls': (('GET', '/doc/schema-markdown/element.js'),)
                },
                {
                    'name': 'static_schema_markdown_encode_js',
                    'urls': (('GET', '/doc/schema-markdown/encode.js'),)
                },
                {
                    'name': 'static_schema_markdown_index_js',
                    'urls': (('GET', '/doc/schema-markdown/index.js'),)
                },
                {
                    'name': 'static_schema_markdown_markdown_js',
                    'urls': (('GET', '/doc/schema-markdown/markdown.js'),)
                },
                {
                    'name': 'static_schema_markdown_parser_js',
                    'urls': (('GET', '/doc/schema-markdown/parser.js'),)
                },
                {
                    'name': 'static_schema_markdown_schema_js',
                    'urls': (('GET', '/doc/schema-markdown/schema.js'),)
                },
                {
                    'name': 'static_schema_markdown_schemaUtil_js',
                    'urls': (('GET', '/doc/schema-markdown/schemaUtil.js'),)
                },
                {
                    'name': 'static_schema_markdown_typeModel_js',
                    'urls': (('GET', '/doc/schema-markdown/typeModel.js'),)
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
                for request in create_doc_requests(api=False)
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
                    'name': 'static_doc_css',
                    'urls': (('GET', '/doc/doc.css'),)
                },
                {
                    'name': 'static_doc_svg',
                    'urls': (('GET', '/doc/doc.svg'),)
                },
                {
                    'name': 'static_doc_js',
                    'urls': (('GET', '/doc/doc.js'),)
                },
                {
                    'name': 'static_schema_markdown_doc_js',
                    'urls': (('GET', '/doc/schema-markdown/doc.js'),)
                },
                {
                    'name': 'static_schema_markdown_element_js',
                    'urls': (('GET', '/doc/schema-markdown/element.js'),)
                },
                {
                    'name': 'static_schema_markdown_encode_js',
                    'urls': (('GET', '/doc/schema-markdown/encode.js'),)
                },
                {
                    'name': 'static_schema_markdown_index_js',
                    'urls': (('GET', '/doc/schema-markdown/index.js'),)
                },
                {
                    'name': 'static_schema_markdown_markdown_js',
                    'urls': (('GET', '/doc/schema-markdown/markdown.js'),)
                },
                {
                    'name': 'static_schema_markdown_parser_js',
                    'urls': (('GET', '/doc/schema-markdown/parser.js'),)
                },
                {
                    'name': 'static_schema_markdown_schema_js',
                    'urls': (('GET', '/doc/schema-markdown/schema.js'),)
                },
                {
                    'name': 'static_schema_markdown_schemaUtil_js',
                    'urls': (('GET', '/doc/schema-markdown/schemaUtil.js'),)
                },
                {
                    'name': 'static_schema_markdown_typeModel_js',
                    'urls': (('GET', '/doc/schema-markdown/typeModel.js'),)
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
                for request in create_doc_requests(app=False)
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
                for request in create_doc_requests(css=False)
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
                    'name': 'static_schema_markdown_doc_js',
                    'urls': (('GET', '/doc/schema-markdown/doc.js'),)
                },
                {
                    'name': 'static_schema_markdown_element_js',
                    'urls': (('GET', '/doc/schema-markdown/element.js'),)
                },
                {
                    'name': 'static_schema_markdown_encode_js',
                    'urls': (('GET', '/doc/schema-markdown/encode.js'),)
                },
                {
                    'name': 'static_schema_markdown_index_js',
                    'urls': (('GET', '/doc/schema-markdown/index.js'),)
                },
                {
                    'name': 'static_schema_markdown_markdown_js',
                    'urls': (('GET', '/doc/schema-markdown/markdown.js'),)
                },
                {
                    'name': 'static_schema_markdown_parser_js',
                    'urls': (('GET', '/doc/schema-markdown/parser.js'),)
                },
                {
                    'name': 'static_schema_markdown_schema_js',
                    'urls': (('GET', '/doc/schema-markdown/schema.js'),)
                },
                {
                    'name': 'static_schema_markdown_schemaUtil_js',
                    'urls': (('GET', '/doc/schema-markdown/schemaUtil.js'),)
                },
                {
                    'name': 'static_schema_markdown_typeModel_js',
                    'urls': (('GET', '/doc/schema-markdown/typeModel.js'),)
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
                for request in create_doc_requests(api=False, app=False)
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
            'title': 'localhost:80',
            'groups': {
                'Documentation': [
                    'chisel_doc_index',
                    'chisel_doc_request'
                ],
                'Redirects': [
                    'redirect_doc'
                ],
                'Statics': [
                    'static_doc_css',
                    'static_doc_html',
                    'static_doc_js',
                    'static_doc_svg',
                    'static_schema_markdown_doc_js',
                    'static_schema_markdown_element_js',
                    'static_schema_markdown_encode_js',
                    'static_schema_markdown_index_js',
                    'static_schema_markdown_markdown_js',
                    'static_schema_markdown_parser_js',
                    'static_schema_markdown_schemaUtil_js',
                    'static_schema_markdown_schema_js',
                    'static_schema_markdown_typeModel_js'
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
    urls
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
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action/{a}'}],
            'types': {
                'my_action': {
                    'action': {
                        'doc': ['Action doc.', '', 'Another doc paragraph.'],
                        'name': 'my_action',
                        'input': 'my_action_input',
                        'output': 'my_action_output',
                        'path': 'my_action_path',
                        'query': 'my_action_query',
                        'urls': [{'method': 'POST', 'path': '/my_action/{a}'}]
                    }
                },
                'my_action_input': {
                    'struct': {
                        'name': 'my_action_input',
                        'members': [
                            {
                                'doc': ['Action path member doc.'],
                                'name': 'm7',
                                'type': {'user': 'MyEnum2'}
                            },
                            {
                                'doc': ['Action path member2 doc.'],
                                'name': 'm8',
                                'type': {'user': 'MyStruct2'}
                            },
                            {
                                'name': 'm9',
                                'type': {'user': 'MyTypedef2'}
                            }
                        ]
                    }
                },
                'my_action_output': {
                    'struct': {
                        'name': 'my_action_output',
                        'members': [
                            {
                                'doc': ['Action output member doc.'],
                                'name': 'm1',
                                'type': {'builtin': 'bool'}
                            },
                            {
                                'doc': ['Action output member2 doc.'],
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
                                'type': {'dict': {'type': {'builtin': 'int'}}}
                            },
                            {
                                'name': 'm11',
                                'type': {'user': 'MyEnum'}
                            },
                            {
                                'name': 'm12',
                                'type': {'array': {'type': {'user': 'MyEnum'}}}
                            },
                            {
                                'name': 'm13',
                                'type': {'dict': {'type': {'user': 'MyEnum'}}}
                            },
                            {
                                'name': 'm14',
                                'type': {'user': 'MyEnum'}
                            },
                            {
                                'name': 'm15',
                                'type': {'user': 'MyStruct'}
                            },
                            {
                                'name': 'm16',
                                'type': {'array': {'type': {'user': 'MyStruct'}}}
                            },
                            {
                                'name': 'm17',
                                'type': {'dict': {'type': {'user': 'MyStruct'}}}
                            },
                            {
                                'name': 'm18',
                                'type': {'user': 'MyTypedef'}
                            },
                            {
                                'name': 'm19',
                                'type': {'user': 'MyUnion'}
                            }
                        ]
                    }
                },
                'my_action_path': {
                    'struct': {
                        'name': 'my_action_path',
                        'members': [
                            {
                                'doc': ['Action path member doc.'],
                                'name': 'm1',
                                'type': {'user': 'MyEnum2'}
                            },
                            {
                                'doc': ['Action path member2 doc.'],
                                'name': 'm2',
                                'type': {'user': 'MyStruct2'}
                            },
                            {
                                'name': 'm3',
                                'type': {'user': 'MyTypedef2'}
                            }
                        ]
                    }
                },
                'my_action_query': {
                    'struct': {
                        'name': 'my_action_query',
                        'members': [
                            {
                                'doc': ['Action path member doc.'],
                                'name': 'm4',
                                'type': {'user': 'MyEnum2'}
                            },
                            {
                                'doc': ['Action path member2 doc.'],
                                'name': 'm5',
                                'type': {'user': 'MyStruct2'}
                            },
                            {
                                'name': 'm6',
                                'type': {'user': 'MyTypedef2'}
                            }
                        ]
                    }
                },
                'MyEnum': {
                    'enum': {
                        'name': 'MyEnum',
                        'doc': ['Enum doc.', '', 'Another enum paragraph.'],
                        'values': [
                            {
                                'doc': ['Enum value doc.', '', 'Another enum value paragraph.'],
                                'name': 'V1'
                            },
                            {
                                'doc': ['Enum value2 doc.'],
                                'name': 'V2'
                            },
                            {
                                'name': 'V3'
                            }
                        ]
                    }
                },
                'MyEnum2': {
                    'enum': {
                        'name': 'MyEnum2'
                    }
                },
                'MyStruct': {
                    'struct': {
                        'name': 'MyStruct',
                        'doc': ['Struct doc.', '', 'Another doc paragraph.'],
                        'members': [
                            {
                                'doc': ['Struct member doc.'],
                                'name': 'm1',
                                'type': {'builtin': 'int'}
                            },
                            {
                                'doc': ['Struct member2 doc.'],
                                'name': 'm2',
                                'type': {'builtin': 'int'}
                            },
                            {
                                'name': 'm3',
                                'type': {'builtin': 'int'}
                            }
                        ]
                    }
                },
                'MyStruct2': {
                    'struct': {
                        'name': 'MyStruct2',
                    }
                },
                'MyUnion': {
                    'struct': {
                        'name': 'MyUnion',
                        'doc': ['Union doc.', '', 'Another doc paragraph.'],
                        'members': [
                            {
                                'doc': ['Union member doc.'],
                                'name': 'm1',
                                'type': {'builtin': 'int'}
                            },
                            {
                                'doc': ['Union member2 doc.'],
                                'name': 'm2',
                                'type': {'builtin': 'float'}
                            },
                            {
                                'name': 'm3',
                                'type': {'builtin': 'string'}
                            }
                        ],
                        'union': True
                    }
                },
                'MyTypedef': {
                    'typedef': {
                        'name': 'MyTypedef',
                        'doc': ['Typedef doc.', '', 'Another typedef paragraph.'],
                        'type': {'dict': {'keyType': {'user': 'MyEnum'}, 'type': {'user': 'MyStruct'}}}
                    }
                },
                'MyTypedef2': {
                    'typedef': {
                        'name': 'MyTypedef2',
                        'type': {'builtin': 'int'}
                    }
                }
            }
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action2')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'name': 'my_action2',
            'urls': [{'method': 'POST', 'url': '/my_action2'}],
            'types': {
                'my_action2': {
                    'action': {
                        'name': 'my_action2'
                    }
                }
            }
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
        string(nullable) m17
        optional bool(nullable) m18
        optional int m19
'''))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}],
            'types': {
                'IntDict': {
                    'typedef': {
                        'name': 'IntDict',
                        'type': {'dict': {'type': {'builtin': 'int'}}},
                        'attr': {'lenGT': 0}
                    }
                },
                'my_action': {
                    'action': {
                        'name': 'my_action',
                        'output': 'my_action_output'
                    }
                },
                'my_action_output': {
                    'struct': {
                        'name': 'my_action_output',
                        'members': [
                            {'attr': {'gt': 0.0, 'lt': 100.0}, 'name': 'm1', 'type': {'builtin': 'int'}},
                            {'attr': {'gte': 0.0, 'lte': 100.0}, 'name': 'm2', 'type': {'builtin': 'int'}},
                            {'attr': {'eq': 100.0}, 'name': 'm3', 'type': {'builtin': 'int'}},
                            {'attr': {'lenGT': 0, 'lenLT': 100}, 'name': 'm4', 'type': {'builtin': 'string'}},
                            {'attr': {'lenGTE': 0, 'lenLTE': 100}, 'name': 'm5', 'type': {'builtin': 'string'}},
                            {'attr': {'lenEq': 100}, 'name': 'm6', 'type': {'builtin': 'string'}},
                            {'attr': {'lenGT': 0, 'lenLT': 100}, 'name': 'm7', 'type': {'array': {'type': {'builtin': 'int'}}}},
                            {'attr': {'lenGTE': 0, 'lenLTE': 100}, 'name': 'm8', 'type': {'array': {'type': {'builtin': 'int'}}}},
                            {'attr': {'lenEq': 100}, 'name': 'm9', 'type': {'array': {'type': {'builtin': 'int'}}}},
                            {'name': 'm10', 'type': {'array': {'attr': {'gt': 0.0}, 'type': {'builtin': 'int'}}}},
                            {'attr': {'lenGT': 0, 'lenLT': 100}, 'name': 'm11', 'type': {'dict': {'type': {'builtin': 'int'}}}},
                            {'attr': {'lenGTE': 0, 'lenLTE': 100}, 'name': 'm12', 'type': {'dict': {'type': {'builtin': 'int'}}}},
                            {'attr': {'lenEq': 100}, 'name': 'm13', 'type': {'dict': {'type': {'builtin': 'int'}}}},
                            {'name': 'm14', 'type': {'dict': {'attr': {'lenGT': 1}, 'type': {'builtin': 'string'},
                                                              'keyAttr': {'lenGT': 0}, 'keyType': {'builtin': 'string'}}}},
                            {'name': 'm15', 'type': {'user': 'IntDict'}},
                            {'name': 'm16', 'optional': True, 'type': {'builtin': 'float'}},
                            {'name': 'm17', 'type': {'builtin': 'string'}, 'attr': {'nullable': True}},
                            {'name': 'm18', 'optional': True, 'type': {'builtin': 'bool'}, 'attr': {'nullable': True}},
                            {'name': 'm19', 'optional': True, 'type': {'builtin': 'int'}}
                        ]
                    }
                }
            }
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
        app.add_requests(create_doc_requests([app.requests['my_action']]))

        status, _, response = app.request('GET', '/doc/doc_index')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'title': 'localhost:80',
            'groups': {
                'Uncategorized': [
                    'my_action'
                ]
            }
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}],
            'types': {
                'my_action': {'action': {'name': 'my_action'}}
            }
        })

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action2')
        self.assertEqual(status, '400 Bad Request')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'error': 'UnknownName'
        })

    def test_no_urls(self):
        app = Application()
        app.add_requests(create_doc_requests())
        app.add_request(Action(None, name='my_action', urls=(), spec='''\
action my_action
'''))

        status, _, response = app.request('GET', '/doc/doc_request', query_string='name=my_action')
        self.assertEqual(status, '200 OK')
        self.assertDictEqual(json.loads(response.decode('utf-8')), {
            'name': 'my_action',
            'types': {
                'my_action': {'action': {'name': 'my_action'}}
            }
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
            'name': 'my_action',
            'urls': [{'method': 'POST', 'url': '/my_action'}],
            'types': {
                'my_action': {'action': {'name': 'my_action'}}
            }
        })
