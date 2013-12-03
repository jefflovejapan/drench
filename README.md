#Drench

Drench is a lightweight BitTorrent client written in Python. There are a couple of nice features, like the ability to download a subset of all the files in the torrent and exiting cleanly once the download is complete. Ultimately, the plan is to incorporate a JavaScript-based visualization to let the user see what's going on while the program runs.

##Install

The preferred way to install Drench is will be with [`pip`](http://www.pip-installer.org/en/latest/installing.html), which will let you run the following command from the terminal:

`pip install drench`

##Use

From the command line enter the following:

`python drench ./mytorrent.torrent --port 8000 --directory ~/Downloads/`

`./mytorrent.torrent`: The location of your torrent file (required)

`--port 8000`: The port to use for BitTorrent traffic (optional)

`--directory ~/Downloads`: Where to save your download (optional)

Drench isn't capable of downloading multiple torrents at once; just start up a second instance in another terminal instead.

##Status

You can use Drench to download torrent files from the small handful of sites I've tested on. 

What doesn't work:
- Visualization
- Seeding
- Magnet links
- UDP-based handshake with tracker



