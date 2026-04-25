FROM ros:humble-ros-base

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install fastapi uvicorn httpx

# Set working directory
WORKDIR /app

# Copy bridge code
COPY bridge/ /app/bridge/

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8081

# Command to run
CMD ["python3", "bridge/api.py"]
