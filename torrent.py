# Preprocessing of the .torrent performed with bdecode

import requests
import socket
import tparser
import hashlib
import urllib
# import pudb


class torrent():

    def __init__(self, tdict):
        self.tdict = tdict

    def get_request(self):
        assert self.tdict['info']
        hashed_info = hashlib.sha1(tparser.bencode(self.tdict['info']))
        # Get a hashy string
        url_string = urllib.urlencode({'myhashything': hashed_info.digest()})
        print url_string.strip('myhashything=')


def main():
    # pudb.set_trace()
    tor_dict = tparser.bdecode('torrent.torrent')
    mytorrent = torrent(tor_dict)
    mytorrent.get_request()

    # http://thomasballinger.com:6969/announce?
    # info_hash=%2b%15%ca%2b%fdH%cd%d7m9%ecU%a3%ab%1b%8aW%18%0a%09
    # peer_id=-TR2820-jlt0de3likus
    # port=55251
    # uploaded=0
    # downloaded=0
    # left=1277987
    # numwant=0
    # key=556b1696
    # compact=1&
    # upportcrypto=1
    # event=stopped


if __name__ == '__main__':
    main()
