# Preprocessing of the .torrent performed with bdecode

import requests
import socket
import tparser
import hashlib
import urllib
# import pudb


class torrent():

    def __init__(self, tdict, port=55308):
        self.tdict = tdict
        self.port = port
        self.r = None

    def get_request(self):
        # payload = {}
        assert self.tdict['info']
        hashed_info = hashlib.sha1(tparser.bencode(self.tdict['info']))
        hash_string = hashed_info.digest()
        payload = {}
        payload['info_hash'] = hash_string
        payload['peer_id'] = '-TR2820-wa0n562rl3lu'
        payload['port'] = self.port
        payload['uploaded'] = 0
        payload['downloaded'] = 0
        # pudb.set_trace()
        payload['left'] = self.tdict['info']['length']
        payload['numwant'] = 0
        payload['compact'] = 1
        payload['supportcrypto'] = 1
        self.r = requests.get(self.tdict['announce'],
                              params=payload)


def main():
    tor_dict = tparser.bdecode('torrent.torrent')
    mytorrent = torrent(tor_dict)
    mytorrent.get_request()
    print mytorrent.r.text
    print mytorrent.r


if __name__ == '__main__':
    main()
