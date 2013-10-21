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
        self.peers = None
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
        peer_list = []
        presponse = [str(ord(i)) for i in self.tresponse['peers']]
        while presponse:
            peer = '.'.join(presponse[0:4]) + ':' + ''.join(presponse[4:6])
            peer_list.append(peer)
            presponse = presponse[6:]
        return peer_list

    def handshake(self):
        pstr = 'BitTorrent protocol'
        pstrlen = len(pstr)
        reserved = '00000000'
        info_hash = self.hash_string
        peer_id = self.peer_id
        pudb.set_trace()
        packet = ''.join([struct.pack('b', pstrlen), pstr,
                 ''.join([chr(int(i)) for i in reserved]), info_hash,
                 peer_id])
        self.session = requests.Session()
        self.session.get('http://{}'.format(self.peers[1]))
        self.session.send(packet)

    def get_request(self):
        assert self.tdict['info']
        payload = self.build_payload()
        self.r = requests.get(self.tdict['announce'],
                              params=payload)
        self.tresponse = tparser.bdecodes(self.r.text.encode('latin-1'))
        self.peers = self.get_peers()


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('torrent_path')
    args = argparser.parse_args()  # Getting path from command line
    torrent_path = args.torrent_path
    mytorrent = torrent(torrent_path)
    mytorrent.get_request()
    print mytorrent.r.text.encode('latin-1')
    mytorrent.handshake()
    print mytorrent.shake.text


if __name__ == '__main__':
    main()
