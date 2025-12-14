import sys
import threading
import time
from pki.ca import CA
from server import Server


def main():
    port = 5001
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port; using default 5001")
    ca = CA("CLI-CA")
    srv = Server("CLIServer", ca, port=port)
    # Export CA public key so client can verify the server certificate
    with open('ca_pub.json', 'w') as f:
        f.write(ca.export_pub_json())
    # Run in foreground; Server.start() already accepts multiple connections sequentially
    print(f"[Server] Listening on 127.0.0.1:{port}. Start client in another terminal.")
    print("[Server] Wrote CA public key to ca_pub.json (share this with clients).")
    srv.start()

if __name__ == '__main__':
    main()
