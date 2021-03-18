// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/* eslint-disable id-length */

import {markdownElements} from '../../src/markdownModel/elements.js';
import test from 'ava';
import {validateElements} from '../../src/elementModel/model.js';


test('markdownElements', (t) => {
    const elements = markdownElements({
        'parts': [
            {'paragraph': {'style': 'h1', 'spans': [{'text': 'Title'}]}},
            {
                'paragraph': {
                    'spans': [
                        {'text': 'This is a sentence. This is '},
                        {
                            'style': {
                                'style': 'bold',
                                'spans': [
                                    {'text': 'bold and '},
                                    {'style': {'style': 'italic', 'spans': [{'text': 'bold-italic'}]}},
                                    {'text': '.'}
                                ]
                            }
                        }
                    ]
                }
            },
            {
                'paragraph': {
                    'spans': [
                        {'text': 'This is a link to the '},
                        {'link': {
                            'href': 'https://craigahobbs.github.io/chisel/doc/',
                            'title': 'The Chisel Type Model',
                            'spans': [
                                {'style': {'style': 'bold', 'spans': [{'text': 'Chisel'}]}},
                                {'text': ' Type Model'}
                            ]
                        }}
                    ]
                }
            },
            {
                'paragraph': {
                    'spans': [
                        {'text': 'This is an image: '},
                        {'image': {
                            'src': 'https://craigahobbs.github.io/chisel/doc/doc.svg',
                            'alt': 'Chisel Documentation Icon',
                            'title': 'Chisel'
                        }}
                    ]
                }
            },
            {
                'list': {
                    'items': [
                        {
                            'parts': [
                                {'paragraph': {'spans': [{'text': 'This is a paragraph.'}]}},
                                {'paragraph': {'spans': [{'text': 'This is a another paragraph.'}]}}
                            ]
                        },
                        {
                            'parts': [
                                {'paragraph': {'spans': [{'text': 'This is the second list item.'}]}}
                            ]
                        }
                    ]
                }
            },
            {
                'list': {
                    'start': 10,
                    'items': [
                        {
                            'parts': [
                                {'paragraph': {'spans': [{'text': 'This is a paragraph.'}]}}
                            ]
                        }
                    ]
                }
            },
            {
                'codeBlock': {
                    'lines': [
                        'Line 1',
                        'Line 2'
                    ]
                }
            }
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {'html': 'h1', 'elem': [{'text': 'Title'}]},
            {
                'html': 'p',
                'elem': [
                    {'text': 'This is a sentence. This is '},
                    {'html': 'strong', 'elem': [
                        {'text': 'bold and '},
                        {'html': 'em', 'elem': [{'text': 'bold-italic'}]},
                        {'text': '.'}
                    ]}
                ]
            },
            {
                'html': 'p',
                'elem': [
                    {'text': 'This is a link to the '},
                    {
                        'html': 'a',
                        'attr': {'href': 'https://craigahobbs.github.io/chisel/doc/', 'title': 'The Chisel Type Model'},
                        'elem': [{'html': 'strong', 'elem': [{'text': 'Chisel'}]}, {'text': ' Type Model'}]
                    }
                ]
            },
            {
                'html': 'p',
                'elem': [
                    {'text': 'This is an image: '},
                    {
                        'html': 'img',
                        'attr': {
                            'src': 'https://craigahobbs.github.io/chisel/doc/doc.svg',
                            'title': 'Chisel',
                            'alt': 'Chisel Documentation Icon'
                        }
                    }
                ]
            },
            {
                'html': 'ul',
                'attr': null,
                'elem': [
                    {
                        'html': 'li',
                        'elem': [
                            {'html': 'p', 'elem': [{'text': 'This is a paragraph.'}]},
                            {'html': 'p', 'elem': [{'text': 'This is a another paragraph.'}]}
                        ]
                    },
                    {
                        'html': 'li',
                        'elem': [
                            {'html': 'p', 'elem': [{'text': 'This is the second list item.'}]}
                        ]
                    }
                ]
            },
            {
                'html': 'ol',
                'attr': {'start': '10'},
                'elem': [
                    {
                        'html': 'li',
                        'elem': [
                            {'html': 'p', 'elem': [{'text': 'This is a paragraph.'}]}
                        ]
                    }
                ]
            },
            {
                'html': 'pre',
                'elem': {
                    'html': 'code',
                    'elem': [
                        {'text': 'Line 1\n'},
                        {'text': 'Line 2\n'}
                    ]
                }
            }
        ]
    );
});


test('markdownElements, line break', (t) => {
    const elements = markdownElements({
        'parts': [
            {
                'paragraph': {
                    'spans': [
                        {'text': 'This is a line break'},
                        {'br': null},
                        {'text': 'some more text'}
                    ]
                }
            }
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {
                'html': 'p',
                'elem': [
                    {'text': 'This is a line break'},
                    {'html': 'br'},
                    {'text': 'some more text'}
                ]
            }
        ]
    );
});


test('markdownElements, horizontal rule', (t) => {
    const elements = markdownElements({
        'parts': [
            {'paragraph': {'spans': [{'text': 'Some text'}]}},
            {'hr': null},
            {'paragraph': {'spans': [{'text': 'More text'}]}}
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {'html': 'p', 'elem': [{'text': 'Some text'}]},
            {'html': 'hr'},
            {'html': 'p', 'elem': [{'text': 'More text'}]}
        ]
    );
});


test('markdownElements, link span with no title', (t) => {
    const elements = markdownElements({
        'parts': [
            {
                'paragraph': {
                    'spans': [
                        {'link': {
                            'href': 'https://craigahobbs.github.io/chisel/doc/',
                            'spans': [{'text': 'Type Model'}]
                        }}
                    ]
                }
            }
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {
                'html': 'p',
                'elem': [
                    {
                        'html': 'a',
                        'attr': {'href': 'https://craigahobbs.github.io/chisel/doc/'},
                        'elem': [{'text': 'Type Model'}]
                    }
                ]
            }
        ]
    );
});


test('markdownElements, image span with no title', (t) => {
    const elements = markdownElements({
        'parts': [
            {
                'paragraph': {
                    'spans': [
                        {'image': {
                            'src': 'https://craigahobbs.github.io/chisel/doc/doc.svg',
                            'alt': 'Chisel Documentation Icon'
                        }}
                    ]
                }
            }
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {
                'html': 'p',
                'elem': [
                    {
                        'html': 'img',
                        'attr': {
                            'src': 'https://craigahobbs.github.io/chisel/doc/doc.svg',
                            'alt': 'Chisel Documentation Icon'
                        }
                    }
                ]
            }
        ]
    );
});


test('markdownElements, code block with language', (t) => {
    const elements = markdownElements({
        'parts': [
            {
                'codeBlock': {
                    'language': 'javascript',
                    'lines': [
                        'foo();',
                        'bar();'
                    ]
                }
            }
        ]
    });
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {
                'html': 'pre',
                'elem': {
                    'html': 'code',
                    'elem': [
                        {'text': 'foo();\n'},
                        {'text': 'bar();\n'}
                    ]
                }
            }
        ]
    );
});


test('markdownElements, code block with language override', (t) => {
    const codeBlockLanguages = {
        'fooscript': (codeBlock) => ({'text': codeBlock.lines.join('---')})
    };
    const elements = markdownElements({
        'parts': [
            {
                'codeBlock': {
                    'language': 'fooscript',
                    'lines': [
                        'foo();',
                        'bar();'
                    ]
                }
            }
        ]
    }, null, codeBlockLanguages);
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {'text': 'foo();---bar();'}
        ]
    );
});


test('markdownElements, relative and absolute URLs', (t) => {
    const markdown = {
        'parts': [
            {
                'paragraph': {
                    'spans': [
                        {'link': {
                            'href': 'https://craigahobbs.github.io/chisel/doc/',
                            'spans': [{'text': 'Absolute Link'}]
                        }},
                        {'link': {
                            'href': 'doc/',
                            'spans': [{'text': 'Relative Link'}]
                        }}
                    ]
                }
            }
        ]
    };

    // Test without file URL
    const elements = markdownElements(markdown);
    validateElements(elements);
    t.deepEqual(
        elements,
        [
            {
                'elem': [
                    {
                        'attr': {'href': 'https://craigahobbs.github.io/chisel/doc/'},
                        'elem': [{'text': 'Absolute Link'}],
                        'html': 'a'
                    },
                    {
                        'attr': {'href': 'doc/'},
                        'elem': [{'text': 'Relative Link'}],
                        'html': 'a'
                    }
                ],
                'html': 'p'
            }
        ]
    );

    // Test with file URL
    const elementsURL = markdownElements(markdown, 'https://foo.com/index.md');
    validateElements(elementsURL);
    t.deepEqual(
        elementsURL,
        [
            {
                'elem': [
                    {
                        'attr': {'href': 'https://craigahobbs.github.io/chisel/doc/'},
                        'elem': [{'text': 'Absolute Link'}],
                        'html': 'a'
                    },
                    {
                        'attr': {'href': 'https://foo.com/doc/'},
                        'elem': [{'text': 'Relative Link'}],
                        'html': 'a'
                    }
                ],
                'html': 'p'
            }
        ]
    );
});
