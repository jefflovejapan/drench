import pudb


class Visualizer(object):
    # outfile is temporary while I figure out how to implement
    # visualization
    def __init__(self, outfile='derp.txt'):
        self.outfile = open(outfile, 'w')
        self.sock = None

    def write(self, data):
        if self.sock:
            self.outfile.write(data + '\n')

    def close(self):
        self.outfile.close()

    def set_sock(self, sock):
        self.sock = sock
