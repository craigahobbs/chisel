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
                if (request.doc) {
                    bodyElems.push(textElem(request.doc));
                }

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

                // Add the custom action response note
                if (request.action && !request.action.output) {
                    notesElem.elems.push(chips.elem('div', {'class': 'chsl-note'}, [
                        chips.elem('p', [
                            chips.elem('b', [
                                chips.text('Note: '),
                            ]),
                            chips.text('The action has a non-default response. See documentation for details.'),
                        ]),
                    ]));
                }

                // Action?
                if (request.action) {
                    //!!
                }

                // Render
                chips.render(body, bodyElems, true);
            }
        });
    };

    function textElem(lines) {
        var divElems = [];
        var paragraph = [];
        for (iLine = 0; iLine < lines.length; iLine++) {
            if (lines[iLine].length) {
                paragraph.push(lines[iLine]);
            } else if (paragraph.length) {
                divElems.push(chips.elem('p', chips.text(paragraph.join('\n'))));
                paragraph = [];
            }
        }
        if (paragraph.length) {
            divElems.push(chips.elem('p', [chips.text(paragraph.join('\n'))]));
        }
        return chips.elem('div', {'class': 'chsl-text'}, divElems);
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
