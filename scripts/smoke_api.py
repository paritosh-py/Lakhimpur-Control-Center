"""Start a real local HTTP server, verify it, and always stop it."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Select an available loopback port; startup errors are surfaced explicitly.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError(process.stderr.read().decode())
            try:
                with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
                    health = json.load(response)
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("API failed to start within five seconds")
        with urlopen(f"http://127.0.0.1:{port}/api/config", timeout=2) as response:
            config = json.load(response)
        assert health["status"] == "ok"
        assert config["district"] == "Lakhimpur" and config["state"] == "Assam"
        print(json.dumps({"result": "PASS", "health": health, "district": config["district"],
                          "state": config["state"], "transport": "actual loopback HTTP"}, indent=2))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stderr.close()


if __name__ == "__main__":
    main()
