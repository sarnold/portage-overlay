# Trying to do xml-rpc using ssh (via paramiko library)

import  paramiko_bp as paramiko # our version is slightly modified
import socket
import sys
import threading, thread

print "Main thread is",thread.get_ident()


bind_address=("", 12098)
connect_address=("localhost", 12098)

class ServerChannel(paramiko.Channel):
    pass
    

class ServerTransport(paramiko.Transport):
    okauth=( ('rogerb', 'password'), ('example', 'nonsense') )
    def check_channel_request(self, kind, chanid):
        print "check channel request in thread",thread.get_ident()
        if kind == 'bitfling':
            return ServerChannel(chanid)
        return self.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        print "check auth request in thread",thread.get_ident()
        print "checking creds",`username`, `password`
        if (username,password) in self.okauth:
            return self.AUTH_SUCCESSFUL
        return self.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

def server():
    # setup logging
    import logging
    l = logging.getLogger("paramiko")
    l.setLevel(logging.DEBUG)
    if len(l.handlers) == 0:
        f = open('demo_server.log', 'wt')
        lh = logging.StreamHandler(f)
        lh.setFormatter(logging.Formatter('%(levelname)-.3s [%(asctime)s] %(name)s: %(message)s', '%Y%m%d:%H%M%S'))
        l.addHandler(lh)

    host_key = paramiko.DSSKey()
    host_key.read_private_key_file('pmkey')
    
    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(bind_address)
    sock.listen(5)

    while True:
        conn, addr=sock.accept()
        print "accept from",addr
        transport=ServerTransport(conn)
        transport.add_server_key(host_key)
        print "starting server"
        transport.start_server()
        print "accepting channel"
        chan=transport.accept()
        print "got a channel"
        while True:
            try:
                c=chan.recv(1)
                print "received",c
            except EOFError:
                c=None
            if c is None or len(c)==0:
                print "received end of channel"
                transport.close()
                break
            chan.sendall(chr(ord(c)+1))

def client():
    # setup logging
        # setup logging
    import logging
    l = logging.getLogger("paramiko")
    l.setLevel(logging.DEBUG)
    if len(l.handlers) == 0:
        f = open('demo_client.log', 'wt')
        lh = logging.StreamHandler(f)
        lh.setFormatter(logging.Formatter('%(levelname)-.3s [%(asctime)s] %(name)s: %(message)s', '%Y%m%d:%H%M%S'))
        l.addHandler(lh)
    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(connect_address)
    transport=paramiko.Transport(sock)
    transport.setDaemon(True)
    event=threading.Event()
    transport.start_client(event)
    event.wait(15)
    print "active =",transport.is_active()
    keytype, hostkey = transport.get_remote_server_key()
    print "host key is",keytype,paramiko.util.hexify(hostkey)
    event=threading.Event()
    transport.auth_password('rogerb', 'password', event)
    event.wait(10)
    chan=transport.open_channel("bitfling")
    import random
    for i in range(10):
        chan.sendall(random.choice( ("one", "two", "three") )+" ")
        print chan.recv(4)

if __name__=='__main__':
    if sys.argv[1]=='server':
        server()
    else:
        client()
