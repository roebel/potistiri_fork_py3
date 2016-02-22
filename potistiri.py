#!/usr/bin/env python

import argparse
import requests
import re
import ConfigParser as cfgparse
import getpass
from string import ascii_lowercase as lowercase, digits
from random import choice
from os import mkdir
from os.path import isfile

conf_dir = '/home/' + getpass.getuser() + '/.config/potistiri/'


def aneva(server, post_params, filepath):
    '''
    This function performs the HTTPS POST request to the coquelicot server.
    "post_params" are constructed as a list of tuples since ordering actually
    matters.
    '''
    try:
        with open(filepath, 'rb') as f:
            post_params += [('file', f)]

            server += 'upload' if server.endswith('/') else '/upload'
            try:
                r = requests.post(server, files=post_params)
            except Exception as e:
                print(e)

            if r.status_code == 200:
                return [l.split('>')[1].split('<')[0]
                        for l in r.text.split('\n')
                        if re.search('textarea', l)][0]
            else:
                return 'HTTP Error {}'.format(r.status_code)
    except IOError:
        return 'File to be uploaded not found or not readable'


def pass_post(up_pass, expire, one_time, file_key):
    '''
    This function constructs POST parameters
    for coquelicot instances with simple upload password.
    '''
    post_params = [
        ('upload_password', str(up_pass)),
        ('any_number', 'true' if not one_time else ''),
        ('expire', str(expire)),
        ('one_time', 'true' if one_time else ''),
        ('file_key', str(file_key)),
        ]

    return post_params


def ldap_post():
    '''
    This function constructs POST parameters
    for coquelicot instances with LDAP authentication.
    '''
    pass


def read_conf(arg):
    c = cfgparse.ConfigParser()
    try:
        with open(conf_dir + 'servers.conf', 'rb') as f:
            try:
                c.readfp(f)
                return c.get(c.sections()[0], arg)
            except (cfgparse.MissingSectionHeaderError,
                    cfgparse.NoOptionError):
                return False
    except IOError:
        return False


def offer_init():
    if not isfile(conf_dir + 'servers.conf'):
        mes = 'Want to save your coquelicot provider ' + \
               'details in a config file?\n'
        choice = raw_input(mes).lower()
        if choice in {'yes', 'y', '', ' '}:
            try:
                mkdir(conf_dir)
            except OSError, e:
                if e.errno == 17:
                    pass
                else:
                    exit(1)
            except IOError:
                exit(1)
            c = cfgparse.RawConfigParser()
            service_mes = 'Type the name of the service: '
            url_mes = 'Type the https:// address of the file server: '
            paswd_mes = 'Type the upload pass used for this server: '
            section = raw_input(service_mes)
            url = raw_input(url_mes)
            paswd = raw_input(paswd_mes)
            c.add_section(section)
            c.set(section, 'server', url)
            c.set(section, 'pass', paswd)
            with open(conf_dir + 'servers.conf', 'wb') as f:
                c.write(f)
        else:
            exit(0)
    else:
        print(conf_dir + 'servers.conf already exists. Edit it, lazy!')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', dest='server')
    parser.add_argument('--upload-password', '-p', dest='up_pass')
    parser.add_argument('--expire', '-e', dest='expire', default='60')
    parser.add_argument('--one-time', '-o', dest='one_time',
                        action='store_true')
    parser.add_argument('--file-key', '-k', dest='file_key',
                        action='store_true')
    ga = parser.add_mutually_exclusive_group(required=True)
    ga.add_argument('--file', '-f', dest='filepath')
    ga.add_argument('--setconf', dest='setconf', action='store_true')
    args = parser.parse_args()

    if args.setconf:
        offer_init()
    else:
        fpath = args.filepath
        if not isfile(fpath):
            exit('{} not found or not readable.'.format(fpath))
        if args.server is None:
            args.server = read_conf('server')
        if args.up_pass is None:
            args.up_pass = read_conf('pass')
        if not (args.server and args.up_pass):
            print('Missing server and/or upload-password arguments')
            exit('Try --setconf to store them in a config file.')
        if args.file_key:
            m = 'Type passphrase to lock the uploaded file. ' + \
                'Or just hit enter to create one for you: '
            file_key = getpass.getpass(m)
            if not file_key:
                file_key = ''.join(choice(lowercase+digits) for _ in range(25))

        print(aneva(
            args.server,
            pass_post(args.up_pass,
                      args.expire,
                      args.one_time,
                      file_key if args.file_key else ''),
            fpath))
        if args.file_key:
            print('Download pass: {}'.format(file_key))

if __name__ == '__main__':
    main()
