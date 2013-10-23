import requests
import socket
import tparser
import hashlib
import argparse
import struct
import select
import time
import pudb
import processor
import tpeer


class torrent():

    def __init__(self, torrent_path, port=55308):
        tdict = tparser.bdecode(torrent_path)
        self.tdict = tdict
        self.port = port
        self.r = None
        self.tresponse = None
        self.peerdict = {}
        self.hash_string = None
        self.rlist = []  # Sockets to check for avail reads
        self.wlist = []  # Sockets to check for avail writes
        self.xlist = []  # Sockets to check for exceptions (?)
        self.processor = processor.processor()

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
        # pudb.set_trace()
        print 'downloading from peer {}'.format(psocket.getpeername())
        while True:
            '''
            "Unchoke" message
            len = 0001
            id = 2
            '''
            psocket.send(struct.pack('>ib', 1, 1))
            unresponse = psocket.recv(1000)
            print unresponse

            '''
            "Request" message
            len = 0013
            id = 6
            index = whatever 0-based piece index
            begin = whatever 0-based block within piece to start at
            '''
            psocket.send(struct.pack('>ibii', 13, 6, 0, 0))
            response = psocket.recv(2**14)
            print 'The length of the response is {}'.format(len(response))

    def get_message_length(self, psocket):
        length = struct.unpack('>i', psocket.recv(4))[0]
        return length

    def get_message(self, psocket, length):
        message = psocket.recv(length)
        if len(message) == length:
            return message
        else:
            self.save_state(psocket, message, length)

    def get_message_id(self, psocket):
        message_id = struct.unpack('b', psocket.recv(1))
        return message_id

    def event_loop(self):
        while 1:
            rrlist, rwlist, rxlist = select.select(self.rlist, self.wlist,
                                                   self.xlist)
            print rrlist, rwlist, rxlist
            for i in rrlist:
                message_length = self.get_message_length(i)
                message_id = self.get_message_id(i)
                message = self.get_message(i, message_length-1)
                self.handle_message(message_id, message)

            time.sleep(1)

    def handle_message(self, message_id, message):
        pass

    def save_state(self, psocket, message, length):
        pass

    def handshake_peers(self):
        pstr = 'BitTorrent protocol'
        pstrlen = len(pstr)
        info_hash = self.hash_string
        peer_id = self.peer_id

        '''
        pstrlen = length of pstr as one byte
        pstr = BitTorrent protocol
        reserved = chr(0)*8
        info_hash = 20-byte hash above (aka self.hash_string)
        peer_id = 20-byte string
        '''
        packet = ''.join([chr(pstrlen), pstr, chr(0)*8, info_hash, peer_id])
        print "Here's my packet {}".format(packet)
        for i in self.peers:
            print i  # just want to see who i'm talking to
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(True)
            s.settimeout(0.5)
            try:
                s.connect(i)
                s.send(packet)
                data = s.recv(68)  # Peer's handshake back (length from docs)
                print 'From {} received: {}'.format(i, data)
                if data:
                    s.setblocking(False)
                    self.rlist.append(s)
            except socket.timeout:
                print 'timed out'
        else:
            self.event_loop()

    def tracker_request(self):
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
    mytorrent.tracker_request()
    mytorrent.handshake_peers()


if __name__ == '__main__':
    main()
