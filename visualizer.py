import os
from collections import namedtuple
from tparser import bdecode_file
from bitarray import bitarray
from twisted.internet import reactor
from twisted.internet.protocol import Factory
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
download_file = namedtuple('download_file', 'path bits')


def init_state(t_dict):
    state_dict = {}
    if 'files' in t_dict['info']:
        state_dict['files'] = [download_file(path=os.path.join(*afile['path']),
                                             bits=bitarray('0' *
                                                           afile['length']))
                               for afile in t_dict['info']['files']]
    else:
        state_dict['files'] = [download_file(path=t_dict['info']['name'],
                                             bits=bitarray('0' *
                                                           t_dict['info']
                                                                 ['length']))]
    for some_file in state_dict['files']:
        print some_file.path, len(some_file.bits)
    print '\n\n'
    return state_dict


class Visualizer(object):
    # outfile is temporary while I figure out how to implement
    # visualization
    def __init__(self, outfile='derp.txt', t_dict={}):
        self.outfile = open(outfile, 'w')
        self.sock = None
        self.state = init_state(t_dict)

    def visualize(self, data):
        if self.sock:
            self.outfile.write(data + '\n')

    def close(self):
        self.outfile.close()

    def set_sock(self, sock):
        self.sock = sock

if __name__ == '__main__':
    init_state(bdecode_file('dorian.torrent'))
    init_state(bdecode_file('torrent.torrent'))
