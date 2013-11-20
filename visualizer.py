import txws
from collections import namedtuple
from twisted.web import http
from twisted.internet import protocol, reactor, endpoints
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

#


class BitClient(protocol.Protocol):
    '''
    Responsible for grabbing TCP connection to BitTorrent client.
    Gets callback on dataReceived initiating a broadcast to all
    websockets
    '''

    def dataReceived(self, data):
        print data
        WebSocket.broadcast(data)


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
        print 'adding a websocket'
        WebSocket.websockets.append(ws)

    @classmethod
    def broadcast(self, message):
        for ws in WebSocket.websockets:
            ws.transport.write(message)

    def dataReceived(self, data):
        print data


class MyWSFactory(protocol.Factory):
    def buildProtocol(self, addr):
        print 'building a WebSocket object'
        ws = WebSocket()
        WebSocket.add_socket(ws)
        print WebSocket.websockets
        return ws

point = endpoints.TCP4ClientEndpoint(reactor, "127.0.0.1", 8035)
bit_client = BitClient()
d = endpoints.connectProtocol(point, bit_client)
reactor.listenTCP(8000, MyHTTPFactory())
reactor.listenTCP(8001, txws.WebSocketFactory(MyWSFactory()))
reactor.run()
