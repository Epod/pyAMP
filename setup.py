from setuptools import setup

setup(
    name='pyAMP',
    version='1.0',
#    packages=[''],
    url='',
    license='',
    author='Epod',
    author_email='epod@linux.com',
    description='Easier interaction with Cisco AMP via the API, including executing actions not avalible through the GUI',
    install_requires=['menu3', 'requests', 'pandas']
)
