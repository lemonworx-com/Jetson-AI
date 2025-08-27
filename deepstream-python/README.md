## Build

```sh
docker build -t lmx-jetson-ai .
```

## Run

```sh
xhost +
docker run -it --rm --network=host --runtime nvidia -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --privileged lmx-jetson-ai
```