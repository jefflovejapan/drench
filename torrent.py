import requests
import socket
import tparser
import hashlib
import urllib
import argparse
import pudb


class torrent():

    def __init__(self, torrent_path, port=55308):
        tdict = tparser.bdecode(torrent_path)
        self.tdict = tdict
        self.port = port
        self.r = None

    def get_request(self):
        assert self.tdict['info']
        hashed_info = hashlib.sha1(tparser.bencode(self.tdict['info']))
        hash_string = hashed_info.digest()
        payload = {}
        payload['info_hash'] = hash_string
        payload['peer_id'] = '-TR2820-wa0n562rl3lu'
        payload['port'] = self.port
        payload['uploaded'] = 0
        payload['downloaded'] = 0
        payload['left'] = self.tdict['info']['length']
        payload['numwant'] = 0
        payload['compact'] = 1
        payload['supportcrypto'] = 1
        self.r = requests.get(self.tdict['announce'],
                              params=payload)


def main():
    pudb.set_trace()
    argparser = argparse.ArgumentParser()
    argparser.add_argument('torrent_path')
    args = argparser.parse_args()  # Getting path from command line
    torrent_path = args.torrent_path
    mytorrent = torrent(torrent_path)
    mytorrent.get_request()
    print mytorrent.r.text
    print mytorrent.r


if __name__ == '__main__':
    main()
