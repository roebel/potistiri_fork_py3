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

This file can store connection details for a certain coquelicot instance such as the service's url, authentication type and authentication credentials.

You can run potistiri with the '--setconf' parameter in order to initialize the configuration file. Alternatively,you may directly create and edit the file.

Sample configurations files are included in this repo, one for each authentication type, but it's basically like this.

### LDAP ###

    [some_service_name]
    server = https://files.provider.org
    type = ldap
    user = myuser

in case the coquelicot provider needs LDAP authentication. For LDAP providers you may also store the LDAP pass in the conf, but that's probably a bad idea. Also mind the permissions of the configuration file, perhaps:

    chmod o-r ~/.config/potistiri/servers.conf

### simple pass ###

In case of a provider with simple pass authentication conf should look like that:

    [some_service_name]
    server = https://files.someprovider.org
    type = simple
    pass = some-upload-password

This pass is actually globally set for the provider and not bound to each user, thus can be considered safe to write on disk.

## Usage

All the options offered in a coquelicot instance web UI can be passed as parameters to potistiri. Specifically:

- -s/--server <url> : the url of the coquelicot provider
- -f/--file <filepath>: the path to the file to be uploaded
- -e/--expire <minutes> : lifetime of the uploaded file in minutes
- -o/--one-time : if set file will be available only for a single download
- -k/--file-key <string> : a phrase key to symmetrically encrypt the uploaded file
- -p/--upload-password <pass> : auth in case of a simple pass provider
- -u/--ldap-user <user> : user in case of a LDAP provider
- --setconf : guides user through configuration file initialization

### Usage examples ###

    potistiri --setconf
    potistiri -f /tmp/ko
    potistiri -s https://file.ohmy.net -p passme -f /tmp/la
    potistiri -s https://arxeio.net -u ldapalex -f mysecrets.yaml
