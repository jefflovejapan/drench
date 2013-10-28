import requests
import socket
import tparser
import hashlib
import argparse
import select
import time
import pudb
import reactor
import peer


class torrent():

    def __init__(self, torrent_path, port=55308):
        torrent_dict = tparser.bdecode(torrent_path)
        # pudb.set_trace()
        self.torrent_dict = torrent_dict
        self.peerdict = {}
        self.peer_ips = []
        self.port = port
        self.r = None
        self.tracker_response = None
        self.peerdict = {}
        self.hash_string = None
        self.reactor = reactor.Reactor()

    @property
    def piece_length(self):
        return self.torrent_dict['info']['piece length']

    @property
    def num_pieces(self):
        # Since there's 20 bytes in the string for each piece
        pieces = divmod(len(self.torrent_dict['info']['pieces']), 20)
        if pieces[1] == 0:
            return pieces[0]
        else:
            # Hash needs to be 20 bytes per piece
            raise ValueError('Torrent file error -- bad hash')

    @property
    def length(self):
        return self.torrent_dict['info']['length']

    @property
    def last_piece_length(self):
        return self.length - (self.piece_length * (self.num_pieces - 1))

    def build_payload(self):
        payload = {}
        hashed_info = hashlib.sha1(tparser.bencode(self.torrent_dict['info']))
        self.hash_string = hashed_info.digest()
        self.peer_id = '-TR2820-wa0n562rl3lu'  # TODO: randomize
        payload['info_hash'] = self.hash_string
        payload['peer_id'] = self.peer_id
        payload['port'] = self.port
        payload['uploaded'] = 0
        payload['downloaded'] = 0
        payload['left'] = self.torrent_dict['info']['length']
        payload['compact'] = 1
        payload['supportcrypto'] = 1
        payload['event'] = 'started'
        return payload

    # TODO - create peer objects with ref to reactor
    def get_peer_ips(self):
        presponse = [ord(i) for i in self.tracker_response['peers']]
        while presponse:
            peer_ip = (('.'.join(str(x) for x in presponse[0:4]),
                       256*presponse[4] + presponse[5]))
            if peer_ip not in self.peer_ips:
                self.peer_ips.append(peer_ip)
            presponse = presponse[6:]

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

        packet = ''.join([chr(pstrlen), pstr, chr(0)*8, info_hash,
                          peer_id])
        print "Here's my packet {}".format(packet)
        # TODO -- add some checks in here so that I'm talking
            # to a maximum of 30 peers
        for i in self.peer_ips:
            print i  # just want to see who i'm talking to
            s = socket.socket()
            s.setblocking(True)
            s.settimeout(0.5)
            try:
                s.connect(i)
            except socket.timeout:
                print '{} timed out on connect'.format(i)
                continue
            s.send(packet)
            try:
                data = s.recv(68)  # Peer's handshake - len from docs
                if data:
                    print 'From {} received: {}'.format(i, data)
                    self.initpeer(s, data)  # Initializing peers here
            except socket.timeout:
                print '{} timed out on recv'.format(i)
                continue
        else:
            self.peer_ips = []

    def initpeer(self, sock, data):
        tpeer = peer.peer(sock, self.reactor, data)
        tpeer.max_size = self.torrent_dict['info']['piece length']
        self.peerdict[sock] = tpeer

        self.reactor.select_list.append(tpeer)
        # Reactor now listening to tpeer object

    # TODO -- refactor
    def tracker_request(self):
        assert self.torrent_dict['info']
        payload = self.build_payload()
        self.r = requests.get(self.torrent_dict['announce'],
                              params=payload)
        print len(self.r.text)

        # Decoding response from tracker
        self.tracker_response = tparser.bdecodes(self.r.text.encode('latin-1'))
        self.get_peer_ips()


def main():
    pudb.set_trace()
    argparser = argparse.ArgumentParser()
    argparser.add_argument('torrent_path')
    args = argparser.parse_args()  # Getting path from command line
    torrent_path = args.torrent_path
    mytorrent = torrent(torrent_path)
    mytorrent.tracker_request()
    mytorrent.handshake_peers()
    mytorrent.reactor.event_loop()
    return


if __name__ == '__main__':
    main()
