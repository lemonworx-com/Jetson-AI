## Build

### Compile model engines

```sh
cd models
./generate-engines.sh
```

### Build Container

```sh
docker build -t lmx-jetson-ai .
```

## Run

```sh
export DISPLAY=:0
xhost +
docker run -it --rm --network=host --runtime nvidia -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --privileged lmx-jetson-ai
```


## Apps

### Deestream Test 1

```sh
python3 dstest_1_simplified.py /app/streams/sample_qHD.h264
```