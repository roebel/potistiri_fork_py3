#!/usr/bin/env python

import argparse
import requests
import re
import ConfigParser as cfgparse
import getpass
from string import ascii_lowercase as lowercase, digits
from random import choice


def aneva(server, up_pass, expire, one_time, file_key, filepath):
    try:
        with open(filepath, 'rb') as f:
            files_list = [
                ('upload_password', str(up_pass)),
                ('any_number', 'true' if not one_time else ''),
                ('expire', str(expire)),
                ('one_time', 'true' if one_time else ''),
                ('file_key', str(file_key)),
                ('file', f)
                ]

            server += 'upload' if server.endswith('/') else '/upload'
            try:
                r = requests.post(server, files=files_list)
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


def read_conf(arg):
    c = cfgparse.ConfigParser()
    try:
        with open('/home/' + getpass.getuser() + '/.potistirirc', 'rb') as f:
            try:
                c.readfp(f)
                return c.get(c.sections()[0], arg)
            except (cfgparse.MissingSectionHeaderError,
                    cfgparse.NoOptionError):
                return False
    except IOError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', dest='server')
    parser.add_argument('--upload-password', '-p', dest='up_pass')
    parser.add_argument('--expire', '-e', dest='expire', default='60')
    parser.add_argument('--one-time', '-o', dest='one_time',
                        action='store_true')
    parser.add_argument('--file-key', '-k', dest='file_key',
                        action='store_true')
    parser.add_argument('--file', '-f', dest='filepath', required=True)
    args = parser.parse_args()

    if args.server is None:
        args.server = read_conf('server')
    if args.up_pass is None:
        args.up_pass = read_conf('pass')
    if not (args.server and args.up_pass):
        exit('Missing server and/or upload-password arguments')
    if args.file_key:
        m = 'Type passphrase to lock the uploaded file. ' + \
              'Or just hit enter to create one for you: '
        file_key = getpass.getpass(m)
        if not file_key:
            file_key = ''.join(choice(lowercase+digits) for _ in range(25))

    print(aneva(
        args.server,
        args.up_pass,
        args.expire,
        args.one_time,
        file_key if args.file_key else '',
        args.filepath))
    if args.file_key:
        print('Download pass: {}'.format(file_key))

if __name__ == '__main__':
    main()
