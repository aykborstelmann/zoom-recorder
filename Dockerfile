FROM selenium/node-firefox
RUN sudo apt update && sudo apt install ffmpeg python3 python3-pip pulseaudio -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN sudo mkdir -p /home/app
CMD cd /home/app && python3 main.py