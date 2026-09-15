#!/usr/bin/env python3
"""Test/benchmark client for the native session protocol."""
import socket
import uuid
from pathlib import Path


def encode(value):
    if isinstance(value, str):
        value = value.encode()
    if isinstance(value, bytes):
        return str(len(value)).encode() + b':' + value
    if isinstance(value, dict):
        return b'd' + b''.join(encode(k) + encode(v) for k, v in sorted(value.items())) + b'e'
    raise TypeError(value)


def decode(stream):
    head = stream.read(1)
    if head == b'd':
        out = {}
        while stream.peek(1)[:1] != b'e':
            key = decode(stream)
            out[key] = decode(stream)
        stream.read(1)
        return out
    if head == b'l':
        out = []
        while stream.peek(1)[:1] != b'e':
            out.append(decode(stream))
        stream.read(1)
        return out
    if not head or not head.isdigit():
        raise ValueError(f'invalid bencode prefix {head!r}')
    length = head
    while True:
        byte = stream.read(1)
        if byte == b':':
            break
        if not byte.isdigit():
            raise ValueError('invalid string length')
        length += byte
    count = int(length)
    data = stream.read(count)
    if len(data) != count:
        raise EOFError('truncated reply')
    return data.decode()


class Client:
    def __init__(self):
        self.socket = socket.create_connection(('127.0.0.1', int(Path('.nrepl-port').read_text())), timeout=30)
        self.stream = self.socket.makefile('rb')
        self.token = Path('.live-token').read_text()
        self.next_id = 0
        self.client_id = uuid.uuid4().hex

    def request(self, op, **fields):
        self.next_id += 1
        request = {'op': op, 'id': f'client-{self.client_id}-{self.next_id}', 'token': self.token, **fields}
        self.socket.sendall(encode(request))
        return decode(self.stream)

    def close(self):
        self.stream.close()
        self.socket.close()
