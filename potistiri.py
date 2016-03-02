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


def ldap_post(ldap_user, ldap_pass, expire, one_time, file_key):
    '''
    This function constructs POST parameters
    for coquelicot instances with LDAP authentication.
    '''
    post_params = [
        ('ldap_user', str(ldap_user)),
        ('ldap_password', str(ldap_pass)),
        ('any_number', 'true' if not one_time else ''),
        ('expire', str(expire)),
        ('one_time', 'true' if one_time else ''),
        ('file_key', str(file_key)),
        ]

    return post_params


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
            service_mes = 'Type a short name of the service: '
            url_mes = 'Type the https:// address of the file server: '
            authtype_mes = 'Authentication offered by this provider, ' + \
                           'type "simple" or "ldap": '
            paswd_mes = 'Type the upload pass used for this server: '
            ldap_user_mes = 'Type the ldap user: '

            section = raw_input(service_mes)
            url = raw_input(url_mes)
            c.add_section(section)
            c.set(section, 'server', url)

            authtype = raw_input(authtype_mes)
            c.set(section, 'type', authtype)
            if authtype == 'simple':
                paswd = raw_input(paswd_mes)
                c.set(section, 'pass', paswd)
            elif authtype == 'ldap':
                ldap_user = raw_input(ldap_user_mes)
                c.set(section, 'user', ldap_user)
            with open(conf_dir + 'servers.conf', 'wb') as f:
                c.write(f)
        else:
            exit(0)
    else:
        print(conf_dir + 'servers.conf already exists. Edit it, lazy!')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', dest='server')
    parser.add_argument('--expire', '-e', dest='expire', default='60')
    parser.add_argument('--one-time', '-o', dest='one_time',
                        action='store_true')
    parser.add_argument('--file-key', '-k', dest='file_key',
                        action='store_true')
    ga = parser.add_mutually_exclusive_group(required=True)
    ga.add_argument('--file', '-f', dest='filepath')
    ga.add_argument('--setconf', dest='setconf', action='store_true')
    gb = parser.add_mutually_exclusive_group()
    gb.add_argument('--ldap-user', '-u', dest='ldapuser')
    gb.add_argument('--upload-password', '-p', dest='up_pass')
    args = parser.parse_args()

    if args.setconf:
        offer_init()
    else:
        fpath = args.filepath
        server_type = ''
        if not isfile(fpath):
            exit('{} not found or not readable.'.format(fpath))
        if args.server is None:
            args.server = read_conf('server')
            if not args.server:
                print('Missing server argument.')
                exit('Try --setconf to store it in a config file.')
            server_type = read_conf('type')

        if args.up_pass is None and server_type == 'simple':
            args.up_pass = read_conf('pass')
        if args.ldapuser is None and server_type == 'ldap':
            args.ldapuser = read_conf('user')
            ldap_pass = read_conf('pass')
        if not (args.up_pass or args.ldapuser):
            print('Missing connection arguments')
            exit('Try --setconf to store them in a config file.')
        if args.ldapuser and server_type == 'simple':
            exit('Cannot use ldap authentication with this type of provider.')
        if args.up_pass and server_type == 'ldap':
            exit('Cannot use simple pass authentication with ldap provider.')
        if args.ldapuser and not ldap_pass:
            m = 'Type ldap password: '
            ldap_pass = getpass.getpass(m)

        if args.file_key:
            m = 'Type passphrase to lock the uploaded file. ' + \
                'Or just hit enter to create one for you: '
            file_key = getpass.getpass(m)
            if not file_key:
                file_key = ''.join(choice(lowercase+digits) for _ in range(25))

        if args.up_pass:
            post_params = pass_post(args.up_pass,
                                    args.expire,
                                    args.one_time,
                                    file_key if args.file_key else '')
        else:
            post_params = ldap_post(args.ldapuser,
                                    ldap_pass,
                                    args.expire,
                                    args.one_time,
                                    file_key if args.file_key else '')

        print(aneva(args.server, post_params, fpath))
        if args.file_key:
            print('Download pass: {}'.format(file_key))

if __name__ == '__main__':
    main()
