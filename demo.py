from pki.ca import CA
from server import Server
from client import run_client, run_chat
import threading
import time

def main():
    ca = CA("Test-CA")
    srv = Server("BankServer", ca, port=5001)
    t = threading.Thread(target=srv.start, daemon=True)
    t.start()
    time.sleep(0.2)
    # single transaction example
    result = run_client(ca, '127.0.0.1', 5001, prefer='SIMON')
    print(result)
    # chat example
    replies = run_chat(ca, '127.0.0.1', 5001, [
        "Hello server",
        "Balance?",
        "Transfer 50",
        "Thanks"
    ], prefer='SPECK', rekey_every=2)
    for r in replies:
        print(r)

if __name__ == '__main__':
    main()
