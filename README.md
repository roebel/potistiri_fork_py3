# potistiri

potistiri is a python cli client for [coquelicot](https://coquelicot.potager.org/) file sharing instances. Currently supports two authentication methods: 'simplepass' and 'ldap'.

## Installation

potistiri is a python script, consequently there are multiple ways to run it. Probably this will be sufficient:

    wget https://gitlab.com/irregulator/potistiri/raw/master/potistiri.py -O /usr/local/bin/potistiri
    chmod +x /usr/local/bin/potistiri

Alternatively, just clone the repository and run it from there.

## Configuration

potistiri has a configuration file placed in:

    ~/.config/potistiri/servers.conf

This conf file can store connection details for a certain coquelicot instance such as the service's url, authentication type and authentication credentials.

You can run potistiri with the '--setconf' parameter in order to initialize the configuration file. Alternatively,you may directly create and edit the file.

## Usage


