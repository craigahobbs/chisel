var chips = (function () {
    var module = {};

    module.nbsp = String.fromCharCode(160);

    module.render = function (parent, elems, clear) {
        if (clear) {
            parent.innerHTML = '';
        }
        return appendNodes(parent, elems);
    };

    module.node = function (elem) {
        var node = elem.text ? document.createTextNode(elem.text) : document.createElement(elem.tag);
        if (elem.attrs) {
            for (var attr in elem.attrs) {
                var value = elem.attrs[attr];
                if (value) {
                    node.setAttribute(attr, value);
                }
            }
        }
        return appendNodes(node, elem.elems);
    };

    function appendNodes(parent, elems) {
        if (module.isArray(elems)) {
            for (var iElem = 0; iElem < elems.length; iElem++) {
                appendNodes(parent, elems[iElem]);
            }
        } else if (elems) {
            parent.appendChild(module.node(elems));
        }
        return parent;
    }

    module.elem = function (tag, attrsOrElems, elems) {
        var attrs = module.isObject(attrsOrElems) ? attrsOrElems : undefined;
        return {
            tag: tag,
            attrs: attrs || {},
            elems: (attrs ? elems : attrsOrElems) || [],
        };
    };

    module.text = function (text) {
        return {
            text: text,
        };
    };

    module.ref = function (id) {
        return document.getElementById(id);
    };

    module.href = function(hashParams, params, path) {
        hashParams = module.encodeParams(hashParams);
        params = module.encodeParams(params);
        path = path ? path : window.location.pathname;
        if (hashParams === null && params === null) {
            return path;
        } else if (hashParams === null && params !== null) {
            return path + '?' + params;
        } else if (hashParams !== null && params === null) {
            return path + '#' + hashParams;
        }
        return path + '?' + params + '#' + hashParams;
    };

    module.encodeParams = function(params) {
        var items = [];
        if (undefined !== params) {
            for (var name in params) {
                items.push(encodeURIComponent(name) + '=' + encodeURIComponent(params[name]));
            }
        }
        return items.length ? items.join('&') : null;
    };

    module.decodeParams = function (paramString) {
        var params = {},
            r = /([^&;=]+)=?([^&;]*)/g,
            d = function (s) { return decodeURIComponent(s.replace(/\+/g, " ")); },
            q = (paramString || window.location.hash.substring(1)),
            e;

        while ((e = r.exec(q)) !== null) {
            params[d(e[1])] = d(e[2]);
        }

        return params;
    };

    module.xhr = function (method, url, async, args) {
        args = args || {};
        var xhr = new XMLHttpRequest();
        xhr.open(method, module.href(null, args.params, url), async);
        xhr.responseType = args.responseType || 'json';
        xhr.onreadystatechange = function () {
            if (XMLHttpRequest.DONE === xhr.readyState) {
                if (200 === xhr.status) {
                    if (args.onok) {
                        args.onok(xhr.response);
                    }
                } else {
                    if (args.onerror) {
                        args.onerror(xhr.response);
                    }
                }
            }
        };
        xhr.send();
    };

    module.isArray = function (obj) {
        return Object.prototype.toString.call(obj) === '[object Array]';
    };

    module.isObject = function (obj) {
        return Object.prototype.toString.call(obj) === '[object Object]';
    };

    return module;
}());
