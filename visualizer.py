import txws
import socket
from collections import namedtuple
from twisted.web import http
from twisted.internet import protocol, reactor
import pudb


download_file = namedtuple('download_file', 'path bits')


def init_state(t_dict):
    pass
# state_dict = {}
# if 'files' in t_dict['info']:
#     state_dict['files'] = [download_file(path=os.path.join(*afile['path']),
#                                          bits=bitarray('0' *
#                                                        afile['length']))
#                            for afile in t_dict['info']['files']]
# elif 'name' in t_dict['info']:
#     state_dict['files'] = [download_file(path=t_dict['info']['name'],
#                                          bits=bitarray('0' *
#                                                        t_dict['info']
#                                                              ['length']))]
# else:
#     state_dict['files'] = []
# for some_file in state_dict['files']:
#     print some_file.path, len(some_file.bits)
# print '\n\n'
# return state_dict


class Visualizer(object):

    def __init__(self, t_dict={}):
        init_state(t_dict)
        self.sock = socket.socket()
        self.sock.connect(('localhost', 8035))

    def visualize(self, data):
        if self.sock:
            self.outfile.write(data + '\n')

    def close(self):
        self.outfile.close()

    def set_sock(self, sock):
        self.sock = sock


class MyRequestHandler(http.Request):
    script = open('client.js').read()
    resources = {
        '/': '''<script>{}</script>
                <h1>O hai</h1>'''.format(script)
    }

    def process(self):
        print 'process got called'
        self.setHeader('Content-Type', 'text/html')
        if self.path in self.resources:
            self.write(self.resources[self.path])
        else:
            self.setResponseCode(http.NOT_FOUND,
                                 'Sorry, dogg. We dont have those here')
        self.finish()

# Need to create our own protocol -- LineReceiver isn't generic enough
# (or is it too generic?)


class MyHTTP(http.HTTPChannel):
    print 'MyHTTP initialized'
    requestFactory = MyRequestHandler


class MyHTTPFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        http = MyHTTP()
        return http


class WebSocket(protocol.Protocol):
    websockets = []

    @classmethod
    def add_socket(self, ws):
        self.websockets.append(ws)

    @classmethod
    def broadcast(self, message):
        for ws in self.websockets:
            ws.transport.write(message)

    def dataReceived(self, data):
        pass


class MyWSFactory(protocol.Factory):
    def buildProtocol(self, addr):
        print 'building a WebSocket object'
        ws = WebSocket()
        WebSocket.add_socket(ws)
        return ws


myVisualizer = Visualizer()
reactor.listenTCP(8000, MyHTTPFactory())
reactor.listenTCP(8001, txws.WebSocketFactory(MyWSFactory()))
reactor.run()
