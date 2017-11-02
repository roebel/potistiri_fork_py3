#!/usr/bin/env python

from __future__ import print_function

import argparse
# needed for sending very large files when python is not able to read the complete file
from requests_toolbelt import MultipartEncoder
import requests
import re
try:
    import ConfigParser as cfgparse
except ImportError:
    import configparser as cfgparse

import getpass
from string import ascii_lowercase as lowercase, digits
from random import choice
import sys
from os import mkdir, environ
from os.path import isfile, join

# establish Python2/3 compatible input
try: input = raw_input
except NameError: pass

conf_dir = join(environ['HOME'], '.config','potistiri')
conf_file = join(conf_dir, 'servers.conf')

def aneva(server, post_params_list, filepath):
    '''
    This function performs the HTTPS POST request to the coquelicot server.
    "post_params" are constructed as a list of tuples since ordering actually
    matters.
    '''
    try:
        with open(filepath, 'rb') as f:

            post_params = MultipartEncoder(post_params_list+[('file', (filepath, f))])

            server += 'upload' if server.endswith('/') else '/upload'
            try:
                r = requests.post(server, data=post_params, 
                                  headers={'Content-Type': post_params.content_type})
            except Exception as e:
                print("upload failed", file=sys.stderr)
                print(e, file=sys.stderr)
                return None
            
            if r.status_code == 200:
                return [l.split('>')[1].split('<')[0]
                        for l in r.text.split('\n')
                        if re.search('textarea', l) or re.search('available', l)]
            else:
                print('HTTP Error {}'.format(r.status_code), file=sys.stderr)
                return None

    except IOError:
        print( 'File to be uploaded not found or not readable', file=sys.stderr)
        return None


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
        with open(conf_file, 'r') as f:
            try:
                c.readfp(f)
                return c.get(c.sections()[0], arg)
            except (cfgparse.MissingSectionHeaderError,
                    cfgparse.NoOptionError):
                return False
    except IOError:
        return False


def offer_init():
    if not isfile(conf_file):
        mes = 'Want to save your coquelicot provider ' + \
               'details in a config file?\n'
        choice = input(mes).lower()
        if choice in {'yes', 'y', '', ' '}:
            try:
                mkdir(conf_dir)
            except OSError as e:
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

            section = input(service_mes)
            url = input(url_mes)
            c.add_section(section)
            c.set(section, 'server', url)

            authtype = input(authtype_mes)
            c.set(section, 'type', authtype)
            if authtype == 'simple':
                paswd = input(paswd_mes)
                c.set(section, 'pass', paswd)
            elif authtype == 'ldap':
                ldap_user = input(ldap_user_mes)
                c.set(section, 'user', ldap_user)
            with open(conf_file, 'w') as f:
                c.write(f)
        else:
            exit(0)
    else:
        print(conf_file+' already exists. Edit it, lazy!', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', dest='server')
    parser.add_argument('--expire', '-e', default=str(1440*7), help="expiration time in minutes (Def: %(default)s)")
    parser.add_argument('--one-time', '-o', dest='one_time',  action='store_true')
    parser.add_argument('-k', '--file-key',  dest='file_key',  action='store_true')
    ga = parser.add_mutually_exclusive_group(required=True)
    ga.add_argument('-f', '--file', dest='filepath', nargs="+", help="filename to upload")
    ga.add_argument('--setconf', dest='setconf', action='store_true')
    gb = parser.add_mutually_exclusive_group()
    gb.add_argument('-u', '--ldap-user', dest='ldapuser')
    gb.add_argument('-p', '--upload-password', dest='up_pass')
    args = parser.parse_args()

    if args.setconf:
        offer_init()
    else:
        server_type = ''
        if args.server is None:
            args.server = read_conf('server')
            if not args.server:
                print('Missing server argument.',file=sys.stderr)
                exit('Try --setconf to store it in a config file.')
            server_type = read_conf('type')

        if args.up_pass is None and server_type == 'simple':
            args.up_pass = read_conf('pass')
        if args.ldapuser is None and server_type == 'ldap':
            args.ldapuser = read_conf('user')
            ldap_pass = read_conf('pass')
        if not (args.up_pass or args.ldapuser):
            print('Missing connection arguments',file=sys.stderr)
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

        expire_time_min =int(args.expire)
        expire_days = (expire_time_min//1440)
        expire_hs   = (expire_time_min - expire_days*1440)//60
        expire_mins = (expire_time_min - expire_days*1440 - expire_hs*60)
        if expire_days > 0:
            expire_string="{0:d}days:{1:d}hours:{2:d}min".format(expire_days, expire_hs, expire_mins)
        elif expire_hs > 0 :
            expire_string="{0:d}hours:{1:d}min".format(expire_hs, expire_mins)
        else :
            expire_string="{0:d}min".format(expire_mins)

        print("upload mode  oneshot={0} expires={1}".format(args.one_time, expire_string))
        for fpath in  args.filepath:
            if not isfile(fpath):
                print('{} not found or not readable -- skipping.'.format(fpath))
                continue
            res=aneva(args.server, post_params, fpath)
            if res is not None:
                print("{0} -> {res[0]}, {res[1]}".format(fpath, res=res))

        if args.file_key:
            print('Download pass: {}'.format(file_key))

if __name__ == '__main__':
    main()
