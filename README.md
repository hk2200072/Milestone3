# E2E Crypto System

This project integrates symmetric (Simon/Speck) and asymmetric (ElGamal) cryptography into an end-to-end encrypted Client–Server system with a simulated Certificate Authority (CA), certificate issuance/verification, secure handshake, authenticated messaging, and optional key rotation. No external libraries are used (only Python standard library).

## Quick start

- Single-transaction demo and chat demo:

```
python demo.py
```

- Performance benchmark (computational time + communication bytes):

```
python benchmark.py
```

## What it does

- Simulated CA issues an ElGamal certificate to the Server.
- Client verifies the Server certificate (signature + expiry), negotiates cipher suite (SIMON, SPECK, or DOUBLE), and encapsulates a fresh session key and IV via ElGamal.
- Secure channel uses CTR mode with a custom MAC (no hashlib/hmac) over ciphertext for integrity.
- Messaging mode: client sends multiple messages; server replies to each. Client can trigger key rotation after N messages.

## How to use messaging (chat)

- See `client.run_chat` used in `demo.py`.
  - `messages`: list of plaintext strings to send.
  - `prefer`: 'SIMON', 'SPECK', or 'DOUBLE'.
  - `rekey_every`: send a Rekey after every N messages (set 0 to disable).

Interactive two-terminal examples:

- Server: `python cli_server.py 5001`
- Client (SIMON): `python cli_client.py 127.0.0.1 5001 SIMON`
- Client (SPECK): `python cli_client.py 127.0.0.1 5001 SPECK`
- Client (DOUBLE): `python cli_client.py 127.0.0.1 5001 DOUBLE`

## Benchmarking

- `benchmark.py` sends N messages of given size and prints:
  - `messages`, `msg_size`, `suite`, `rekey_every`
  - `time_sec`, `throughput_msgs_per_sec`
  - `bytes_sent`, `bytes_received`, `total_bytes`, `avg_bytes_per_msg`

## Project structure

- `crypto/simon.py`, `crypto/speck.py`: Simon-128/128 and Speck-128/128 + CTR wrappers
- `crypto/elgamal.py`: ElGamal (RFC3526 Group 14) + signing for CA
- `crypto/mode.py`: custom MAC (no hashlib/hmac) and simple KDF
- `pki/ca.py`, `pki/cert.py`: Simulated CA and JSON certificate format
- `net/protocol.py`: Handshake, secure channel, Rekey, metrics-enabled I/O
- `net/metrics.py`: byte counters (sent/received)
- `server.py`, `client.py`: roles and messaging loops
- `demo.py`, `benchmark.py`: runnable examples

## Security notes

- Each session gets fresh `K` and `IV` (from `secrets`).
- Integrity via a custom MAC over ciphertext (built on the internal hash; no hashlib/hmac).
- Certificates signed by CA (ElGamal signature). Client validates expiry and signature.
- No external dependencies.

## Key rotation

- Client may call `client_rekey` (automated via `rekey_every` in `run_chat`).
- Rekey encapsulates a new `K||IV` to the server using ElGamal; both sides derive fresh keys and reset counters.

