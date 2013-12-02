# setup.py
from setuptools import setup

setup(
    name="drench",
    version="0.1",
    packages=['client.html', 'peer.py', 'torrent.py', 'reactor.py',
              'switchboard.py', 'listener.py', 'tparser.py',
              'visualizer.py'],

    install_requires=['bitarray>=0.8.1'],

    # metadata for upload to PyPI
    maintainer="Jeffrey Blagdon",
    maintainer_email="jeffblagdon@gmail.com",
    description="A simple BitTorrent client",
    license="MIT",
    keywords="bittorrent torrent visualization twisted"
)
