import zmq
import numpy as np
from .serialize import SerializingContext


class StreamServer:
  def __init__(self, host="0.0.0.0", zmq_port=5555):
    self.context = SerializingContext()
    self.socket = self.context.socket(zmq.PUB)

    # limit publisher buffer size
    self.socket.setsockopt(zmq.SNDHWM, 2)

    self.host = host
    self.zmq_port = zmq_port
    self.socket.bind('tcp://{}:{}'.format(self.host, self.zmq_port))

  def send(self, frame, idx="frame"):
    try:
      md = dict(
        msg=idx,
        dtype=str(frame.dtype),
        shape=frame.shape
      )
      self.socket.send_string(idx, zmq.SNDMORE)          # Send topic first
      self.socket.send_json(md, zmq.SNDMORE)             # Then metadata
      self.socket.send(frame, copy=False)                # Then raw frame bytes
      #print(f"[DEBUG] sent frame with shape {frame.shape}")
      
    except Exception as e:
      print(f"[ERROR] Server :{e} ") 