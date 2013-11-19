import socket
import os
import txws
from collections import namedtuple
from bitarray import bitarray
from twisted.internet import protocol, reactor
import pudb


# Need to:
#   - listen
#   - create
# Torrent and switchboard talk to "visualizer"
#   - what is the visualizer?
#       - it's a wrapper for this Twisted server
#   - should start up the Twisted server on startup and
#     start writing stuff out to it
#   - on incoming connection, the Twisted server makes a websocket
#       - if it's asked for one, otherwise do nothing
#   - if there are no incoming connections, we just build up
#     the state of this torrent
#       - *Which bytes* do we have in the file(s)?
#       - Who are the peers?

# Accepting incoming connections to this visualizer
# **Managing the state stuff


download_file = namedtuple('download_file', 'path bits')

# TODO -- put inside Visualizer as method


def init_state(t_dict):
    state_dict = {}
    if 'files' in t_dict['info']:
        state_dict['files'] = [download_file(path=os.path.join(*afile['path']),
                                             bits=bitarray('0' *
                                                           afile['length']))
                               for afile in t_dict['info']['files']]
    elif 'name' in t_dict['info']:
        state_dict['files'] = [download_file(path=t_dict['info']['name'],
                                             bits=bitarray('0' *
                                                           t_dict['info']
                                                                 ['length']))]
    else:
        state_dict['files'] = []
    for some_file in state_dict['files']:
        print some_file.path, len(some_file.bits)
    print '\n\n'
    return state_dict


class Visualizer(object):
    # outfile is temporary while I figure out how to implement
    # visualization
    # def __init__(self, t_dict={}, address=('127.0.0.1', 7000)):
    #     self.sock = socket.socket()
    #     self.sock.connect(address)
    #     self.state = init_state(t_dict)
    #     self.data_source = address
    def __init__(self):
        pass

    def visualize(self, data):
        if self.sock:
            self.outfile.write(data + '\n')

    def close(self):
        self.outfile.close()

    def set_sock(self, sock):
        self.sock = sock


class Echo(txws.WebSocketProtocol):
    def dataReceived(self, data):
        self.transport.write(data)


class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()


def main():
    reactor.listenTCP(8000, txws.WebSocketFactory(EchoFactory()))
    reactor.run()


if __name__ == '__main__':
    main()
