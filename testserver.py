import socket
import select


def event_loop(mysocket, outfile):
    while 1:
        readsocks = select.select([mysocket], [], [])
        if readsocks:
            in_data = readsocks[0][0].recv(10000)
            outfile.write(in_data)


def main():
    outfile = open('derp.txt', 'w')
    mysocket = socket.socket()
    mysocket.connect(('127.0.0.1', 7005))
    event_loop(mysocket, outfile)


if __name__ == '__main__':
    main()
