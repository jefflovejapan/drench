class Visualizer(object):
    # outfile is temporary while I figure out how to implement
    # visualization
    def __init__(self, sock, outfile='derp.txt'):
        self.sock = sock
        self.outfile = open(outfile, 'w')

    def write(self, data):
        self.outfile.write(data)

    def close(self):
        self.outfile.close()
