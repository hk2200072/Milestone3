import sys
import socket
from pki.ca import load_ca_pub_from_json
from net.protocol import Handshake, send_json, recv_json, client_rekey

# Interactive client. Usage: python cli_client.py [host] [port] [suite]
# suite: SIMON or SPECK (default SIMON)

def main():
    host = '127.0.0.1'
    port = 5001
    suite = 'SIMON'
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print('Invalid port; using default 5001')
    if len(sys.argv) >= 4:
        suite = sys.argv[3].upper()
    # Load CA public key exported by the server
    try:
        with open('ca_pub.json','r') as f:
            ca_pub_json = f.read()
    except FileNotFoundError:
        print('[Client] Missing ca_pub.json. Copy it from the server terminal directory.')
        return
    ca_pub = load_ca_pub_from_json(ca_pub_json)
    hs = Handshake(ca_pub)
    print(f"[Client] Connecting to {host}:{port} with suite={suite} ...")
    with socket.create_connection((host, port)) as s:
        ch, cert_json = hs.client(s, suite)
        print("[Client] Handshake complete. Type messages; /rekey to rotate keys; /bye to quit.")
        while True:
            try:
                line = input('> ').strip()
            except EOFError:
                line = '/bye'
            if line.lower() == '/bye':
                ct, tag = ch.encrypt(b'BYE')
                send_json(s, {"type":"AppData","ct": ct.hex(), "tag": tag.hex()})
                break
            if line.lower() == '/rekey':
                client_rekey(s, ch, cert_json)
                print('[Client] Rekeyed.')
                continue
            # Echo what you sent
            print(f"[You] {line}")
            ct, tag = ch.encrypt(line.encode())
            send_json(s, {"type":"AppData","ct": ct.hex(), "tag": tag.hex()})
            resp = recv_json(s)
            if not resp or resp.get('type') != 'AppData':
                print('[Client] Server closed connection.')
                break
            rct = bytes.fromhex(resp['ct']) ; rtag = bytes.fromhex(resp['tag'])
            pt = ch.decrypt(rct, rtag)
            try:
                msg = pt.decode()
            except UnicodeDecodeError:
                msg = str(pt)
            print(f"[Server] {msg}")

if __name__ == '__main__':
    main()
