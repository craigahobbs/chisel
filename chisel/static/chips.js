var chips = (function () {
    var module = {};

    module.render = function (parent, elems, clear) {
        if (clear) {
            parent.innerHTML = '';
        }
        for (iElem = 0; iElem < elems.length; iElem++) {
            parent.appendChild(module.node(elems[iElem]));
        }
        return parent;
    };

    module.node = function (elem) {
        var node = elem.text ? document.createTextNode(elem.text) : document.createElement(elem.tag);
        if (elem.attrs) {
            for (var attr in elem.attrs) {
                node.setAttribute(attr, elem.attrs[attr]);
            }
        }
        if (elem.elems) {
            for (var iElem = 0; iElem < elem.elems.length; iElem++) {
                node.appendChild(module.node(elem.elems[iElem]));
            }
        }
        return node;
    };

    module.elem = function (tag, attrsOrElems, elems) {
        var attrs = (Object.prototype.toString.call(attrsOrElems) === '[object Object]') ? attrsOrElems : undefined;
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

    return module;
}());
