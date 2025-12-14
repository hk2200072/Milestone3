import socket
import json
from pki.ca import CA, Entity
from net.protocol import Handshake, send_json, recv_json, client_rekey

class Client(Entity):
    def __init__(self, name: str):
        super().__init__(name)

def run_client(ca: CA, server_host: str, server_port: int, prefer: str = 'SIMON'):
    hs = Handshake(ca.pub)
    with socket.create_connection((server_host, server_port)) as s:
        ch, cert_json = hs.client(s, prefer)
        msg = b"TRANSFER: from=Alice to=Bob amount=100"
        ct, tag = ch.encrypt(msg)
        send_json(s, {"type":"AppData","ct": ct.hex(), "tag": tag.hex()})
        resp = recv_json(s)
        if resp.get("type") == "AppData":
            rct = bytes.fromhex(resp["ct"]) ; rtag = bytes.fromhex(resp["tag"])
            pt = ch.decrypt(rct, rtag)
            return pt.decode()
        return ""

import time

def run_chat(ca: CA, server_host: str, server_port: int, messages, prefer: str = 'SIMON', rekey_every: int = 3, rotate_seconds: int = 3600):
    hs = Handshake(ca.pub)
    replies = []
    with socket.create_connection((server_host, server_port)) as s:
        ch, cert_json = hs.client(s, prefer)
        last_rekey = time.time()
        for i, m in enumerate(messages, 1):
            now = time.time()
            if rotate_seconds and (now - last_rekey) >= rotate_seconds:
                client_rekey(s, ch, cert_json)
                last_rekey = now
            if rekey_every and i % rekey_every == 0:
                client_rekey(s, ch, cert_json)
                last_rekey = time.time()
            ct, tag = ch.encrypt(m.encode())
            send_json(s, {"type":"AppData","ct": ct.hex(), "tag": tag.hex()})
            resp = recv_json(s)
            if resp.get("type") != "AppData":
                break
            rct = bytes.fromhex(resp["ct"]) ; rtag = bytes.fromhex(resp["tag"])
            pt = ch.decrypt(rct, rtag)
            replies.append(pt.decode())
        # send BYE
        ct, tag = ch.encrypt(b"BYE")
        send_json(s, {"type":"AppData","ct": ct.hex(), "tag": tag.hex()})
    return replies
