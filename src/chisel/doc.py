# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

"""
Chisel documentation application
"""

from collections import defaultdict

from schema_markdown import get_referenced_types
from schema_markdown.type_model import TYPE_MODEL

from .action import Action, ActionError
from .request import RedirectRequest, StaticRequest


# The chisel-doc application's HTML stub
CHISEL_DOC_HTML = b'''\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Chisel</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://craigahobbs.github.io/markdown-up/markdown-model.css">
        <link rel="stylesheet" href="https://craigahobbs.github.io/markdown-up/app.css">
    </head>
    <body>
    </body>
    <script type="module">
        import {MarkdownUp} from 'https://craigahobbs.github.io/markdown-up/lib/app.js';
        const app = new MarkdownUp(window, {
            'markdownText': `\
~~~ markdown-script
async function indexPage()
    # Fetch the documentation index API
    docIndex = fetch('doc_index')
    title = arrayGet(docIndex, 'title')
    groups = arrayGet(docIndex, 'groups')
    groupNames = objectKeys(groups)

    # Render the index page
    setDocumentTitle(title)
    markdownPrint('# ' + markdownEncode(title))
    ixGroup = 0
    groupLoop:
        groupName = arrayGet(groupNames, ixGroup)
        groupRequests = objectGet(groups, groupName)
        markdownPrint('', '### ' + markdownEncode(groupName))
        ixRequest = 0
        requestLoop:
            requestName = arrayGet(groupRequests, ixRequest)
            markdownPrint('', '[' + markdownEncode(requestName) + "](#var.vName='" + encodeURIComponent(requestName) + "')")
            ixRequest = ixRequest + 1
        jumpif (ixRequest < arrayLength(groupRequests)) requestLoop
        ixGroup = ixGroup + 1
    jumpif (ixGroup < arrayLength(groupNames)) groupLoop
endfunction

async function requestPage(typeName)
    # Fetch the request API
    docRequest = fetch('doc_request?name=' + encodeURIComponent(typeName))
    doc = objectGet(docRequest, 'doc')
    urls = objectGet(docRequest, 'urls')
    types = objectGet(docRequest, 'types')

    # Render the request page
    setDocumentTitle(typeName)
    markdownPrint('[Index](#var=)')

    # Action request?
    jumpif (types == null) nonAction
    schemaPrint(types, typeName, urls)
    return

    # Non-action request
    nonAction:
    markdownPrint('', '# ' + markdownEncode(typeName))
    if(doc != null, markdownPrint('', doc))
    jumpif(urls == null || arrayLength(urls) == 0) noURLs
        markdownPrint('', '**Note:** The request is exposed at the following ' + if(arrayLength(urls) == 1, 'URL:', 'URLs:'))
        ixURL = 0
        urlLoop:
            requestURL = arrayGet(urls, ixURL)
            method = objectGet(requestURL, 'method')
            url = objectGet(requestURL, 'url')
            markdownPrint('', fromCharCode(160, 160) + '[' + markdownEncode(method) + ' ' + markdownEncode(url) + '](' + url + ')')
            ixURL = ixURL + 1
        jumpif (ixURL < arrayLength(urls)) urlLoop
    noURLs:
endfunction

if(vName != null, requestPage(vName), indexPage())
~~~
`});
        app.run();
    </script>
</html>
'''


def create_doc_requests(requests=None, root_path='/doc', api=True, app=True):
    """
    Yield a series of requests for use with :meth:`~chisel.Application.add_requests` comprising the Chisel
    documentation application. By default, the documenation application is hosted at "/doc/".

    :param requests: A list of requests or None to use the application's requests
    :type requests: list(~chisel.Request)
    :param str root_path: The documentation application URL root path. The default is "/doc".
    :param bool api: If True, include the documentation APIs. Two documentation APIs are added,
        "/doc/doc_index" and "`/doc/doc_request <doc/#name=chisel_doc_request>`__".
    :param bool app: If True, include the documentation client application.
    :returns: Generator of :class:`~chisel.Request`
    """

    if api:
        yield DocIndex(requests=requests, urls=(('GET', root_path + '/doc_index'),))
        yield DocRequest(requests=requests, urls=(('GET', root_path + '/doc_request'),))
    if app:
        yield RedirectRequest((('GET', root_path),), root_path + '/', doc_group='Documentation')
        yield StaticRequest(
            'chisel_doc',
            CHISEL_DOC_HTML,
            urls=(('GET', root_path + '/'), ('GET', root_path + '/index.html')),
            doc_group='Documentation'
        )


class DocIndex(Action):
    """
    The documentation index API. This API provides all the information the documentation application needs to render the
    index page.

    :param requests: A list of requests or None to use the application's requests
    :type requests: dict(str, ~chisel.Request)
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    """

    __slots__ = ('requests',)

    SPEC = '''\
group "Documentation"

# A non-empty string array
typedef string[len > 0] StringArray

# Get the documentation index
action chisel_doc_index
    output
        # The documentation index title
        string title

        # The dictionary of documentation group titles to array of request names
        StringArray{} groups
'''

    def __init__(self, requests=None, urls=(('GET', '/doc_index'),)):
        super().__init__(self._doc_index, name='chisel_doc_index', urls=urls, spec=self.SPEC)
        if requests is not None:
            self.requests = {request.name: request for request in requests}
        else:
            self.requests = None

    def _doc_index(self, ctx, unused_req):
        requests = self.requests if self.requests is not None else ctx.app.requests
        groups = defaultdict(list)
        for request in requests.values():
            groups[request.doc_group or 'Uncategorized'].append(request.name)
        return {
            'title': ctx.environ['HTTP_HOST'],
            'groups': {group: sorted(names) for group, names in groups.items()}
        }


class DocRequest(Action):
    """
    The documentation request API. This API provides all the information the documentation applicaton needs to render
    the request documentation page. The documentation request API's documentation is `here
    <doc/#name=chisel_doc_request>`__.

    :param requests: A list of requests or None to use the application's requests
    :type requests: list(~chisel.Request)
    :param list(tuple) urls: The list of URL method/path tuples. The first value is the HTTP request method (e.g. 'GET')
        or None to match any. The second value is the URL path or None to use the default path.
    """

    __slots__ = ('requests',)

    SPEC = '''
group "Documentation"

# Struct representing a request's URL information
struct RequestURL

    # The request URL HTTP request method. If not present, all HTTP request methods are accepted.
    optional string method

    # The request URL path
    string url

# Get a request's documentation information
action chisel_doc_request
    query
        # The request name
        string name

    output
        # The request name
        string name

        # The documentation markdown text lines
        optional string[] doc

        # The array of URL paths where the request is hosted.
        optional RequestURL[] urls

        # The map of the action's type name's to type models. This member is only present for JSON APIs.
        optional Types types

    errors
        # The request name is unknown
        UnknownName
'''

    def __init__(self, requests=None, urls=(('GET', '/doc_request'),)):
        super().__init__(self._doc_request, name='chisel_doc_request', urls=urls, types=dict(TYPE_MODEL), spec=self.SPEC)
        if requests is not None:
            #: Optional list of requests to document or None. If None, the applications request collection is used.
            self.requests = {request.name: request for request in requests}
        else:
            self.requests = None

    def _doc_request(self, ctx, req):
        requests = self.requests if self.requests is not None else ctx.app.requests
        request = requests.get(req['name'])
        if request is None:
            raise ActionError('UnknownName')

        response = {
            'name': request.name
        }
        if request.urls:
            response['urls'] = [self._url_dict(method, url) for method, url in request.urls]
        if isinstance(request, Action):
            response['types'] = get_referenced_types(request.types, request.name)
        elif request.doc is not None:
            response['doc'] = [request.doc] if isinstance(request.doc, str) else request.doc

        return response

    @staticmethod
    def _url_dict(method, url):
        url_dict = {'url': url}
        if method is not None:
            url_dict['method'] = method
        return url_dict
