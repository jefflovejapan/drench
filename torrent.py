import requests
import socket
import tparser
import hashlib
import argparse
import reactor
import peer
import time
import pudb
from listener import Listener
from switchboard import Switchboard


class PeerListener(Listener):
    def __init__(self, address='127.0.0.1',
                 port=8035, torrent=None):
        Listener.__init__(self, address, port)
        self.torrent = torrent

    def read(self):
        newsock, _ = self.sock.accept()
        # It's add_peer's job to add the peer to event_loop
        self.torrent.add_peer(newsock)


class VisListener(Listener):
    def __init__(self, address='127.0.0.1',
                 port=7000, torrent=None):
        Listener.__init__(self, address, port)
        assert torrent
        self.torrent = torrent

    def read(self):
        newsock, _ = self.sock.accept()
        self.vis_sock = newsock


class Torrent(object):

    def __init__(self, torrent_path, port=55308):
        torrent_dict = tparser.bdecode_file(torrent_path)
        self.torrent_dict = torrent_dict
        self.peer_dict = {}
        self.peer_ips = []
        self.port = port
        self.r = None
        self.tracker_response = None
        self.peer_dict = {}
        self.hash_string = None
        self.vis_sock = ''
        self.queued_requests = []
        self.reactor = reactor.Reactor()
        self.reactor.add_listeners([PeerListener(torrent=self, port=7000),
                                    VisListener(torrent=self, port=8035)])
        self.switchboard = Switchboard(dirname=self.torrent_dict['info']
                                       ['name'], file_list=self.torrent_dict
                                       ['info']['files'], piece_length=
                                       self.piece_length, num_pieces=
                                       self.num_pieces, vis_sock=
                                       self.vis_sock)

    @property
    def piece_length(self):
        return self.torrent_dict['info']['piece length']

    @property
    def num_pieces(self):
        num, rem = divmod(len(self.torrent_dict['info']['pieces']), 20)
        if rem == 0:
            return num
        else:
            raise Exception("Improperly formed 'pieces' entry in torrent_dict")

    @property
    def length(self):
        return sum([i['length'] for i in self.torrent_dict['info']['files']])

    @property
    def last_piece_length(self):
        return self.length - (self.piece_length * (self.num_pieces - 1))

    def build_payload(self):
        '''
        Builds the payload that will be sent in tracker_request
        '''
        payload = {}
        hashed_info = hashlib.sha1(tparser.bencode(self.torrent_dict['info']))
        self.hash_string = hashed_info.digest()
        self.peer_id = '-TR2820-wa0n562rl3lu'  # TODO: randomize
        payload['info_hash'] = self.hash_string
        payload['peer_id'] = self.peer_id
        payload['port'] = self.port
        payload['uploaded'] = 0
        payload['downloaded'] = 0
        payload['left'] = self.length
        payload['compact'] = 1
        payload['supportcrypto'] = 1
        payload['event'] = 'started'
        return payload

    # TODO -- refactor?
    def tracker_request(self):
        '''
        Sends the initial request to the tracker, compiling list of all peers
        announcing to the tracker
        '''

        assert self.torrent_dict['info']
        payload = self.build_payload()

        if self.torrent_dict['announce'].startswith('udp'):
            raise Exception('need to deal with UDP')

        else:
            self.r = requests.get(self.torrent_dict['announce'],
                                  params=payload)

        # Decoding response from tracker
        self.tracker_response = tparser.bdecode(self.r.text.encode('latin-1'))
        self.get_peer_ips()

    def get_peer_ips(self):
        '''
        Generates list of peer IPs from tracker response. Note: not all of
        these IPs might be good, which is why we only init peer objects for
        the subset that respond to handshake
        '''
        presponse = [ord(i) for i in self.tracker_response['peers']]
        while presponse:
            peer_ip = (('.'.join(str(x) for x in presponse[0:4]),
                       256 * presponse[4] + presponse[5]))
            if peer_ip not in self.peer_ips:
                self.peer_ips.append(peer_ip)
            presponse = presponse[6:]

# TODO -- refactor this so it takes peer IPs or
# sockets (in the case of incoming connections)
    def handshake_peers(self):
        '''
        pstrlen = length of pstr as one byte
        pstr = BitTorrent protocol
        reserved = chr(0)*8
        info_hash = 20-byte hash above (aka self.hash_string)
        peer_id = 20-byte string
        '''

        pstr = 'BitTorrent protocol'
        pstrlen = len(pstr)
        info_hash = self.hash_string
        peer_id = self.peer_id

        packet = ''.join([chr(pstrlen), pstr, chr(0) * 8, info_hash,
                          peer_id])
        print "Here's my packet {}".format(repr(packet))
        # TODO -- add some checks in here so that I'm talking
        # to a maximum of 30 peers

        # TODO -- think about why i'm deleting self.peer_ips.
        # What was the point of it? Why won't I need it?
        # Think about what we're doing -- using this list to create
        # new peer objects. Should make this functional, that way I
        # can also call when I get new peers.
        for i in self.peer_ips:
            print i  # just want to see who i'm talking to
            s = socket.socket()
            s.setblocking(True)
            s.settimeout(1)
            try:
                s.connect(i)
            except socket.timeout:
                print '{} timed out on connect'.format(i)
                continue
            except socket.error:
                print '{} threw a socket error'.format(i)
                continue
            s.send(packet)
            try:
                data = s.recv(68)  # Peer's handshake - len from docs
                if data:
                    print 'From {} received: {}'.format(i, repr(data))
                    self.initpeer(s)  # Initializing peers here
            except:
                print '{} timed out on recv'.format(i)
                continue
        else:
            self.peer_ips = []

    def initpeer(self, sock):
        '''
        Creates a new peer object for a nvalid socket and adds it to reactor's
        listen list
        '''

        tpeer = peer.Peer(sock, self.reactor, self)
        self.peer_dict[sock] = tpeer
        self.reactor.select_list.append(tpeer)
        # Reactor now listening to tpeer object

    def add_peer(self, sock):
        print 'adding peer at', sock.getpeername()
        time.sleep(3)

    def kill_peer(self, tpeer):
        thispeer = self.peer_dict.pop(tpeer.sock)
        print 'peer with fileno {} killing itself'.format(thispeer.fileno())
        self.reactor.select_list.remove(thispeer)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('torrent_path')
    args = argparser.parse_args()  # Getting path from command line
    torrent_path = args.torrent_path
    mytorrent = Torrent(torrent_path)
    mytorrent.tracker_request()
    mytorrent.handshake_peers()
    mytorrent.reactor.event_loop()
    return


if __name__ == '__main__':
    main()
