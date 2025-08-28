import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst

import configparser

def create_element(factory_name: str, name: str =None):
  element = Gst.ElementFactory.make(factory_name, name)
  if not element:
    raise RuntimeError(f"Could not create element '{factory_name}'")
  return element

def on_pad_added(src, new_pad, depay):
  print(f"[DEBUG] Pad added: {new_pad.get_name()}")
  sink_pad = depay.get_static_pad("sink")
  if sink_pad.is_linked():
    print("[DEBUG] Already linked. Skipping.")
    return
  result = new_pad.link(sink_pad)
  if result != Gst.PadLinkReturn.OK:
    print(f"[ERROR] Failed to link pad: {result}")
  else:
    print("[DEBUG] Pad linked successfully")
    
def configure_tracker(tracker, config_path):
  config = configparser.ConfigParser()
  config.read(config_path)
  for key, value in config["tracker"].items():
    if key in ["tracker-width", "tracker-height", "gpu-id"]:
      tracker.set_property(key.replace('-', '_'), int(value))
    else:
      tracker.set_property(key.replace('-', '_'), value)
      
def link_many(*elements):
  for i in range(len(elements) - 1):
    if not elements[i].link(elements[i+1]):
      raise RuntimeError(f"Failed to link {elements[i].name} to {elements[i+1].name}")
