import requests
import socket
import tparser
import hashlib
import argparse
import select
import time
import pudb
import reactor
import cPickle
from bitarray import bitarray


class torrent():

    def __init__(self, torrent_path, port=55308):
        tdict = tparser.bdecode(torrent_path)
        # pudb.set_trace()
        self.tdict = tdict
        self.peerdict = {}
        self.peers = []
        self.port = port
        self.r = None
        self.tresponse = None
        self.peerdict = {}
        self.hash_string = None
        self.rlist = []  # Sockets to check for avail reads
        self.wlist = []  # Sockets to check for avail writes
        self.xlist = []  # Sockets to check for exceptions (?)
        self.reactor = reactor.Reactor()

    @property
    def piece_length(self):
        return self.tdict['info']['piece length']

    @property
    def num_pieces(self):
        # Since there's 20 bytes in the string for each piece
        pieces = divmod(len(self.tdict['info']['pieces']), 20)
        if pieces[1] == 0:
            return pieces[0]
        else:
            # Hash needs to be 20 bytes per piece
            raise ValueError('Torrent file error -- bad hash')

    @property
    def length(self):
        return self.tdict['info']['length']

    @property
    def last_piece_length(self):
        return self.length - (self.piece_length * (self.num_pieces - 1))


#     def build_payload(self):
#         payload = {}
#         hashed_info = hashlib.sha1(tparser.bencode(self.tdict['info']))
#         self.hash_string = hashed_info.digest()
#         self.peer_id = '-TR2820-wa0n562rl3lu'  # TODO: randomize
#         payload['info_hash'] = self.hash_string
#         payload['peer_id'] = self.peer_id
#         payload['port'] = self.port
#         payload['uploaded'] = 0
#         payload['downloaded'] = 0
#         payload['left'] = self.tdict['info']['length']
#         payload['compact'] = 1
#         payload['supportcrypto'] = 1
#         payload['event'] = 'started'
#         return payload

#     # TODO - create peer objects with ref to reactor
#     def get_peers(self):
#         presponse = [ord(i) for i in self.tresponse['peers']]
#         while presponse:
#             peer = (('.'.join(str(x) for x in presponse[0:4]), 256*presponse[4]
#                      + presponse[5]))
#             if peer not in self.peers:
#                 self.peers.append(peer)
#             presponse = presponse[6:]

#     def event_loop(self):
#         while 1:
#             rrlist, rwlist, rxlist = select.select(self.rlist, self.wlist,
#                                                    self.xlist)
#             if rrlist:
#                 self.do_reads(rrlist)
#             if rwlist:
#                 self.do_writes(rwlist)
#             if rxlist:
#                 self.handle_exceptions(rxlist)
#             for psocket in self.peerdict.keys():
#                 self.request(psocket)
#             time.sleep(0.1)

#     def do_reads(self, rrlist):
#         for i in rrlist:
#             message_length = self.peerdict[i].get_message_length()
#             message_id = self.peerdict[i].get_message_id()
#             message = self.peerdict[i].get_message(i, message_length-1)
#             self.handle_message(i, message_id, message)

#     def handshake_peers(self):
#         def phandshake_clos(self):
#             pstr = 'BitTorrent protocol'
#             pstrlen = len(pstr)
#             info_hash = self.hash_string
#             peer_id = self.peer_id

#             '''
#             pstrlen = length of pstr as one byte
#             pstr = BitTorrent protocol
#             reserved = chr(0)*8
#             info_hash = 20-byte hash above (aka self.hash_string)
#             peer_id = 20-byte string
#             '''
#             packet = ''.join([chr(pstrlen), pstr, chr(0)*8, info_hash,
#                               peer_id])
#             print "Here's my packet {}".format(packet)
#             for i in self.peers:
#                 print i  # just want to see who i'm talking to
#                 s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 s.setblocking(True)
#                 s.settimeout(0.5)
#                 try:
#                     s.connect(i)
#                     s.send(packet)
#                     try:
#                         data = s.recv(68)  # Peer's handshake - len from docs
#                         if data:
#                             print 'From {} received: {}'.format(i, data)
#                             s.setblocking(False)
#                             self.initpeer(s)
#                     except socket.error as e:
#                         print e.message

#                 except socket.timeout:
#                     print 'timed out'
#             else:
#                 self.event_loop()
#         return phandshake_clos

#     # TODO -- add call to this for any new peers I get from tracker
#     def initpeer(self, s):
#         self.rlist.append(s)  # I'm adding to my rlist for event loop
#         self.track_peer(s)  # But I'm also adding to peerdict.
#         self.interested(s)
#         self.unchoke(s)  # Otherwise they won't send me anything (?)

#     def track_peer(self, psocket):
#         if psocket not in self.peerdict.keys():
#             self.peerdict[psocket] = {}

#     def tracker_request(self):
#         assert self.tdict['info']
#         payload = self.build_payload()
#         self.r = requests.get(self.tdict['announce'],
#                               params=payload)
#         print len(self.r.text)
#         self.tresponse = tparser.bdecodes(self.r.text.encode('latin-1'))
#         self.get_peers()


# def main():
#     argparser = argparse.ArgumentParser()
#     argparser.add_argument('torrent_path')
#     args = argparser.parse_args()  # Getting path from command line
#     torrent_path = args.torrent_path
#     mytorrent = torrent(torrent_path)
#     mytorrent.tracker_request()
#     mytorrent.handshake_peers()


# if __name__ == '__main__':
#     main()
