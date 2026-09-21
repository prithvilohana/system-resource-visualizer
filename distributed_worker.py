import argparse
import json
import math
import socketserver
import threading


def is_prime(number):
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False

    limit = int(math.sqrt(number)) + 1
    for divisor in range(3, limit, 2):
        if number % divisor == 0:
            return False
    return True


def count_primes_range(start, end):
    return sum(1 for number in range(start, end) if is_prime(number))


class WorkerRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request_line = self.rfile.readline()
        if not request_line:
            return

        try:
            request = json.loads(request_line.decode("utf-8"))
            command = request.get("command")

            if command == "hello":
                response = {
                    "ok": True,
                    "name": self.server.worker_name,
                    "logical_cpus": self.server.logical_cpus,
                }
            elif command == "prime_range":
                start = int(request["start"])
                end = int(request["end"])
                if start < 2 or end <= start:
                    raise ValueError("Invalid prime range")
                response = {
                    "ok": True,
                    "count": count_primes_range(start, end),
                }
            else:
                raise ValueError(f"Unknown command: {command}")
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}

        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))
        self.wfile.flush()


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="PDC distributed benchmark worker")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--name", default=socketserver.socket.gethostname())
    args = parser.parse_args()

    with ReusableThreadingTCPServer((args.host, args.port), WorkerRequestHandler) as server:
        server.worker_name = args.name
        server.logical_cpus = __import__("os").cpu_count() or 1
        print(f"Worker '{args.name}' listening on {args.host}:{args.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Worker stopped.", flush=True)


if __name__ == "__main__":
    main()
