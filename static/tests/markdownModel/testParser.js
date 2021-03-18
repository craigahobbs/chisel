// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

/* eslint-disable id-length */

import {markdownModel} from '../../src/markdownModel/markdownModel.js';
import {markdownParse} from '../../src/markdownModel/parser.js';
import test from 'ava';
import {validateType} from '../../src/schemaMarkdown/schema.js';


test('markdownParse', (t) => {
    const markdown = markdownParse(`
# Title

This is a sentence.
This is another sentence.


This is another paragraph.`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, lines', (t) => {
    const markdown = markdownParse([
        '# Title',
        '',
        'This is a sentence.',
        'This is another sentence.',
        '',
        '',
        'This is another paragraph.\n\nAnd another.'
    ]);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, empty', (t) => {
    const markdown = markdownParse('');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': []
        }
    );
});


test('markdownParse, horizontal rule', (t) => {
    const markdown = markdownParse(`
Some text
***
******
More text
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, horizontal rule hyphens', (t) => {
    const markdown = markdownParse(`
Some text

---
------
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, horizontal rule underscores', (t) => {
    const markdown = markdownParse(`
Some text

___
______
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, horizontal rule spaces', (t) => {
    const markdown = markdownParse(`
Some text
 *  *    ** 
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, horizontal rule beyond code block', (t) => {
    const markdown = markdownParse(`
    *****
`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'codeBlock': {'lines': ['*****']}}
            ]
        }
    );
});


test('markdownParse, horizontal rule following code block', (t) => {
    const markdown = markdownParse(`
This is a horizontal fule immediately following a code block:

    code

---
`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is a horizontal fule immediately following a code block:'}]}},
                {'codeBlock': {'lines': ['code']}},
                {'hr': null}
            ]
        }
    );
});


test('markdownParse, heading alternate syntax', (t) => {
    const markdown = markdownParse(`
Title
=====

This is a sentence.

Subtitle
--------

Some words.
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, heading alternate syntax multi-line', (t) => {
    const markdown = markdownParse(`
Title
and More
  ===
`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'style': 'h1', 'spans': [{'text': 'Title\nand More'}]}}
            ]
        }
    );
});


test('markdownParse, heading alternate syntax following list', (t) => {
    const markdown = markdownParse(`
- Title
and more
=====
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, heading alternate syntax beyond code block', (t) => {
    const markdown = markdownParse(`
Title
    =====
`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {'parts': [
            {'paragraph': {
                'spans': [{'text': 'Title\n    ====='}]
            }}
        ]}
    );
});


test('markdownParse, list', (t) => {
    const markdown = markdownParse(`
- item 1

  item 1.2

* item 2
another
+ item 3`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, ordered list', (t) => {
    const markdown = markdownParse(`
1. item 1

   item 1.2

* item 2
another
+ item 3`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, list nested', (t) => {
    const markdown = markdownParse(`
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
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, code block', (t) => {
    const markdown = markdownParse(`
This is some code:

    code 1
    code 2

    code 3

Cool, huh?`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is some code:'}]}},
                {'codeBlock': {'lines': ['code 1', 'code 2', '', 'code 3']}},
                {'paragraph': {'spans': [{'text': 'Cool, huh?'}]}}
            ]
        }
    );
});


test('markdownParse, code block with fenced code block text', (t) => {
    const markdown = markdownParse(`
This is a fenced code block:

    ~~~ javascript
    code 1
    code 2

    code 3
    ~~~

Cool, huh?`);
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {'spans': [{'text': 'This is a fenced code block:'}]}},
                {'codeBlock': {'lines': [
                    '~~~ javascript',
                    'code 1',
                    'code 2',
                    '',
                    'code 3',
                    '~~~'
                ]}},
                {'paragraph': {'spans': [{'text': 'Cool, huh?'}]}}
            ]
        }
    );
});


test('markdownParse, fenced code block', (t) => {
    const markdown = markdownParse(`
This is some code:

\`\`\` javascript
foo();
bar();
\`\`\`
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, empty fenced code block', (t) => {
    const markdown = markdownParse(`
This is some code:

\`\`\` javascript
\`\`\`
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, empty, end-of-file fenced code block', (t) => {
    const markdown = markdownParse(`
This is some code:

\`\`\` javascript`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, code block fenced no language', (t) => {
    const markdown = markdownParse(`
This is some code:

\`\`\`
foo();
bar();
\`\`\`
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, code block nested', (t) => {
    const markdown = markdownParse(`
- This is some code:

  \`\`\`
  foo();
  bar();
  \`\`\`
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, spans', (t) => {
    const markdown = markdownParse(`
These are some basic styles: **bold**, *italic*, ***bold-italic***.

This is a [link](https://foo.com) and so is [this](https://bar.com "Bar").

This is another link: <https://foo.com>

This is an ![image](https://foo.com/foo.jpg) and so is ![this](https://bar.com/bar.jpg "Bar").
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, nested spans', (t) => {
    const markdown = markdownParse(`
This is a [link **with *formatting***](https://foo.com)
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, spans spaces', (t) => {
    const markdown = markdownParse(`
***no *** *** no*** **no ** ** no** *no * * no*
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, link multiline', (t) => {
    const markdown = markdownParse('[text\ntext](href://foo.com "text\ntext")');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'link': {'href': 'href://foo.com', 'spans': [{'text': 'text\ntext'}], 'title': 'text\ntext'}}
                    ]
                }}
            ]
        }
    );
});


test('markdownParse, italic multiline', (t) => {
    const markdown = markdownParse('*text\ntext*');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'style': {'spans': [{'text': 'text\ntext'}], 'style': 'italic'}}
                    ]
                }}
            ]
        }
    );
});


test('markdownParse, bold multiline', (t) => {
    const markdown = markdownParse('**text\ntext**');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'style': {'spans': [{'text': 'text\ntext'}], 'style': 'bold'}}
                    ]
                }}
            ]
        }
    );
});


test('markdownParse, bold-italic multiline', (t) => {
    const markdown = markdownParse('***text\ntext***');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(
        markdown,
        {
            'parts': [
                {'paragraph': {
                    'spans': [
                        {'style': {'spans': [{'style': {'spans': [{'text': 'text\ntext'}], 'style': 'italic'}}], 'style': 'bold'}}
                    ]
                }}
            ]
        }
    );
});


test('markdownParse, line breaks', (t) => {
    const markdown = markdownParse(`
This is a line break  
  this is not
and this is  

This is another paragraph.
`);
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = markdownParse('\\ \\* \\_ \\{ \\} \\[ \\] **bol\\.d** \\( \\) \\# \\+ \\- \\. \\! \\a');
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, link escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = markdownParse('[tex\]t](hre\.f "titl\.e")');
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, link href space', (t) => {
    const markdown = markdownParse('[text](hre f)');
    validateType(markdownModel.types, 'Markdown', markdown);
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


test('markdownParse, link href alternate space', (t) => {
    const markdown = markdownParse('<hre f>');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '<hre f>'}]}}]});
});


test('markdownParse, link href alternate space begin', (t) => {
    const markdown = markdownParse('< href>');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '< href>'}]}}]});
});


test('markdownParse, link href alternate space end', (t) => {
    const markdown = markdownParse('<href >');
    validateType(markdownModel.types, 'Markdown', markdown);
    t.deepEqual(markdown, {'parts': [{'paragraph': {'spans': [{'text': '<href >'}]}}]});
});


test('markdownParse, image escapes', (t) => {
    /* eslint-disable-next-line no-useless-escape */
    const markdown = markdownParse('![al\]t](sr\.c "titl\.e")');
    validateType(markdownModel.types, 'Markdown', markdown);
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
