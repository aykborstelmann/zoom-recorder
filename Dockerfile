FROM selenium/node-firefox
RUN sudo apt update && sudo apt install ffmpeg python3 python3-pip pulseaudio socat alsa-utils -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN sudo mkdir -p /opt/project && sudo chown -R seluser:seluser /opt/project/
VOLUME /opt/project
CMD cd /opt/project && python3 main.py