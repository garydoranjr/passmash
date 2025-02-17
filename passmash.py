#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Author: Tim Henderson
#Email: tim.tadh@hackthology.com
#For licensing see the LICENSE file in the top level directory.

import sys, os
from getpass import getpass
from getopt import getopt, GetoptError
import hmac
from hashlib import sha256

RELEASE = 'master'

usage_message = \
'''usage: passmash [options] url '''

extended_message = \
'''
Options

    -h, help                     Display this message
    -c, clamp=N                  Don't output more than N characters
    -s, strip                    Strip non-alpha-numberic characters
    -v, version                  Version information


Explanation

    Produces a password for a website based on
        - url (supplied as a commandline argument)
        - password (supplied at interactive prompt)
        - keyfile (located at ~/.ssh/passmash.key)
    
    We recomend the keyfile be random data. eg.

        $ head -c 512 /dev/urandom > ~/.ssh/passmash.key

    The hashing algorithm is:

        h = hmac.new(key, password, sha256)
        h.update(url)
        for i in xrange(25000):
            h.update(h.digest())
        return h.digest()
'''

error_codes = {
    'usage':1,
    'version':2,
    'option':3,
}

def keyfile():
    keyfile = os.path.expanduser('~/.ssh/passmash.key')
    with open(keyfile, 'rb') as f:
        key = f.read()
    return key

def hashfile():
    keyfile = os.path.expanduser('~/.ssh/passmash.hash')
    if os.path.exists(keyfile):
        with open(keyfile, 'rb') as f:
            key = f.read()
        return key

def save_hashfile(hash):
    keyfile = os.path.expanduser('~/.ssh/passmash.hash')
    with open(keyfile, 'wb+') as f:
        f.write(hash)

def mash(key, url, password):
    h = hmac.new(key, password, sha256)
    h.update(url)
    for i in xrange(250000):
        h.update(h.digest())
    return h.digest()

def pretty(hash):
    return hash.encode('base64').strip().rstrip('=')

def log(msg):
    print >>sys.stderr, msg

def output(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def usage(code=None):
    '''Prints the usage and exits with an error code specified by code. If code
    is not given it exits with error_codes['usage']'''
    log(usage_message)
    if code is None:
        log(extended_message)
        code = error_codes['usage']
    sys.exit(code)


def main():
    try:
        opts, args = getopt(sys.argv[1:],
            'hvc:s',
            ['help', 'version', 'clamp=', 'strip'])
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])
    
    url = ' '.join(args).strip()
    if not url:
        usage()
    
    clamp = None
    strip = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-v', '--version'):
            log(RELEASE)
            sys.exit(error_codes['version'])
        elif opt in ('-c', '--clamp'):
            clamp = int(arg)
        elif opt in ('-s', '--strip'):
            strip = True
   
    key = keyfile()
    saved_hash = hashfile()

    confirmed = False
    attempts = 0
    while not confirmed and attempts < 5:
        attempts += 1
        password = getpass()
        if saved_hash is None:
            password_conf = getpass("Confirm:")
            if password != password_conf:
                log('Passwords do not match.\n')
                continue
            save_hashfile(sha256(password + key).hexdigest())
            confirmed = True
        else:
            if sha256(password + key).hexdigest() != saved_hash:
                log('Passwords do not match.\n')
                continue
            confirmed = True

    mashed = pretty(mash(key, url, password))
    if strip:
        mashed = ''.join(c for c in mashed if c.isalnum())
    if clamp is None: 
        clamp = len(mashed)
    output(mashed[:min(clamp, len(mashed))])
    log('')


if __name__ == '__main__':
    main()

