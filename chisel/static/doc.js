var chisel;
if (undefined === chisel) {
    chisel = {};
}
chisel.doc = (function () {
    var module = {};

    module.index = function (body, params) {
        // Set the title
        var title = window.location.host;
        document.title = title;
        chips.root(body, []);

        // Build the index
        chips.xhr('get', '/docIndexApi', true, {
            onok: function (index) {
                chips.root(body, [
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
                ]);
            },
        });
    };

    module.request = function (body, params) {
        // Set the title
        document.title = params.name;
        chips.root(body, []);

        // Get the request info
        chips.xhr('get', '/docApi', true, {
            params: params,
            onok: function (request) {
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
                //!!

                // Add the URLs
                if (request.urls.length) {
                    bodyElems.push(chips.elem('div', {'class': 'chsl-note'}, [
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
                    //!!
                }

                chips.root(body, bodyElems);
            }
        });
    };

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
