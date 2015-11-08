var chisel;
if (undefined === chisel) {
    chisel = {};
}
chisel.doc = (function () {
    var module = {};

    module.index = function (body, params) {
        chips.xhr('get', '/docIndexApi', true, {
            onok: function (index) {
                var title = window.location.host;
                document.title = title;

                chips.render(body, [
                    chips.elem('h1', [
                        chips.text(title),
                    ]),
                    chips.elem('ul', {'class': 'chsl-request-list'}, [
                        chips.elem('li', index.names.map(function (name) {
                            return chips.elem('li', [
                                chips.elem('a', {'href': chips.href({'name': name})}, [
                                    chips.text(name),
                                ]),
                            ]);
                        })),
                    ]),
                ], true);
            },
        });
    };

    module.request = function (body, params) {
        chips.xhr('get', '/docApi', true, {
            params: params,
            onok: function (request) {
                document.title = params.name;

                // Add the nav bar
                var bodyElems = [];
                if (params.nonav !== 'true') {
                    bodyElems.push(chips.elem('div', {'class': 'chsl-header'}, [
                        chips.elem('a', {'href': chips.href()}, [
                            chips.text('Back to documentation index'),
                        ]),
                    ]));
                }

                // Add the title
                bodyElems.push(chips.elem('h1', [
                    chips.text(request.name),
                ]));

                // Add the request doc text
                bodyElems.push(textElem(request.doc));

                // Add the notes section
                var notesElem = chips.elem('div', {'class': 'chsl-notes'});
                bodyElems.push(notesElem);

                // Add the URL note
                if (request.urls.length) {
                    notesElem.elems.push(chips.elem('div', {'class': 'chsl-note'}, [
                        chips.elem('p', [
                            chips.elem('b', [
                                chips.text('Note: '),
                            ]),
                            chips.text('The request is exposed at the following URL' + (request.urls.length > 1 ? 's:' : ':')),
                            chips.elem('ul', request.urls.map(function (url) {
                                return chips.elem('li', [
                                    chips.elem('a', {'href': url.url}, [
                                        chips.text(url.method ? url.method + ' ' + url.url : url.url),
                                    ]),
                                ]);
                            })),
                        ]),
                    ]));
                }

                // Action?
                if (request.action) {
                    // Action input and output struct sections
                    bodyElems.push(actionInputOutputElem(request.action.input, 'h2', 'Input Parameters', 'The action has no input parameters.'));
                    if (request.action.output) {
                        bodyElems.push(actionInputOutputElem(request.action.output, 'h2', 'Output Parameters', 'The action has no output parameters.'));
                    } else {
                        notesElem.elems.push(chips.elem('div', {'class': 'chsl-note'}, [
                            chips.elem('p', [
                                chips.elem('b', [
                                    chips.text('Note: '),
                                ]),
                                chips.text('The action has a non-default response. See documentation for details.'),
                            ]),
                        ]));
                    }
                }

                // Render
                chips.render(body, bodyElems, true);
            }
        });
    };

    function textElem(lines) {
        var divElems = [];
        var paragraph = [];
        if (chips.isArray(lines)) {
            for (iLine = 0; iLine < lines.length; iLine++) {
                if (lines[iLine].length) {
                    paragraph.push(lines[iLine]);
                } else if (paragraph.length) {
                    divElems.push(chips.elem('p', chips.text(paragraph.join('\n'))));
                    paragraph = [];
                }
            }
        } else if (lines) {
            paragraph.push(lines);
        }
        if (paragraph.length) {
            divElems.push(chips.elem('p', [chips.text(paragraph.join('\n'))]));
        }
        return divElems.length ? chips.elem('div', {'class': 'chsl-text'}, divElems) : null;
    }

    function typeHref(type) {
        if (type.typedef && type.typedef.name) {
            return 'typedef_' + type.typedef.name;
        } else if (type['enum'] && type['enum'].name) {
            return 'enum_' + type['enum'].name;
        } else if (type.struct && type.struct.name) {
            return 'struct_' + type.struct.name;
        }
        return null;
    }

    function actionInputOutputElem(type, titleTag, title, emptyText) {
        if (type.dict) {
            //!!
        }
        return structElem(type.struct, titleTag, title, emptyText);
    }

    function structElem(struct, titleTag, title, emptyText) {
        titleTag = titleTag || 'h3';
        title = title || ((struct.union ? 'union ' : 'struct ') + struct.name);
        emptyText = emptyText || 'The struct is empty.';
        var elems = [];

        // Section title
        elems.push(chips.elem(titleTag, {'id': typeHref(struct)}, [
            chips.elem('a', {'class': 'linktarget'}, [
                chips.text(title),
            ]),
        ]));
        elems.push(textElem(struct.doc));

        // Struct members
        if (struct.members.length) {
            //!!
        } else {
            elems.push(textElem(emptyText));
        }

        return elems;
    }

    module.main = function (body) {
        // Listen for hash parameter changes
        window.onhashchange = function () {
            module.main(body);
        };

        // Index page?
        var params = chips.decodeParams();
        if (undefined !== params.name) {
            module.request(body, params);
        } else {
            module.index(body, params);
        }
    };

    return module;
}());
