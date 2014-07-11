from distutils.core import setup

setup(
    name='Libdw',
    version='0.1',
    author='Oka Kurniawan',
    author_email='oka_kurniawan@sutd.edu.sg',
    packages=['libdw','libdw.test'],
    scripts=[],
    url='',
    license='LICENSE.txt',
    description='Library for 10.009 Digital World.',
    long_description=open('README.txt').read(),
)
