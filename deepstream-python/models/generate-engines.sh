#!/bin/bash
set -e

# Trackers
BUILD_REID=1

# Detectors
BUILD_TRAFFICCAMNET=1
BUILD_PEOPLENET=1

# TRACKERS

## ReID Model Batch 4
if [[ $BUILD_REID == 1 ]]; then
  MODEL_FILE="./pre-trained/nvidia/ReID/resnet50_market1501.onnx"
  ENGINE_FILE="./trt/resnet50_market1501.onnx_b4_gpu0_fp16.engine"

  if [[ ! -f ${ENGINE_FILE} ]]; then
    echo "[INFO] Building INT8 TensorRT engine from: $MODEL_FILE"
    mkdir -p $(dirname "$ENGINE_FILE")

    /usr/src/tensorrt/bin/trtexec \
      --onnx="$MODEL_FILE" \
      --saveEngine="$ENGINE_FILE" \
      --memPoolSize=workspace:8G \
      --minShapes='input':1x3x256x128 \
      --optShapes='input':4x3x256x128 \
      --maxShapes='input':4x3x256x128 \
      --noTF32 \
      --fp16 \
      --builderOptimizationLevel=5 \
      --skipInference

    echo "[INFO] Engine saved to: $ENGINE_FILE"
  else
    echo "[INFO] $(basename $ENGINE_FILE) already built"
  fi
  echo "[INFO] Skipping $(basename $ENGINE_FILE) build"
fi

# DETECTORS

## TrafficCamNet
if [[ $BUILD_TRAFFICCAMNET == 1 ]]; then
  MODEL_FILE="./pre-trained/nvidia/TrafficCamNet/resnet18_trafficcamnet_pruned.onnx"
  INT8CALIB_FILE="./pre-trained/nvidia/TrafficCamNet/resnet18_trafficcamnet_pruned_int8.txt"
  ENGINE_FILE="./trt/resnet18_trafficcamnet_pruned.onnx_b1_gpu0.engine"

  if [[ ! -f ${ENGINE_FILE} ]]; then
    echo "[INFO] Building INT8 TensorRT engine from: $MODEL_FILE"
    mkdir -p $(dirname "$ENGINE_FILE")

    /usr/src/tensorrt/bin/trtexec \
      --onnx="$MODEL_FILE" \
      --saveEngine="$ENGINE_FILE" \
      --memPoolSize=workspace:8G \
      --minShapes='input_1:0':1x3x544x960 \
      --optShapes='input_1:0':1x3x544x960 \
      --maxShapes='input_1:0':1x3x544x960 \
      --noTF32 \
      --fp16 \
      --int8 \
      --calib="$INT8CALIB_FILE" \
      --builderOptimizationLevel=5 \
      --skipInference

    echo "[INFO] Engine saved to: $ENGINE_FILE"
  else
    echo "[INFO] $(basename $ENGINE_FILE) already built"
  fi
  echo "[INFO] Skipping $(basename $ENGINE_FILE) build"
fi

## PeopleNet Batch 1
if [[ $BUILD_PEOPLENET == 1 ]]; then
  MODEL_FILE="./pre-trained/nvidia/PeopleNet/resnet34_peoplenet.onnx"
  INT8CALIB_FILE="./pre-trained/nvidia/PeopleNet/resnet34_peoplenet_int8.txt"
  ENGINE_FILE="./trt/resnet34_peoplenet.onnx_b1_gpu0.engine"

  if [[ ! -f ${ENGINE_FILE} ]]; then
    echo "[INFO] Building INT8 TensorRT engine from: $MODEL_FILE"
    mkdir -p $(dirname "$ENGINE_FILE")

    /usr/src/tensorrt/bin/trtexec \
      --onnx="$MODEL_FILE" \
      --saveEngine="$ENGINE_FILE" \
      --memPoolSize=workspace:8G \
      --minShapes='input_1:0':1x3x544x960 \
      --optShapes='input_1:0':1x3x544x960 \
      --maxShapes='input_1:0':1x3x544x960 \
      --noTF32 \
      --fp16 \
      --int8 \
      --calib="$INT8CALIB_FILE" \
      --builderOptimizationLevel=5 \
      --skipInference

    echo "[INFO] Engine saved to: $ENGINE_FILE"
  else
    echo "[INFO] $(basename $ENGINE_FILE) already built"
  fi
  echo "[INFO] Skipping $(basename $ENGINE_FILE) build"
fi

