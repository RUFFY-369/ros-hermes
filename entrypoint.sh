#!/bin/bash
set -e

# Headless rendering support
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1

# Source ROS 2 setup
source "/opt/ros/humble/setup.bash"

# If a local workspace exists, source it
if [ -f "/ros_ws/install/setup.bash" ]; then
    source "/ros_ws/install/setup.bash"
fi

exec "$@"
