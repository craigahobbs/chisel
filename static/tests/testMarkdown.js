import * as chisel from '../src/chisel.js';
import {markdownElements, parseMarkdown} from '../src/markdown.js';
import {markdownTypes} from '../src/markdownTypes.js';
import test from 'ava';

/* eslint-disable id-length */


test('parseMarkdown', (t) => {
    const markdown = parseMarkdown(`
# Title

This is a sentence.
This is another sentence.


This is another paragraph.`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Title'}], 'style': 'h1'}},
                {'paragraph': {'spans': [{'text': 'This is a sentence.\nThis is another sentence.'}]}},
                {'paragraph': {'spans': [{'text': 'This is another paragraph.'}]}}
            ]
        }
    );
});


test('parseMarkdown, lines', (t) => {
    const markdown = parseMarkdown([
        '# Title',
        '',
        'This is a sentence.',
        'This is another sentence.',
        '',
        '',
        'This is another paragraph.\n\nAnd another.'
    ]);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Title'}], 'style': 'h1'}},
                {'paragraph': {'spans': [{'text': 'This is a sentence.\nThis is another sentence.'}]}},
                {'paragraph': {'spans': [{'text': 'This is another paragraph.'}]}},
                {'paragraph': {'spans': [{'text': 'And another.'}]}}
            ]
        }
    );
});


test('parseMarkdown, empty', (t) => {
    const markdown = parseMarkdown('');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': []
        }
    );
});


test('parseMarkdown, horizontal rule', (t) => {
    const markdown = parseMarkdown(`
Some text
***
******
More text
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Some text'}]}},
                {'hr': null},
                {'hr': null},
                {'paragraph': {'spans': [{'text': 'More text'}]}}
            ]
        }
    );
});


test('parseMarkdown, horizontal rule hyphens', (t) => {
    const markdown = parseMarkdown(`
Some text

---
------
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Some text'}]}},
                {'hr': null},
                {'hr': null}
            ]
        }
    );
});


test('parseMarkdown, horizontal rule underscores', (t) => {
    const markdown = parseMarkdown(`
Some text

___
______
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Some text'}]}},
                {'hr': null},
                {'hr': null}
            ]
        }
    );
});


test('parseMarkdown, horizontal rule spaces', (t) => {
    const markdown = parseMarkdown(`
Some text
 *  *    ** 
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'Some text'}]}},
                {'hr': null}
            ]
        }
    );
});


test('parseMarkdown, horizontal rule beyond code block', (t) => {
    const markdown = parseMarkdown(`
    *****
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'codeBlock': {'lines': ['*****']}}
            ]
        }
    );
});


test('parseMarkdown, heading alternate syntax', (t) => {
    const markdown = parseMarkdown(`
Title
=====

This is a sentence.

Subtitle
--------

Some words.
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'style': 'h1', 'spans': [{'text': 'Title'}]}},
                {'paragraph': {'spans': [{'text': 'This is a sentence.'}]}},
                {'paragraph': {'style': 'h2', 'spans': [{'text': 'Subtitle'}]}},
                {'paragraph': {'spans': [{'text': 'Some words.'}]}}
            ]
        }
    );
});


test('parseMarkdown, heading alternate syntax multi-line', (t) => {
    const markdown = parseMarkdown(`
Title
and More
  ===
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'style': 'h1', 'spans': [{'text': 'Title\nand More'}]}}
            ]
        }
    );
});


test('parseMarkdown, heading alternate syntax following list', (t) => {
    const markdown = parseMarkdown(`
- Title
and more
=====
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {'parts': [
            {'list': {
                'items': [
                    {'parts': [
                        {'paragraph': {
                            'spans': [{'text': 'Title\nand more\n====='}]
                        }}
                    ]}
                ]
            }}
        ]}
    );
});


test('parseMarkdown, heading alternate syntax beyond code block', (t) => {
    const markdown = parseMarkdown(`
Title
    =====
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {'parts': [
            {'paragraph': {
                'spans': [{'text': 'Title\n    ====='}]
            }}
        ]}
    );
});


test('parseMarkdown, list', (t) => {
    const markdown = parseMarkdown(`
- item 1

  item 1.2

* item 2
another
+ item 3`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'list': {
                        'items': [
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 1'}]}},
                                    {'paragraph': {'spans': [{'text': 'item 1.2'}]}}
                                ]
                            },
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 2\nanother'}]}}
                                ]
                            },
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 3'}]}
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, ordered list', (t) => {
    const markdown = parseMarkdown(`
1. item 1

   item 1.2

* item 2
another
+ item 3`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'list': {
                        'start': 1,
                        'items': [
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 1'}]}},
                                    {'paragraph': {'spans': [{'text': 'item 1.2'}]}}
                                ]
                            },
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 2\nanother'}]}}
                                ]
                            },
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'item 3'}]}
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, list nested', (t) => {
    const markdown = parseMarkdown(`
- 1
 - 2
  - 3
   - 4
    - 5
     - 6
  - 7
    - 8
      - 9
   - 10

asdf
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'list': {
                        'items': [
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': '1'}]}}
                                ]
                            },
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': '2'}]}},
                                    {
                                        'list': {
                                            'items': [
                                                {
                                                    'parts': [
                                                        {'paragraph': {'spans': [{'text': '3'}]}}
                                                    ]
                                                },
                                                {
                                                    'parts': [
                                                        {'paragraph': {'spans': [{'text': '4'}]}},
                                                        {
                                                            'list': {
                                                                'items': [
                                                                    {
                                                                        'parts': [
                                                                            {'paragraph': {'spans': [{'text': '5'}]}}
                                                                        ]
                                                                    },
                                                                    {
                                                                        'parts': [
                                                                            {'paragraph': {'spans': [{'text': '6'}]}}
                                                                        ]
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    'parts': [
                                                        {'paragraph': {'spans': [{'text': '7'}]}},
                                                        {
                                                            'list': {
                                                                'items': [
                                                                    {
                                                                        'parts': [
                                                                            {'paragraph': {'spans': [{'text': '8'}]}},
                                                                            {
                                                                                'list': {
                                                                                    'items': [
                                                                                        {
                                                                                            'parts': [
                                                                                                {'paragraph': {'spans': [{'text': '9'}]}}
                                                                                            ]
                                                                                        }
                                                                                    ]
                                                                                }
                                                                            }
                                                                        ]
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    'parts': [
                                                        {'paragraph': {'spans': [{'text': '10'}]}}
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                },
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'asdf'}
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, code block', (t) => {
    const markdown = parseMarkdown(`
This is some code:

    code 1
    code 2
    code 3

Cool, huh?`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'lines': ['code 1', 'code 2', 'code 3']}},
                {'paragraph': {'spans': [{'text': 'Cool, huh?'}]}}
            ]
        }
    );
});


test('parseMarkdown, fenced code block', (t) => {
    const markdown = parseMarkdown(`
This is some code:

\`\`\` javascript
foo();
bar();
\`\`\`
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'language': 'javascript', 'lines': ['foo();', 'bar();']}}
            ]
        }
    );
});


test('parseMarkdown, empty fenced code block', (t) => {
    const markdown = parseMarkdown(`
This is some code:

\`\`\` javascript
\`\`\`
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'language': 'javascript', 'lines': []}}
            ]
        }
    );
});


test('parseMarkdown, empty, end-of-file fenced code block', (t) => {
    const markdown = parseMarkdown(`
This is some code:

\`\`\` javascript`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'language': 'javascript', 'lines': []}}
            ]
        }
    );
});


test('parseMarkdown, code block fenced no language', (t) => {
    const markdown = parseMarkdown(`
This is some code:

\`\`\`
foo();
bar();
\`\`\`
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'lines': ['foo();', 'bar();']}}
            ]
        }
    );
});


test('parseMarkdown, code block nested', (t) => {
    const markdown = parseMarkdown(`
- This is some code:

  \`\`\`
  foo();
  bar();
  \`\`\`
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'list': {
                        'items': [
                            {
                                'parts': [
                                    {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                                    {'codeBlock': {'lines': ['foo();', 'bar();']}}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, spans', (t) => {
    const markdown = parseMarkdown(`
These are some basic styles: **bold**, *italic*, ***bold-italic***.

This is a [link](https://foo.com) and so is [this](https://bar.com "Bar").

This is another link: <https://foo.com>

This is an ![image](https://foo.com/foo.jpg) and so is ![this](https://bar.com/bar.jpg "Bar").
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'These are some basic styles: '},
                            {'style': {'style': 'bold', 'spans': [{'text': 'bold'}]}},
                            {'text': ', '},
                            {'style': {'style': 'italic', 'spans': [{'text': 'italic'}]}},
                            {'text': ', '},
                            {'style': {'spans': [{'style': {'spans': [{'text': 'bold-italic'}], 'style': 'italic'}}], 'style': 'bold'}},
                            {'text': '.'}
                        ]
                    }
                },
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'This is a '},
                            {'link': {'href': 'https://foo.com', 'spans': [{'text': 'link'}]}},
                            {'text': ' and so is '},
                            {'link': {'href': 'https://bar.com', 'spans': [{'text': 'this'}], 'title': 'Bar'}},
                            {'text': '.'}
                        ]
                    }
                },
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'This is another link: '},
                            {'link': {'href': 'https://foo.com', 'spans': [{'text': 'https://foo.com'}]}}
                        ]
                    }
                },
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'This is an '},
                            {'image': {'alt': 'image', 'src': 'https://foo.com/foo.jpg'}},
                            {'text': ' and so is '},
                            {'image': {'alt': 'this', 'src': 'https://bar.com/bar.jpg', 'title': 'Bar'}},
                            {'text': '.'}
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, nested spans', (t) => {
    const markdown = parseMarkdown(`
This is a [link **with *formatting***](https://foo.com)
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'text': 'This is a '},
                        {
                            'link': {
                                'href': 'https://foo.com',
                                'spans': [
                                    {'text': 'link '},
                                    {
                                        'style': {
                                            'style': 'bold',
                                            'spans': [
                                                {'text': 'with '},
                                                {'style': {'style': 'italic', 'spans': [{'text': 'formatting'}]}}
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }}
            ]
        }
    );
});


test('parseMarkdown, spans spaces', (t) => {
    const markdown = parseMarkdown(`
***no *** *** no*** **no ** ** no** *no * * no*
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {
                            'style': {
                                'style': 'bold',
                                'spans': [
                                    {
                                        'style': {
                                            'style': 'italic',
                                            'spans': [
                                                {'text': 'no '},
                                                {'style': {'style': 'bold', 'spans': [{'text': '* *'}]}},
                                                {'text': ' no'}
                                            ]
                                        }
                                    }
                                ]
                            }
                        },
                        {'text': ' '},
                        {
                            'style': {
                                'style': 'bold',
                                'spans': [
                                    {'text': 'no '},
                                    {'style': {'style': 'italic', 'spans': [{'text': '* *'}]}},
                                    {'text': ' no'}
                                ]
                            }
                        },
                        {'text': ' '},
                        {'style': {'style': 'italic', 'spans': [{'text': 'no * * no'}]}}
                    ]
                }}
            ]
        }
    );
});


test('parseMarkdown, line breaks', (t) => {
    const markdown = parseMarkdown(`
This is a line break  
  this is not
and this is  

This is another paragraph.
`);
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'This is a line break'},
                            {'br': null},
                            {'text': '\n  this is not\nand this is'},
                            {'br': null}
                        ]
                    }
                },
                {
                    'paragraph': {
                        'spans': [
                            {'text': 'This is another paragraph.'}
                        ]
                    }
                }
            ]
        }
    );
});


test('parseMarkdown, escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = parseMarkdown('\\ \\* \\_ \\{ \\} \\[ \\] **bol\\.d** \\( \\) \\# \\+ \\- \\. \\! \\a');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'text': '\\ * _ { } [ ] '},
                        {'style': {'style': 'bold', 'spans': [{'text': 'bol.d'}]}},
                        {'text': ' ( ) # + - . ! \\a'}
                    ]
                }}
            ]
        }
    );
});


test('parseMarkdown, link escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = parseMarkdown('[tex\]t](hre\.f "titl\.e")');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'link': {'href': 'hre.f', 'spans': [{'text': 'tex]t'}], 'title': 'titl.e'}}
                    ]
                }}
            ]
        }
    );
});


test('parseMarkdown, link href space', (t) => {
    const markdown = parseMarkdown('[text](hre f)');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'text': '[text](hre f)'}
                    ]
                }}
            ]
        }
    );
});


test('parseMarkdown, link href alternate space', (t) => {
    const markdown = parseMarkdown('<hre f>');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '<hre f>'}]}}]});
});


test('parseMarkdown, link href alternate space begin', (t) => {
    const markdown = parseMarkdown('< href>');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '< href>'}]}}]});
});


test('parseMarkdown, link href alternate space end', (t) => {
    const markdown = parseMarkdown('<href >');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '<href >'}]}}]});
});


test('parseMarkdown, image escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = parseMarkdown('![al\]t](sr\.c "titl\.e")');
    chisel.validateType(markdownTypes, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'image': {'alt': 'al]t', 'src': 'sr.c', 'title': 'titl.e'}}
                    ]
                }}
            ]
        }
    );
});


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
    chisel.validateElements(elements);
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
    chisel.validateElements(elements);
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
    chisel.validateElements(elements);
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
    chisel.validateElements(elements);
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
    chisel.validateElements(elements);
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
    chisel.validateElements(elements);
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
    }, codeBlockLanguages);
    chisel.validateElements(elements);
    t.deepEqual(
        elements,
        [
            {'text': 'foo();---bar();'}
        ]
    );
});
