var chips = (function () {
    var module = {};

    module.style = function (href) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = href;

        document.head.appendChild(link);
    };

    module.root = function (parent, children) {
        parent.innerHTML = '';
        for (var i = 0; i < children.length; i++) {
            parent.appendChild(children[i]);
        }
        return parent;
    };

    module.elem = function (tag, attrsOrChildren, children) {
        var elem = document.createElement(tag);
        var attrs = (Object.prototype.toString.call(attrsOrChildren) === '[object Object]') ? attrsOrChildren : undefined;
        children = attrs ? children : attrsOrChildren;
        if (typeof attrs !== 'undefined') {
            for	(var attr in attrs) {
                elem.setAttribute(attr, attrs[attr]);
            }
        }
        if (typeof children !== 'undefined') {
            for (var i = 0; i < children.length; i++) {
                elem.appendChild(children[i]);
            }
        }
        return elem;
    };

    module.text = function (text) {
        return document.createTextNode(text);
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
