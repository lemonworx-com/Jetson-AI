import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst

import configparser

class Deepstream:

  def init_pipeline(self):
    pipeline = Gst.Pipeline()
    if not pipeline:
      raise RuntimeError(f"Could not create pipeline")
    return pipeline

  def create_element(
    self,
    factory_name : str,
    name : str =None,
  ) -> Gst.Element:
    print(f"[DEBUG] Creating {factory_name} with name {name}")
    element = Gst.ElementFactory.make(factory_name, name)
    if not element:
      raise RuntimeError(f"Could not create element '{factory_name}'")
    return element

  def request_pad_simple(
    self,
    element : Gst.Element,
    pad_name : str,
  ):
    pad = element.request_pad_simple(pad_name)
    if not pad:
      raise RuntimeError(f"Could request pad {pad_name} from element '{element.get_name()}'")
    return pad

  def get_static_pad(
    self,
    element   : Gst.Element,
    pad_name  : str,
  ):
    pad = element.get_static_pad(pad_name)
    if not pad:
      raise RuntimeError(f"Could request pad {pad_name} from element '{element.get_name()}'")
    return pad

  def link_dynamic_elements(
    self,
    sourcing_element : Gst.Element,
    source_pad_name  : str,
    sinking_element  : Gst.Element, 
    sink_pad_name    : str,
  ):
    srcpad = self.get_static_pad(sourcing_element, source_pad_name)  
    sinkpad = self.request_pad_simple(sinking_element, sink_pad_name)
    srcpad.link(sinkpad)

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
      
  def configure_tracker(
    self,
    tracker     : Gst.Element,
    config_path : str
  ):
    config = configparser.ConfigParser()
    config.read(config_path)
    for key, value in config["tracker"].items():
      if key in ["tracker-width", "tracker-height", "gpu-id"]:
        tracker.set_property(key.replace('-', '_'), int(value))
      else:
        tracker.set_property(key.replace('-', '_'), value)
        
  def link_many(
    self,
    *elements : Gst.Element
  ):
    for i in range(len(elements) - 1):
      if not elements[i].link(elements[i+1]):
        raise RuntimeError(f"Failed to link {elements[i].name} to {elements[i+1].name}")
