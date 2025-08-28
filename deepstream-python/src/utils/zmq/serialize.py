import zmq
import numpy as np

class SerializingSocket(zmq.Socket):
  def send_array(self, A, msg='NoName', flags=0, copy=True, track=False):
    md = dict(
      msg=msg,
      dtype=str(A.dtype),
      shape=A.shape,
    )
    # Send topic string first
    self.send_string(msg, flags | zmq.SNDMORE)
    # Then metadata JSON
    self.send_json(md, flags | zmq.SNDMORE)
    # Then raw bytes
    return self.send(A, flags, copy=copy, track=track)

  def recv_array(self, flags=0, copy=True, track=False):
    # Receive topic string first
    topic = self.recv_string(flags=flags)
    # Then metadata JSON
    md = self.recv_json(flags=flags)
    # Then raw frame bytes
    msg = self.recv(flags=flags, copy=copy, track=track)
    A = np.frombuffer(msg, dtype=md['dtype'])
    return (topic, A.reshape(md['shape']))

class SerializingContext(zmq.Context):
  _socket_class = SerializingSocket
