from M2Crypto.m2xmlrpclib import ServerProxy, SSL_Transport
from M2Crypto import m2urllib,httpslib
import sys, string, base64
import xmlrpclib

# have to edit M2Crypto.httpslib.py, line 25 and 100, change to this
#         if sys.version_info>(2,2,1):

class MyTransport(SSL_Transport):

    def check_cert(self, handle):
        if  handle._conn.sock is None:
            handle._conn.connect()
            # only need to check here
            print "would check cert here",handle._conn.sock.get_peer_cert()

    def request(self, host, handler, request_body, verbose=0):
        # Handle username and password.
        user_passwd, host_port = m2urllib.splituser(host)
        _host, _port = m2urllib.splitport(host_port)
        h = httpslib.HTTPS(_host, int(_port), ssl_context=self.ssl_ctx)

        if verbose:
            h.set_debuglevel(1)

        # Check cert ::Addition by RogerB
        self.check_cert(h)

        # What follows is as in xmlrpclib.Transport. (Except the authz bit.)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", _host)

        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader('Keep-Alive', '1')
        h.putheader("Content-Type", "text/xml")
        h.putheader("Content-Length", str(len(request_body)))

        # Authorisation.
        if user_passwd is not None:
            auth=string.strip(base64.encodestring(user_passwd))
            h.putheader('Authorization', 'Basic %s' % auth)

        h.endheaders()

        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            print errcode, errmsg, headers
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        self.verbose = verbose
        return self.parse_response(h.getfile())


server=ServerProxy("https://username:password@localhost:4433", MyTransport())


print server.add(1,2)

print server.add([1,2,3],[4,5,6])

print server.add("one", "two")
