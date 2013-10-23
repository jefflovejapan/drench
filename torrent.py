import requests
import socket
import tparser
import hashlib
import urllib
import argparse
import struct
import pudb


class torrent():

    def __init__(self, torrent_path, port=55308):
        tdict = tparser.bdecode(torrent_path)
        self.tdict = tdict
        self.port = port
        self.r = None
        self.tresponse = None
        self.peers = []
        self.hash_string = None
        self.shake = None

    def build_payload(self):
        payload = {}
        hashed_info = hashlib.sha1(tparser.bencode(self.tdict['info']))
        self.hash_string = hashed_info.digest()
        self.peer_id = '-TR2820-wa0n562rl3lu'  # TODO: randomize
        payload['info_hash'] = self.hash_string
        payload['peer_id'] = self.peer_id
        payload['port'] = self.port
        payload['uploaded'] = 0
        payload['downloaded'] = 0
        payload['left'] = self.tdict['info']['length']
        payload['compact'] = 1
        payload['supportcrypto'] = 1
        payload['event'] = 'started'
        return payload

    def get_peers(self):
        presponse = [ord(i) for i in self.tresponse['peers']]
        while presponse:
            peer = (('.'.join(str(x) for x in presponse[0:4]), 256*presponse[4]
                     + presponse[5]))
            if peer not in self.peers:
                self.peers.append(peer)
            presponse = presponse[6:]

    def download(self, psocket):
        pudb.set_trace()
        print 'downloading from peer {}'.format(psocket.getpeername())
        psocket.setblocking(False)
        psocket.send(struct.pack('bbbb', 0, 0, 0, 1) + '1')
        response = psocket.recv(10000)
        psocket.send(struct.pack('bbbb', 0, 0, 1, 3) + '6' + '0' + '0' +
                     str(2**14))
        response = psocket.recv(2**14)
        print 'The length of the response is {}'.format(len(response))

    def nextpeer(self):
        pass

    def handshake_peers(self):
        pstr = 'BitTorrent protocol'
        pstrlen = len(pstr)
        reserved = '00000000'
        info_hash = self.hash_string
        peer_id = self.peer_id
        for i in self.peers:
            print i
            packet = ''.join([struct.pack('b', pstrlen), pstr,
                     ''.join([chr(int(j)) for j in reserved]), info_hash,
                     peer_id])
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            try:
                s.connect(i)
                s.send(packet)
                data = s.recv(68)
                bitfield = s.recv(15)
                print 'inside handshake len of data is {}'.format(len(data))
                print str(len(bitfield[:4])) + bitfield[5:]
                if self.hash_string in data:
                    self.download(s)
            except socket.timeout:
                print 'connection to peer {} timed out'.format(i)
                pass

    def get_request(self):
        assert self.tdict['info']
        payload = self.build_payload()
        self.r = requests.get(self.tdict['announce'],
                              params=payload)
        print len(self.r.text)
        self.tresponse = tparser.bdecodes(self.r.text.encode('latin-1'))
        self.get_peers()


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('torrent_path')
    args = argparser.parse_args()  # Getting path from command line
    torrent_path = args.torrent_path
    mytorrent = torrent(torrent_path)
    mytorrent.get_request()
    mytorrent.handshake_peers()


if __name__ == '__main__':
    main()
