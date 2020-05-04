// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

export const nbsp = String.fromCharCode(160);

export function render(parent, elems, clear = true) {
    if (clear) {
        parent.innerHTML = '';
    }
    return appendElements(parent, elems);
}

function appendElements(parent, elems) {
    if (Array.isArray(elems)) {
        for (let iElem = 0; iElem < elems.length; iElem++) {
            appendElements(parent, elems[iElem]);
        }
    } else if (elems !== null && typeof elems !== 'undefined') {
        parent.appendChild(createElement(elems));
    }
    return parent;
}

function createElement(element) {
    let browserElement;
    if (element.text) {
        browserElement = document.createTextNode(element.text);
    } else if (typeof element.ns !== 'undefined') {
        browserElement = document.createElementNS(element.ns, element.tag);
    } else {
        browserElement = document.createElement(element.tag);
    }
    if (typeof element.attrs !== 'undefined') {
        for (const [attr, value] of Object.entries(element.attrs)) {
            if (attr !== '_callback' && value !== null && typeof value !== 'undefined') {
                browserElement.setAttribute(attr, value);
            }
        }
        if (element.attrs._callback !== null && typeof element.attrs._callback !== 'undefined') {
            element.attrs._callback(browserElement);
        }
    }
    return appendElements(browserElement, element.elems);
}

export function elem(tag, attrsOrElems = null, elems = null, ns = null) {
    const element = {
        'tag': tag
    };
    const attrs = attrsOrElems !== null && !Array.isArray(attrsOrElems) ? attrsOrElems : null;
    const elemsActual = attrs === null ? attrsOrElems : elems;
    if (attrs !== null) {
        element.attrs = attrs;
    }
    if (elemsActual !== null) {
        element.elems = elemsActual;
    }
    if (ns !== null) {
        element.ns = ns;
    }
    return element;
}

export function svg(tag, attrsOrElems, elems) {
    return elem(tag, attrsOrElems, elems, 'http://www.w3.org/2000/svg');
}

export function text(text_) {
    return {
        'text': text_
    };
}

export function href(hash = null, query = null, pathname = null) {
    let hashStr = '';
    if (hash !== null) {
        hashStr = `#${encodeParams(hash)}`;
    } else if (query === null) {
        hashStr = '#';
    }

    let queryStr = '';
    if (query !== null) {
        queryStr = `?${encodeParams(query)}`;
        if (queryStr === '?') {
            queryStr = '';
        }
    }

    let pathname_ = pathname;
    if (pathname_ === null) {
        pathname_ = window.location.pathname;
    }

    return `${pathname_}${queryStr}${hashStr}`;
}

export function encodeParams(params) {
    const items = [];
    Object.keys(params).sort().forEach((name) => {
        if (params[name] !== null && typeof params[name] !== 'undefined') {
            items.push(`${encodeURIComponent(name)}=${encodeURIComponent(params[name])}`);
        }
    });
    return items.join('&');
}

export function decodeParams(paramStr = null) {
    let paramStr_ = paramStr;
    if (paramStr_ === null) {
        paramStr_ = window.location.hash.substring(1);
    }

    const rNextKeyValue = /([^&=]+)=?([^&]*)/g;
    let match;
    const params = {};
    while ((match = rNextKeyValue.exec(paramStr_)) !== null) {
        params[decodeURIComponent(match[1])] = decodeURIComponent(match[2]);
    }
    return params;
}

export function xhr(method, url, args = {}) {
    const xhr_ = new XMLHttpRequest();
    xhr_.open(method, href(null, args.params, url));
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
