import socket
import threading
from pki.ca import CA, Entity
from pki.cert import Certificate
from net.protocol import Handshake, send_json, recv_json, handle_rekey_msg
from net import metrics

class Server(Entity):
    def __init__(self, name: str, ca: CA, host: str='127.0.0.1', port: int=5000, interactive: bool=True):
        super().__init__(name)
        self.ca = ca
        self.host = host
        self.port = port
        self.interactive = interactive
        self.enroll(ca, "ELGAMAL")
        self._cert_json = self.cert.to_json()
        self._priv = self.priv
    def start(self):
        hs = Handshake(self.ca.pub)
        def get_cert_json():
            return self._cert_json
        get_cert_json._priv = self._priv  # type: ignore
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(5)
            while True:
                conn, addr = srv.accept()
                with conn:
                    ch = hs.server(conn, get_cert_json)
                    metrics.reset()
                    while True:
                        msg = recv_json(conn)
                        if msg is None:
                            break
                        if msg.get("type") == "Rekey":
                            handle_rekey_msg(msg, conn, ch, self._priv)
                            continue
                        if msg.get("type") != "AppData":
                            break
                        ct = bytes.fromhex(msg["ct"]) ; tag = bytes.fromhex(msg["tag"])
                        pt = ch.decrypt(ct, tag)
                        if pt == b"BYE":
                            print("[Server] Client requested to close.")
                            break
                        # Interactive vs non-interactive reply
                        if self.interactive:
                            try:
                                text = pt.decode()
                            except UnicodeDecodeError:
                                text = str(pt)
                            print(f"[Client] {text}")
                            try:
                                reply = input("Server> ")
                            except EOFError:
                                reply = ""
                            rbytes = reply.encode()
                        else:
                            # auto-reply for benchmarks/demos
                            rbytes = b"SRV:" + pt
                        rct, rtag = ch.encrypt(rbytes)
                        send_json(conn, {"type":"AppData","ct": rct.hex(), "tag": rtag.hex()})
                    # print metrics for visibility per session
                    print("Server metrics:", metrics.summary())
