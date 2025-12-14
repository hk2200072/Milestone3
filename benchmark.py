import time
from pki.ca import CA
from server import Server
from client import run_chat
import threading
from net import metrics

def run_once(ca, n_messages, msg_size, suite, rekey_every, port):
    metrics.reset()
    messages = ["M"*msg_size for _ in range(n_messages)]
    t0 = time.perf_counter()
    replies = run_chat(ca, '127.0.0.1', port, messages, prefer=suite, rekey_every=rekey_every, rotate_seconds=0)
    t1 = time.perf_counter()
    total_time = t1 - t0
    m = metrics.summary()
    return {
        'suite': suite,
        'n': len(replies),
        'size': msg_size,
        'rekey_every': rekey_every,
        'time_sec': round(total_time, 6),
        'throughput_msgs_per_sec': round(len(replies)/total_time, 2) if total_time>0 else None,
        'bytes_sent': m['bytes_sent'],
        'bytes_received': m['bytes_received'],
        'total_bytes': m['total_bytes'],
        'avg_bytes_per_msg': int(m['total_bytes']/max(1,len(replies)))
    }

def run_benchmark():
    ca = CA("Bench-CA")
    port = 5002
    srv = Server("BenchServer", ca, port=port, interactive=False)
    t = threading.Thread(target=srv.start, daemon=True)
    t.start()
    time.sleep(0.3)
    suites = ['SIMON','SPECK','DOUBLE']
    sizes = [64, 256, 1024]
    n_messages = 200
    rekey_every = 50
    results = []
    for s in suites:
        for sz in sizes:
            results.append(run_once(ca, n_messages, sz, s, rekey_every, port))
    # Print summary table
    print("suite,n,size,rekey_every,time_sec,throughput,bytes_sent,bytes_received,total_bytes,avg_bytes_per_msg")
    for r in results:
        print(f"{r['suite']},{r['n']},{r['size']},{r['rekey_every']},{r['time_sec']},{r['throughput_msgs_per_sec']},{r['bytes_sent']},{r['bytes_received']},{r['total_bytes']},{r['avg_bytes_per_msg']}")

if __name__ == '__main__':
    run_benchmark()
