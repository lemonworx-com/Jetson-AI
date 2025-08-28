import time
import threading

def heartbeat(path="/tmp/healthcheck", interval=10):
  def write_heartbeat():
    while True:
      with open(path, "w") as f:
        f.write("alive")
      time.sleep(interval)
  thread = threading.Thread(target=write_heartbeat, daemon=True)
  thread.start()