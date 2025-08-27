# !!!!!! NvBA
# Do not use the proper deepstream container as it does not have the 
# 10.3.0.30 version of TRT
# !!!!!! 
FROM ryagi17/deepstream-l4t:l4tr36.4.3-DS7.1.0

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ARG wdir=/app

# create workdir
RUN mkdir -p ${wdir}

# Install basic dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      apt-utils pkg-config git && \    
    apt-get install -y \ 
      wget gnupg curl unzip \
      libxml2 graphviz \
      libgtk2.0-dev libsm6 libxext6 libxcb-xinerama0 libxrender-dev \
      python3 python3-pip && \      
    apt-get clean

# Install Deepstream Dependencies
RUN cd /opt/nvidia/deepstream/deepstream/ && \
    ./user_additional_install.sh

# Install runtime dependencies
RUN apt-get install -y \
      gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly libgstrtspserver-1.0-0 gstreamer1.0-rtsp \
      libgirepository1.0-dev gobject-introspection gir1.2-gst-rtsp-server-1.0 \
      python3-pip python3-tk \
      kmod kbd && \
    apt-get clean

# Missing and broken video libraries 
RUN apt-get install --reinstall -y \
      ffmpeg libavcodec58 libmp3lame0 libxvidcore4 libflac8 && \
    apt-get clean


# Install python runtime dependencies
COPY lib ${wdir}/lib
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r ${wdir}/lib/requirements.txt     
RUN python3 -m pip install -r ${wdir}/lib/requirements-deepstream.txt         
   
# Remove pre-installed OpenCV wheels to avoid conflicts
RUN python3 -m pip uninstall -y opencv-python opencv-python-headless || true
# Force downgrade to V1.X numpy
RUN python3 -m pip install --force-reinstall numpy==1.26.4

# Install OpenCV from builder stage
COPY --from=ryagi17/opencv-l4t:l4t36.4.3-CV4.10.0  /opencv-install/ /usr/local/
# Copy cv2 binding from builder
COPY --from=ryagi17/opencv-l4t:l4t36.4.3-CV4.10.0  /opencv-install/lib/python3.10/dist-packages/cv2/python-3.10/cv2.cpython-310-aarch64-linux-gnu.so /usr/local/lib/python3.10/dist-packages/
RUN ldconfig
