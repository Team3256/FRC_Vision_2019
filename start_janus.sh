./janus -F /opt/janus/etc/janus/
#gst-launch-1.0 v4l2src device=/dev/video1 ! video/x-raw,width=1920,height=1080,framerate=30/1 ! omxh264enc bitrate=80000 ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=8004
gst-launch-1.0 v4l2src device=/dev/video1 ! video/x-raw,width=1280,height=720,framerate=30/1 ! omxh264enc bitrate=1000000 ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=5004
