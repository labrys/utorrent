import re
from http.cookiejar import CookieJar
from io import StringIO
from urllib.parse import urlencode, urljoin
from urllib.request import (
    HTTPBasicAuthHandler,
    HTTPCookieProcessor,
    Request,
    build_opener,
    install_opener,
)

from .upload import MultiPartForm

try:
    import json
except ImportError:
    import simplejson as json


class UTorrentClient:

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.opener = self._make_opener('uTorrent', base_url, username, password)
        self.token = self._get_token()
        # TODO refresh token, when necessary

    @staticmethod
    def _make_opener(realm, base_url, username, password):
        """HTTP Basic Auth and cookie support for token verification."""
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm=realm,
            uri=base_url,
            user=username,
            passwd=password,
        )
        opener = build_opener(auth_handler)
        install_opener(opener)

        cookie_jar = CookieJar()
        cookie_handler = HTTPCookieProcessor(cookie_jar)

        handlers = [auth_handler, cookie_handler]
        opener = build_opener(*handlers)
        return opener

    def _get_token(self):
        url = urljoin(self.base_url, 'token.html')
        response = self.opener.open(url)
        token_re = "<div id='token' style='display:none;'>([^<>]+)</div>"
        match = re.search(token_re, str(response.read()))
        return match.group(1)

    def list(self, **kwargs):
        params = [('list', '1')]
        params += kwargs.items()
        return self._action(params)

    def start(self, *hashes):
        params = [('action', 'start')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def stop(self, *hashes):
        params = [('action', 'stop')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def pause(self, *hashes):
        params = [('action', 'pause')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def forcestart(self, *hashes):
        params = [('action', 'forcestart')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def getfiles(self, cur_hash):
        params = [('action', 'getfiles'), ('hash', cur_hash)]
        return self._action(params)

    def getprops(self, cur_hash):
        params = [('action', 'getprops'), ('hash', cur_hash)]
        return self._action(params)

    def setprops(self, cur_hash, **kvpairs):
        params = [('action', 'setprops'), ('hash', cur_hash)]
        for k, v in kvpairs.items():
            params.append(('s', k))
            params.append(('v', v))

        return self._action(params)

    def setprio(self, cur_hash, priority, *files):
        params = [('action', 'setprio'), ('hash', cur_hash), ('p', str(priority))]
        for file_index in files:
            params.append(('f', str(file_index)))

        return self._action(params)

    def addfile(self, filename, filepath=None, data=None):
        params = [('action', 'add-file')]

        form = MultiPartForm()
        if filepath is not None:
            with open(filepath, 'rb') as file_handler:
                form.add_file('torrent_file', filename.encode('utf-8'), file_handler)
        else:
            with StringIO(data) as file_handler:
                form.add_file('torrent_file', filename.encode('utf-8'), file_handler)

        return self._action(params, str(form), form.get_content_type())

    def addurl(self, url):
        params = [('action', 'add-url'), ('s', url)]
        self._action(params)

    def remove(self, *hashes):
        params = [('action', 'remove')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def removedata(self, *hashes):
        params = [('action', 'removedata')]
        for cur_hash in hashes:
            params.append(('hash', cur_hash))
        return self._action(params)

    def _action(self, params, body=None, content_type=None):
        # about token, see https://github.com/bittorrent/webui/wiki/TokenSystem
        url = self.base_url + '?token=' + self.token + '&' + urlencode(params)
        request = Request(url)

        if body:
            request.data = body
            request.add_header('Content-length', len(body))
        if content_type:
            request.add_header('Content-type', content_type)

        response = self.opener.open(request)
        return response.code, json.loads(response.read())
