import sys

import pyds
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
import contextlib

import cv2
import numpy as np

from datetime import datetime

from utils.colors import *
from utils import timestamp
from utils.zmq.stream_server import StreamServer

from retail_analytics import region, tripwire, heatmap
from database import mongo

from inferencing.pyds.common.platform_info import PlatformInfo
from inferencing.pyds.common.FPS import PERF_DATA


class BaseProbe:
  def __init__(
    self,
    measure_latency : bool =False,
    measure_fps : bool =False
  ):  
    self.measure_latency = measure_latency
    self.measure_fps = measure_fps
    
    self.platform_info = PlatformInfo()

    # Init variables to None
    self.pad = None
    self.info = None
    self.u_data = None

    self.frame_number = 0

    self.gst_buffer = None
    self.hashed_gst_buffer = None

    self.batch_meta = None
    self.display_meta = None
    self.latency_meta = None
    
    self.perf_data = None
    
    if self.measure_fps:
      self.perf_data = PERF_DATA(1)
      
    self.__warmup_opencv()
      
  def __warmup_opencv():
    dummy = np.zeros((1080, 1920, 3), dtype=np.uint8)
    _ = cv2.cvtColor(dummy, cv2.COLOR_BGR2RGBA)
    _ = cv2.GaussianBlur(dummy, (15, 15), 0)
    _ = cv2.putText(dummy, "WARMUP", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    _ = cv2.rotate(dummy, cv2.ROTATE_90_CLOCKWISE)
    
  def __call__(self, pad, info, u_data):
    """
    Act as a decorator to verify GstBuffer,
    iterate on frame_meta, and handle Gst.PadProbeReturn
    """
    self.pad = pad
    self.info = info
    self.u_data = u_data

    self._set_gst_buffer()
    if not self.gst_buffer:
      return Gst.PadProbeReturn.OK

    self.batch_meta = self._get_batch_meta()
    if not self.batch_meta:
      return Gst.PadProbeReturn.OK
    
    l_frame = self.batch_meta.frame_meta_list
    while l_frame is not None:
      try:
        self.frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
      except StopIteration:
        break

      self.display_meta = self._get_display_meta()
      if not self.display_meta:
        return Gst.PadProbeReturn.OK

      self.frame_number = self._get_frame_number()
      
      # get latency info
      if self.measure_latency:
        self.latency_meta = pyds.nvds_measure_buffer_latency(self.hashed_gst_buffer)
        
      # get fps info 
      if self.measure_fps:
        stream_index = "stream{0}".format(self.frame_meta.pad_index)
        self.perf_data.update_fps(stream_index)

      obj_parameters = []
      # parse all detected objects
      l_obj = self.frame_meta.obj_meta_list
      while l_obj is not None:
        try:
          obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
          bbox_info = [obj_meta, *self._get_bbox_info(obj_meta)]
          obj_parameters.append(bbox_info)
          
          l_obj = l_obj.next
        except StopIteration:
          break

      # user defined callback for processing metadata
      cb_return = self.__callback__(obj_parameters)
      
      try:
        l_frame = l_frame.next
      except StopIteration:
        break
    
    return cb_return or Gst.PadProbeReturn.OK

  def _set_gst_buffer(self):
    self.gst_buffer = self.info.get_buffer()
    self.hashed_gst_buffer = hash(self.gst_buffer)

  def _get_batch_meta(self):
    """
    Retrieve batch metadata from the gst_buffer
    Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    """
    return pyds.gst_buffer_get_nvds_batch_meta(self.hashed_gst_buffer)
  
  def _get_display_meta(self):
    """
    Retrieve display metadata from the gst_buffer
    """
    if self.batch_meta is not None:
      return pyds.nvds_acquire_display_meta_from_pool(self.batch_meta)
    return None

  def _get_frame_number(self):
    return self.frame_meta.frame_num

  def _get_bbox_info(self, obj_meta):
    rect_params = obj_meta.rect_params
    x0 = int(rect_params.left)
    y0 = int(rect_params.top)
    x1 = int(rect_params.left) + int(rect_params.width)
    y1 = int(rect_params.top) + int(rect_params.height)
    return (obj_meta.class_id, obj_meta.object_id, [x0,y0,x1,y1])

class PeopleNetPersonDetector(BaseProbe):
  def __init__(
    self,
    measure_latency : bool =False,
    measure_fps : bool =False,
    floorplan_heatmap : heatmap.FloorplanHeatmap =None,
    camera_heatmap : heatmap.CameraHeatmap =None,
    region_monitor : region.RegionMonitor = None,
    tripwire_monitor : tripwire.TripwireMonitor =None,
    tripwire_db : mongo.TripWireDataBase =None,
    TZ_LOCALE : datetime.tzinfo =None,
    stream_server : StreamServer =None,
    overlay_blur : bool =False,
    overlay_tripwires : bool =False,
    overlay_camera_heatmap : bool =False,
    
  ):
    super().__init__(
      measure_latency=measure_latency,
      measure_fps=measure_fps
    )
    
    self.num_persons = 0
    
    self.floorplan_heatmap = floorplan_heatmap
    self.camera_heatmap = camera_heatmap
    self.region_monitor = region_monitor
    self.tripwire_monitor = tripwire_monitor
    self.tripwire_db = tripwire_db
    
    self.TZ_LOCALE = TZ_LOCALE
    
    self.stream_server = stream_server
    self.overlay_blur = overlay_blur
    self.overlay_tripwires = overlay_tripwires
    self.overlay_camera_heatmap = overlay_camera_heatmap

  def __callback__(self, obj_parameters):

    self.num_persons = self.frame_meta.num_obj_meta
    
    self.__display_text_overlay()
    
    obj_metas = []
    obj_ids = []
    boxes = []

    for obj_meta, obj_class, obj_id, bbox_coordinates in obj_parameters:
      
      obj_metas.append(obj_meta)
      obj_ids.append(obj_id)
      boxes.append(bbox_coordinates)
      
      # clear bbox labels
      text_params = obj_meta.text_params
      text_params.display_text = ""
        
    # grab a copy of the current frame
    if self.stream_server is not None:
      # grab a copy of the processed frame
      n_frame = pyds.get_nvds_buf_surface(self.hashed_gst_buffer, self.frame_meta.batch_id)
      # convert python array into numpy array format in the copy mode.
      frame_overlay = np.array(n_frame, copy=True, order='C')
      # convert the array into cv2 default color format
      frame_overlay = cv2.cvtColor(frame_overlay, cv2.COLOR_RGBA2BGR)
      if self.platform_info.is_integrated_gpu():
        # If Jetson, since the buffer is mapped to CPU for retrieval, it must also be unmapped 
        # The unmap call should be made after operations with the original array are complete.
        #  The original array cannot be accessed after this call.
        pyds.unmap_nvds_buf_surface(self.hashed_gst_buffer, self.frame_meta.batch_id)  
      
    # blur detected persons on the frame copy
    if self.stream_server is not None and self.overlay_blur:
      for box in boxes:
        x0, y0, x1, y1 = box
        roi = frame_overlay[y0:y1, x0:x1]
        roi = cv2.GaussianBlur(roi, (35,35), 0)
        frame_overlay[y0:y1, x0:x1] = roi
        
    # update heatmaps
    if self.floorplan_heatmap is not None and len(boxes) > 0:
      self.floorplan_heatmap.process_boxes(boxes)
    
    if self.camera_heatmap is not None and len(boxes) > 0:
      self.camera_heatmap.process_boxes(boxes)
        
    # update tripwire state from monitor
    if self.tripwire_monitor is not None and len(boxes) > 0:  
      tripped = self.tripwire_monitor.update(obj_ids, boxes)
      
      if len(tripped) > 0:
        print(tripped)
            
        if self.tripwire_db is not None:
          tripped_db_data = []
          ts = timestamp.generate_timestamp(self.TZ_LOCALE)
            
          for trip in tripped:
            object_class = 'person'
            object_id, tw_name, tw_direction = trip

            tripped_db_data.append([
              ts,
              object_class,
              object_id,
              tw_name,
              tw_direction
            ])

          self.tripwire_db.write_data(tripped_db_data)
    
    # update region state from monitor
    if self.region_monitor is not None and len(boxes) > 0:
      object_regions = self.region_monitor.update(obj_ids, boxes)
      if len(object_regions) > 0:
        for object_id, region in object_regions:
          
          obj_meta = obj_metas[obj_ids.index(object_id)]
          bbox_coordinates = boxes
          rect_params = obj_meta.rect_params
          
          if region == 'store':
            color = 'green'
          elif region == 'waiting_area':
            color = 'yellow'
          else:
            color = 'red'
            
          rect_params.bg_color.set(*NV_COLORS[color]) 
          rect_params.border_color.set(*NV_COLORS[color]) 
          
          # draw a bbox of the correct color on the overlay
          if self.stream_server is not None:
            x0, y0, x1, y1 = boxes[obj_ids.index(object_id)]
            frame_overlay = cv2.rectangle(frame_overlay, (x0, y0), (x1, y1), BGR_COLORS[color], 2) 
    
    # draw tripwires on overlay
    if self.stream_server is not None and self.overlay_tripwires:
      frame_overlay = self.tripwire_monitor.tripwires.draw_all(frame_overlay)
    
    # draw heatmap on overlay
    if self.stream_server is not None and self.overlay_camera_heatmap:
      colored_heatmap = self.camera_heatmap.get_low_res_heatmap()
      h, w, _ = colored_heatmap.shape
      frame_overlay = cv2.resize(frame_overlay, (w, h), interpolation=cv2.INTER_LINEAR)
      frame_overlay = cv2.addWeighted(frame_overlay, 0.35, colored_heatmap, 0.65, 0)
      
    # send frame to streaming server
    if self.stream_server is not None:
      self.stream_server.send(frame_overlay)
  
    return Gst.PadProbeReturn.OK
  
  def __display_text_overlay(self):
    # Display text overlay
    py_nvosd_text_params = self.display_meta.text_params[0]
    py_nvosd_text_params.display_text = "Frame Number={} Person_count={}".format(
      self.frame_number, self.num_persons
    )

    py_nvosd_text_params.x_offset = 10
    py_nvosd_text_params.y_offset = 12
    py_nvosd_text_params.font_params.font_name = "Serif"
    py_nvosd_text_params.font_params.font_size = 10
    py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
    py_nvosd_text_params.set_bg_clr = 1
    py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

    pyds.nvds_add_display_meta_to_frame(self.frame_meta, self.display_meta)
    
    #print frame info on stdout
    print(pyds.get_string(py_nvosd_text_params.display_text))