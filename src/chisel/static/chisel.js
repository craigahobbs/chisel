export const nbsp = String.fromCharCode(160);

export function render(parent, elems, clear=true) {
    if (clear) {
        parent.innerHTML = '';
    }
    return appendNodes(parent, elems);
}

export function node(elem) {
    let node_ = elem.text ? document.createTextNode(elem.text) : document.createElement(elem.tag);
    if (elem.attrs) {
        for (let attr in elem.attrs) {
            let value = elem.attrs[attr];
            if (value) {
                node_.setAttribute(attr, value);
            }
        }
    }
    return appendNodes(node_, elem.elems);
}

function appendNodes(parent, elems) {
    if (Array.isArray(elems)) {
        for (let iElem = 0; iElem < elems.length; iElem++) {
            appendNodes(parent, elems[iElem]);
        }
    } else if (elems) {
        parent.appendChild(node(elems));
    }
    return parent;
}

export function elem(tag, attrsOrElems, elems) {
    let attrs = isDict(attrsOrElems) ? attrsOrElems : undefined;
    return {
        tag: tag,
        attrs: attrs || {},
        elems: (attrs ? elems : attrsOrElems) || [],
    };
}

export function text(text_) {
    return {
        text: text_,
    };
}

export function href(hashParams, params, path) {
    hashParams = encodeParams(hashParams);
    params = encodeParams(params);
    path = path ? path : window.location.pathname;
    if (hashParams === null && params === null) {
        return path + '#';
    } else if (hashParams === null && params !== null) {
        return path + '?' + params;
    } else if (hashParams !== null && params === null) {
        return path + '#' + hashParams;
    }
    return path + '?' + params + '#' + hashParams;
}

export function encodeParams(params) {
    let items = [];
    if (undefined !== params) {
        let name;
        for (name in params) {
            if (params[name] !== null) {
                items.push(encodeURIComponent(name) + '=' + encodeURIComponent(params[name]));
            }
        }
        for (name in params) {
            if (params[name] === null) {
                items.push(encodeURIComponent(name));
            }
        }
    }
    return items.length ? items.join('&') : null;
}

export function decodeParams(paramString) {
    let params = {},
        r = /([^&;=]+)=?([^&;]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(/\+/g, " ")); },
        q = (paramString || window.location.hash.substring(1)),
        e;

    while ((e = r.exec(q)) !== null) {
        params[d(e[1])] = d(e[2]);
    }

    return params;
}

export function xhr(method, url, args) {
    args = args || {};
    let xhr_ = new XMLHttpRequest();
    xhr_.open(method, href(null, args.params, url));
    xhr_.responseType = args.responseType || 'json';
    xhr_.onreadystatechange = function () {
        if (XMLHttpRequest.DONE === xhr_.readyState) {
            if (200 === xhr_.status) {
                if (args.onok) {
                    args.onok(xhr_.response);
                }
            } else {
                if (args.onerror) {
                    args.onerror(xhr_.response);
                }
            }
        }
    };
    xhr_.send();
}

export function isDict(obj) {
    return !!obj && obj.constructor == Object;
}
