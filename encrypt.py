#!/usr/bin/env python3
import os
import contextlib
import argparse
import Crypto
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
MAC_SIZE = 16
CHUNK_SIZE = 128*1024


@contextlib.contextmanager
def open_if_path(file, *args, **kwargs):
    if isinstance(file, (str, bytes, os.PathLike)):
        with open(file, *args, **kwargs) as file:
            yield file
    else:
        yield file


def encrypt_file(infile, outfile, password):
    with open_if_path(infile, 'rb') as infile, \
         open_if_path(outfile, 'wb') as outfile:
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = os.urandom(SALT_SIZE)
        key = PBKDF2(password, salt, KEY_SIZE, count=100_000,
                     hmac_hash_module=SHA256)
        nonce = os.urandom(NONCE_SIZE)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=MAC_SIZE)
        outfile.write(salt)
        outfile.write(nonce)

        while chunk := infile.read(CHUNK_SIZE):
            outfile.write(cipher.encrypt(chunk))

        outfile.write(cipher.digest())


def decrypt_file(infile, outfile, password):
    with open_if_path(infile, 'rb') as infile, \
         open_if_path(outfile, 'wb') as outfile:
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = infile.read(SALT_SIZE)
        nonce = infile.read(NONCE_SIZE)
        key = PBKDF2(password, salt, KEY_SIZE, count=100_000,
                     hmac_hash_module=SHA256)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=MAC_SIZE)

        digest = b''
        while chunk := infile.read(CHUNK_SIZE):
            chunk = digest + chunk
            chunk, digest = chunk[:-MAC_SIZE], chunk[-MAC_SIZE:]
            outfile.write(cipher.decrypt(chunk))

        cipher.verify(digest)


def get_out_file_name(infile, decrypt):
    if decrypt:
        base, ext = os.path.splitext(infile)
        if ext == '.enc':
            infile = base
        return infile + '.dec'
    else:
        return infile + '.enc'


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('infile')
    p.add_argument('password')
    p.add_argument('-o', '--outfile')
    p.add_argument('-d', '--decrypt', action='store_true')
    args = p.parse_args()

    if not args.outfile:
        args.outfile = get_out_file_name(args.infile, args.decrypt)

    if args.decrypt:
        decrypt_file(args.infile, args.outfile, args.password)
    else:
        encrypt_file(args.infile, args.outfile, args.password)
