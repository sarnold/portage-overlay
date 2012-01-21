#!/usr/bin/env python

# This file is double licensed as the BitPim License and the Python
# licenses.  It incorporates code from the standard Python library
# which was then modified to work properly.

# My own implementation of xmlrpc (both server and client)

# It has a silly name so it doesn't class with standard Python
# and library module names

# This code initially tried to do XML-RPC over HTTP/1.1 persistent
# connections over SSL (provided by M2Crypto).  That turned out into a
# big nightmare of trying to mash libraries to work together that
# didn't really want to.

# This new version uses SSH (provided by paramiko).

# Server design
#
# Main thread (which could be a daemon thread for the rest of the program)
# creates the listening socket, and starts the connection handler threads.
# They all sit in a loop.  They call accept, work on the lifetime of
# a connection, and when it closes go back to accept.  When they get a
# request, it is dumped into a queue for the main thread to deal with,
# who then dumps the results back into a queue for the connection thread.
# Consequently we get the benefits of threading for dealing with event
# stuff, but the actual request handling still seems single threaded.


TRACE=False


# standard modules
import threading
import Queue
import time
import sys
import xmlrpclib
import base64
import string
import logging
import os
import socket

# required add ons
import paramiko

# my modules
if TRACE: import guihelper # to format exceptions
import common

class ServerChannel(paramiko.Channel):

    def __init__(self, chanid, peeraddr, username):
        self.chan=chanid
        self.peeraddr=peeraddr
        self.username=username
        paramiko.Channel.__init__(self, chanid)
        
    def readall(self, amount):
        result=""
        while amount:
            l=self.chan.recv(amount)
            if len(l)==0:
                return result # eof
            result+=l
            amount-=len(l)
        return result

    def XMLRPCLoop(self, conn):
        """Main loop that deals with the XML-RPC data

        @param conn:  The connectionthread object we are working for
        """
        while True:
            try:
                length=int(self.readall(8))
            except ValueError:
                return
            xml=self.readall(length)
            response=conn.processxmlrpcrequest(xml, self.peeraddr,
                                           self.username)
            self.chan.sendall( ("%08d" % (len(response),))+response)

class myServer(paramiko.ServerInterface):

    def __init__(self, peeraddr, onbehalfof):
        self.event = threading.Event()
        self.peeraddr=peeraddr
        self.onbehalfof=onbehalfof
        
    def get_allowed_auths(self, username):
        return "password"

    def check_auth_password(self, username, password):
        # we borrow the connection's queue object for this
        self.bf_auth_username="<invalid user>"
        conn=self.onbehalfof
        conn.log("Checking authentication for user "+`username`)
        msg=Server.Message(Server.Message.CMD_NEW_USER_REQUEST, conn.responsequeue,
                           self.peeraddr, data=(username,password))
        conn.requestqueue.put(msg)
        resp=conn.responsequeue.get()
        assert resp.cmd==resp.CMD_NEW_USER_RESPONSE
        if hasattr(resp, 'exception'):
            conn.logexception("Exception while checking authentication",resp.exception)
            return paramiko.AUTH_FAILED
        if resp.data:
            conn.log("Credentials ok for user "+`username`)
            self.bf_auth_username=username
            return paramiko.AUTH_SUCCESSFUL
        conn.log("Credentials not accepted for user "+`username`)
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == 'bitfling':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    
class Server(threading.Thread):

    class Message:
        """A message between a connection thread and the server object, or vice versa"""
        # These are in the order things happen.  Logging happens all the time, and we
        # cycle XMLRPC requests and responses for the lifetime of a connection
        CMD_LOG=0                            # data is log message
        CMD_LOG_EXCEPTION=1                   # data is sys.exc_info()
        CMD_NEW_ACCEPT_REQUEST=2
        CMD_NEW_ACCEPT_RESPONSE=3
        CMD_NEW_USER_REQUEST=4
        CMD_NEW_USER_RESPONSE=5
        CMD_XMLRPC_REQUEST=6
        CMD_XMLRPC_RESPONSE=7
        CMD_CONNECTION_CLOSE=8
       
        def __init__(self, cmd, respondqueue=None, clientaddr=None, data=None):
            self.cmd=cmd
            self.respondqueue=respondqueue
            self.clientaddr=clientaddr
            self.data=data

        def __repr__(self):
            d=`self.data`
            if len(d)>40:
                d=d[:40]
            str=`self.cmd`
            for i in dir(self):
                if i.startswith("CMD_") and getattr(self, i)==self.cmd:
                    str=i
                    break
            return "Message: cmd=%s data=%s" % (str, d)
    
    class ConnectionThread(threading.Thread):

        def __init__(self, server, listen, queue, name):
            """Constructor
            
            @param server: reference to server object
            @param listen: socket object that is in listening state
            @param queue:  the queue object to send messages to
            @param name: name of this thread"""
            threading.Thread.__init__(self)
            self.setDaemon(True)
            self.setName(name)
            self.responsequeue=Queue.Queue()
            self.server=server
            self.requestqueue=queue
            self.listen=listen

        def log(self, str):
            now=time.time()
            t=time.localtime(now)
            timestr="&%d:%02d:%02d.%03d"  % ( t[3], t[4], t[5],  int((now-int(now))*1000))
            msg=Server.Message(Server.Message.CMD_LOG, data="%s: %s: %s" % (timestr, self.getName(), str))
            self.requestqueue.put(msg)

        def logexception(self, str, excinfo):
            if __debug__ and TRACE: print "exception %s\n%s" % (str, guihelper.formatexception(excinfo))
            self.log(str)
            msg=Server.Message(Server.Message.CMD_LOG_EXCEPTION, data=excinfo)
            self.requestqueue.put(msg)
                            
        def run(self):
            event=threading.Event()
            while not self.server.wantshutdown:
                if __debug__ and TRACE: print self.getName()+": About to call accept"
                try:
                    transport=None
                    event.clear()
                    # blocking wait for new connection to come in
                    sock, peeraddr = self.listen.accept()
                    # ask if we allow this connection
                    msg=Server.Message(Server.Message.CMD_NEW_ACCEPT_REQUEST, self.responsequeue, peeraddr)
                    self.requestqueue.put(msg)
                    resp=self.responsequeue.get()
                    assert resp.cmd==resp.CMD_NEW_ACCEPT_RESPONSE
                    ok=resp.data
                    if not ok:
                        self.log("Connection from "+`peeraddr`+" not accepted")
                        sock.close()
                        continue
                    # startup ssh stuff
                    self.log("Connection from "+`peeraddr`+" accepted")
                    transport=paramiko.Transport(sock)
                    transport.add_server_key(self.server.ssh_server_key)
                    transport.setDaemon(True)
                    srvr=myServer(peeraddr, self)
                    transport.start_server(event,srvr)
                                         
                except:
                    if __debug__ and TRACE: print self.getName()+": Exception in accept block\n"+guihelper.formatexception()
                    self.logexception("Exception in accept", sys.exc_info())
                    if transport is not None: del transport
                    sock.close()
                    continue

                # wait for it to become an SSH connection
                event.wait()
                if not event.isSet() or not transport.is_active():
                    self.log("Connection from "+`peeraddr`+" didn't do SSH negotiation")
                    transport.close()
                    sock.close()
                    continue
                if __debug__ and TRACE: print self.getName()+": SSH connection from "+`peeraddr`

                self.log("SSH negotiated from "+`peeraddr`)

                chan=None
                try:
                    chan=transport.accept()
                    serverchan=ServerChannel(chan,peeraddr,srvr.bf_auth_username)
                    serverchan.XMLRPCLoop(self)
                except:
                    self.logexception("Exception in XMLRPCLoop", sys.exc_info())

                if chan is not None:
                    chan.close()
                    del chan

                if transport is not None:
                    transport.close()
                    del transport

                msg=Server.Message(Server.Message.CMD_CONNECTION_CLOSE,  None, peeraddr)
                self.requestqueue.put(msg)
                self.log("Connection from "+`peeraddr`+" closed")

        def processxmlrpcrequest(self, data, client_addr, username):
            msg=Server.Message(Server.Message.CMD_XMLRPC_REQUEST, self.responsequeue, client_addr, data=(data, username))
            if __debug__ and TRACE:
                self.log("%s: req %s" % (username, `data`))
            self.requestqueue.put(msg)
            resp=self.responsequeue.get()
            assert resp.cmd==resp.CMD_XMLRPC_RESPONSE
            if hasattr(resp, "exception"):
                raise resp.exception
            return resp.data
            

    def __init__(self, host, port, servercert, connectionthreadcount=5, timecheck=60, connectionidlebreak=240):
        """Creates the listening thread and infrastructure.  Don't forget to call start() if you
        want anything to be processed!  You probably also want to call setDaemon().  Remember to
        load a certificate into the sslcontext.

        @param connectionthreadcount:  How many threads are being used.  If new connections
                            arrive while the existing threads are busy in connections, then they will be ignored
        @param timecheck:  How often shutdown requests are checked for in the main thread (only valid on Python 2.3+)
        @param connectionidlebreak: If an SSH connection is idle for this amount of time then it is closed
        """
        threading.Thread.__init__(self)
        self.setName("Threading SSH server controller for %s:%d" % (host, port))
        # setup logging
        l=logging.getLogger("paramiko")
        l.setLevel(logging.INFO)
        lh=FunctionLogHandler(self.OnLog)
        lh.setFormatter(logging.Formatter('%(levelname)-.3s [%(asctime)s] %(name)s: %(message)s', '%Y%m%d:%H%M%S'))
        l.addHandler(lh)
        self.ssh_server_key=servercert
        connection=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not host:
            host="0.0.0.0"
        if __debug__ and TRACE: print "Binding to host %s port %d" % (host, port)
        connection.bind( (host, port) )
        connection.listen(connectionthreadcount+5)
        self.timecheck=timecheck
        self.connectionidlebreak=connectionidlebreak
        self.wantshutdown=False
        self.workqueue=Queue.Queue()
        self.threadlist=[]
        for count in range(connectionthreadcount):
            conthread=self.ConnectionThread(self, connection, self.workqueue, "SSH worker thread %d/%d" % (count+1, connectionthreadcount))
            conthread.start()
            self.threadlist.append(conthread)

    def shutdown(self):
        """Requests a shutdown of all threads"""
        self.wantshutdown=True

    def run23(self):
        while not self.wantshutdown:
            try:
                msg=self.workqueue.get(True, self.timecheck)
            except Queue.Empty:
                continue
            try:
                self.processmessage(msg)
            except:
                sys.excepthook(*sys.exc_info())
        
    def run22(self):
        while not self.wantshutdown:
            try:
                msg=self.workqueue.get(True)
            except Queue.Empty:
                continue
            try:
                self.processmessage(msg)
            except:
                sys.excepthook(*sys.exc_info())
                

    if sys.version_info>=(2,3):
        run=run23
    else:
        run=run22

    def processmessage(self, msg):
        if not isinstance(msg, Server.Message):
            self.OnUserMessage(msg)
            return
        if __debug__ and TRACE:
            if not msg.cmd in (msg.CMD_LOG, msg.CMD_LOG_EXCEPTION):
                print "Processing message "+`msg`
        resp=None
        if msg.cmd==msg.CMD_LOG:
            self.OnLog(msg.data)
            return
        elif msg.cmd==msg.CMD_LOG_EXCEPTION:
            self.OnLogException(msg.data)
            return
        elif msg.cmd==msg.CMD_NEW_ACCEPT_REQUEST:
            ok=self.OnNewAccept(msg.clientaddr)
            resp=Server.Message(Server.Message.CMD_NEW_ACCEPT_RESPONSE, data=ok)
        elif msg.cmd==msg.CMD_NEW_USER_REQUEST:
            ok=self.OnNewUser(msg.clientaddr, msg.data[0], msg.data[1])
            resp=Server.Message(Server.Message.CMD_NEW_USER_RESPONSE, data=ok)
        elif msg.cmd==msg.CMD_XMLRPC_REQUEST:
            data=self.OnXmlRpcRequest(* (msg.data+(msg.clientaddr,)))
            resp=Server.Message(Server.Message.CMD_XMLRPC_RESPONSE, data=data)
        elif msg.cmd==msg.CMD_CONNECTION_CLOSE:
            self.OnConnectionClose(msg.clientaddr)
        else:
            assert False, "Unknown message command "+`msg.cmd`
            raise Exception("Internal processing error")
        if resp is not None:
            msg.respondqueue.put(resp)

    def OnLog(self, str):
        """Process a log message"""
        print str

    def OnLogException(self, exc):
        """Process an exception message"""
        print exc[:2]


    def OnNewAccept(self, clientaddr):
        """Decide if we accept a new new connection"""
        return True

    def OnNewUser(self, clientaddr, username, password):
        """Decide if a user is allowed to authenticate"""
        return True

    def OnConnectionClose(self, clientaddr):
        """Called when a connection closes"""
        if __debug__ and TRACE: print "Closed connection from "+`clientaddr`

    def OnUserMessage(self, msg):
        """Called when a message arrives in the workqueue"""

    def OnXmlRpcRequest(self, xmldata, username, clientaddr):
        """Called when an XML-RPC request arrives, but before the XML is parsed"""
        params, method = xmlrpclib.loads(xmldata)
        # call method
        try:
            response=self.OnMethodDispatch(method, params, username, clientaddr)
            # wrap response in a singleton tuple
            response = (response,)
            response = xmlrpclib.dumps(response, methodresponse=1)
        except xmlrpclib.Fault, fault:
            response = xmlrpclib.dumps(fault)
        except:
            self.OnLog("Exception processing method "+`method`)
            self.OnLogException(sys.exc_info())
            # report exception back to server, with class name first
            # and then `object`.  The client end may be able to
            # re-raise it
            obj=sys.exc_info()[1]
            try:
                klass="%s.%s" % (obj.__module__, obj.__name__)
            except:
                klass="%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)
            response = xmlrpclib.dumps(xmlrpclib.Fault(17, "%s:%s" % (klass, obj)))

        return response            

    def OnMethodDispatch(self, method, params, username, clientaddr):
        """Called once the XML-RPC request is parsed"""
        if __debug__ and TRACE: print "%s %s (user=%s, client=%s)" % (method, `tuple(params)`, username, `clientaddr`)
        if method=='add' and len(params)==2:
            return params[0]+params[1]
        raise xmlrpclib.Fault(10, "Unknown method "+method)

# Copied from xmlrpclib.  This version is slightly modified to be derived from
# object.  The reason is that if you print a _Method object, then the __str__
# method is called, which tries to do it over XML-RPC!  Deriving from object
# causes that and many other methods to be already present so it isn't a
# problem.

class _Method(object):
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)

class CertificateNotAcceptedException(Exception):
    pass

class ServerProxy:
    logsetup=False
    def __init__(self, username, password, host, port, certverifier=None):
        if not self.logsetup:
            # paramiko.util.log_to_file('serverproxy.log')
            self.logsetup=True
        self.__username=username
        self.__password=password
        self.__host=host
        self.__port=port
        self.__channel=None
        self.__certverifier=certverifier

    def __str__(self):
        return "<XML-RPC over SSH proxy for %s @ %s:%d>" % (self.__username, self.__host, self.__port)

    def __repr__(self):
        return "<XML-RPC over SSH proxy for %s @ %s:%d>" % (self.__username, self.__host, self.__port)

    def __makeconnection(self):
        self.__channel=None
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect( (self.__host, self.__port) )
        t=paramiko.Transport(sock)
        t.setDaemon(True)
        event=threading.Event()
        t.start_client(event)
        event.wait(15)
        if not t.is_active():
            raise Exception("No SSH on the other end: %s/%d" % (self.__host, self.__port) )
        key=t.get_remote_server_key()
        
        if self.__certverifier is not None:
            res=self.__certverifier( (self.__host, self.__port), key)
            if not res:
                raise CertificateNotAcceptedException("Certificate not accepted for  %s @ %s:%d" % (self.__username, self.__host, self.__port))
            if not t.is_active():
                raise Exception("Session has failed while waiting for certificate to be verified")

        event=threading.Event()
        t.auth_password(self.__username, self.__password, event)
        event.wait()
        if not t.is_active():
            raise Exception("Authentication to %s failed:  Username %s, password %s" % (self.__host, `self.__username`, `self.__password`))
        self.__channel=t.open_channel("bitfling")

    def __ensure_channel(self):
        if self.__channel is None:
            self.__makeconnection()
        if self.__channel is None:
            raise Exception("Unable to properly connect")

    def __getattr__(self, name):
        if name.startswith("__"):
            raise Exception("Bad method "+`name`)
        return _Method(self.__send, name)

    def __recvall(self, channel, amount):
        result=""
        while amount:
            l=channel.recv(amount)
            if len(l)==0:
                return result # eof
            result+=l
            amount-=len(l)
        return result

    def __send(self, methodname, args):
        self.__ensure_channel()
        request=xmlrpclib.dumps(args, methodname, encoding=None) #  allow_none=False (allow_none is py2.3+)
        self.__channel.sendall( ("%08d" % (len(request),))+request)
        resplen=self.__recvall(self.__channel, 8)
        resplen=int(resplen)
        response=self.__recvall(self.__channel, resplen)
        p, u = xmlrpclib.getparser()
        p.feed(response)
        p.close()
        # if the response was a Fault, then it is raised by u.close()
        try:
            response=u.close()
        except xmlrpclib.Fault,e:
            if e.faultCode!=17:
                raise e
            klass,str=e.faultString.split(':', 1)
            raise common.getfullname(klass)(str)
            
        if len(response)==1:
            response=response[0]
        return response
        
class FunctionLogHandler(logging.Handler):
    "Log handler that calls a specified function"
    def __init__(self, function, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.function=function

    def emit(self, record):
        self.function(record.getMessage())


if __name__=='__main__':
    if len(sys.argv)<2:
        print "You must supply arguments - one of"
        print "  server"
        print "  client"
        sys.exit(1)

    if sys.argv[1]=="server":
        #cert=paramiko.DSSKey()
        #cert.read_private_key_file(os.path.expanduser("~/.bitfling.key"))
        cert=paramiko.DSSKey.from_private_key_file("~/.bitfling.key")
        server=Server('', 12652, cert)
        server.setDaemon(True)
        server.start()

        time.sleep(1120)

    if sys.argv[1]=="client":
        server=ServerProxy('username', 'password', 'localhost', 12652)

        print server.add(3,4)
        print server.add("one", "two")

