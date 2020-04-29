// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

export const nbsp = String.fromCharCode(160);
export const endash = String.fromCharCode(8211);

export function render(parent, elems, clear = true) {
    if (clear) {
        parent.innerHTML = '';
    }
    return appendElements(parent, elems);
}

export function createElement(element) {
    const browserElement = element.text ? document.createTextNode(element.text) : document.createElementNS(element.ns, element.tag);
    let {attrs} = element;
    if (attrs) {
        const callback = attrs._callback;
        if (callback !== undefined) {
            attrs = {...attrs, '_callback': undefined};
        }
        for (const [attr, value] of Object.entries(attrs)) {
            if (value !== undefined) {
                browserElement.setAttribute(attr, value);
            }
        }
        if (callback !== undefined) {
            callback(browserElement);
        }
    }
    return appendElements(browserElement, element.elems);
}

function appendElements(parent, elems) {
    if (Array.isArray(elems)) {
        for (let iElem = 0; iElem < elems.length; iElem++) {
            appendElements(parent, elems[iElem]);
        }
    } else if (elems) {
        parent.appendChild(createElement(elems));
    }
    return parent;
}

export function elem(tag, attrsOrElems, elems, ns = 'http://www.w3.org/1999/xhtml') {
    const attrs = isDict(attrsOrElems) ? attrsOrElems : undefined;
    return {
        'tag': tag,
        'attrs': attrs || {},
        'elems': (attrs ? elems : attrsOrElems) || [],
        'ns': ns
    };
}

export function svg(tag, attrsOrElems, elems) {
    return elem(tag, attrsOrElems, elems, 'http://www.w3.org/2000/svg');
}

export function text(text_) {
    return {
        'text': text_
    };
}

export function href(hashParams, params, path = window.location.pathname) {
    const hashParamsStr = encodeParams(hashParams);
    const paramsStr = encodeParams(params);
    if (hashParamsStr === null && paramsStr === null) {
        return `${path}#`;
    } else if (hashParamsStr === null && paramsStr !== null) {
        return `${path}?${paramsStr}`;
    } else if (hashParamsStr !== null && paramsStr === null) {
        return `${path}#${hashParamsStr}`;
    }
    return `${path}?${paramsStr}#${hashParamsStr}`;
}

export function encodeParams(params) {
    const items = [];
    if (undefined !== params) {
        const names = Object.keys(params).sort();
        names.forEach((name) => {
            if (params[name] !== null && params[name] !== undefined) {
                items.push(`${encodeURIComponent(name)}=${encodeURIComponent(params[name])}`);
            }
        });
        names.forEach((name) => {
            if (params[name] === null) {
                items.push(encodeURIComponent(name));
            }
        });
    }
    return items.length ? items.join('&') : null;
}

export function decodeParams(paramString = window.location.hash.substring(1)) {
    const rNextKeyValue = /(?<key>[^&=]+)=?(?<value>[^&]*)/g;

    let match;
    const params = {};
    while ((match = rNextKeyValue.exec(paramString)) !== null) {
        params[decodeURIComponent(match.groups.key)] = decodeURIComponent(match.groups.value);
    }

    return params;
}

export function xhr(method, url, args = {}) {
    const xhr_ = new XMLHttpRequest();
    xhr_.open(method, href(undefined, args.params, url));
    xhr_.responseType = args.responseType || 'json';
    xhr_.onreadystatechange = () => {
        if (XMLHttpRequest.DONE === xhr_.readyState) {
            if (xhr_.status === 200) {
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
    return !!obj && obj.constructor === Object;
}
