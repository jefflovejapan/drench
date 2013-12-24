# setup.py
from setuptools import setup

setup(
    name="drench",
    version="0.0.10",
    install_requires=['bitarray>=0.8.1', 'requests>=2.0.0'],
    packages=['drench'],

    # metadata for upload to PyPI
    maintainer="Jeffrey Blagdon",
    maintainer_email="jeffblagdon@gmail.com",
    description="A simple BitTorrent client",
    license="MIT",
    url='https://github.com/jefflovejapan/drench',
    keywords="bittorrent torrent visualization twisted"
)
