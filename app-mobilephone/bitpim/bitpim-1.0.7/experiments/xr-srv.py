# M2Crypto
from M2Crypto import DH, SSL
import SimpleXMLRPCServer
import sys
import base64
import xmlrpclib

class AuthenticationChecker:
    realm="XMLRPC"

    def check_auth_headers(self):
        # self.client_address (host, port)
        try:
            cred=self.headers["Authorization"]
        except KeyError:
            return self.auth_failed()

        cred=cred.split()
        if cred[0].lower()!="basic":
            return self.auth_failed()
        
        v=base64.decodestring(cred[1])
        p=v.find(':')
        if p<0:
            return self.auth_failed()

        uname=v[:p]
        pwd=v[p+1:]

        if not self.check_credentials(uname, pwd, self.client_address):
            return self.auth_failed()

        return True

    def check_credentials(self, username, password, address):
        print "check_credentials %s, %s, %s" % (`username`, `password`, `address`)
        return True

    def auth_failed(self):
        self.send_response(401, "Authentication required")
        self.send_header("WWW-Authenticate", "Basic realm="+self.realm)
        self.end_headers()

        return False
        

if sys.version>="2.3": # Python 2.3 - we also supply doc

    
    import DocXMLRPCServer

    class BADocXMLRPCRequestHandler(DocXMLRPCServer.DocXMLRPCRequestHandler, AuthenticationChecker):

        def do_POST(self):
            if not self.check_auth_headers():
                return
            #import pdb
            #pdb.set_trace()
            DocXMLRPCServer.DocXMLRPCRequestHandler.do_POST(self)

        def do_GET(self):
            DocXMLRPCServer.DocXMLRPCRequestHandler.do_GET(self)

        def finish(self):
            # do proper SSL shutdown sequence
            self.request.set_shutdown(SSL.SSL_RECEIVED_SHUTDOWN | SSL.SSL_SENT_SHUTDOWN)
            self.request.close()


    
    class SSLSimpleXMLRPCServer(SSL.SSLServer, SimpleXMLRPCServer.SimpleXMLRPCDispatcher, DocXMLRPCServer.XMLRPCDocGenerator):
        def __init__(self, addr, ssl_context ):
            self.logRequests=True
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self)
            SSL.SSLServer.__init__(self, addr, BADocXMLRPCRequestHandler, ssl_context)
            DocXMLRPCServer.XMLRPCDocGenerator.__init__(self)


else: # Python 2.2 - no doc

    class SSLSimpleXMLRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler, AuthenticationChecker):

        def do_POST(self):
            if not self.check_auth_headers():
                return
            SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.do_POST(self)


        def finish(self):
            print "my finish called"
            # do proper SSL shutdown sequence
            self.request.set_shutdown(SSL.SSL_RECEIVED_SHUTDOWN | SSL.SSL_SENT_SHUTDOWN)
            self.request.close()

    
    class SSLSimpleXMLRPCServer(SSL.SSLServer):
        def __init__(self, addr, ssl_context ):
            self.logRequests=True
            self.instance=None
            self.funcs={}
            SSL.SSLServer.__init__(self, addr, SSLSimpleXMLRPCRequestHandler, ssl_context)
            
        def register_instance(self, instance):
            self.instance = instance

        def register_function(self, function, name = None):
            if name is None:
                name = function.__name__
            self.funcs[name] = function


context=SSL.Context("sslv23")
context.load_cert("host.pem", "privkey.pem")

server = SSLSimpleXMLRPCServer(("localhost", 1234), context)

def add(a,b):
    "doc for add"
    return a+b

server.register_function(add)

server.serve_forever()
