FROM nikolaik/python-nodejs
ENV PYTHONUNBUFFERED=1
#ENV NODE_OPTIONS="--unhandled-rejections=strict --trace-warnings"
#ENV DEBUG="jspybridge"
WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y xserver-xorg-dev libxi-dev xserver-xorg-dev libxext-dev xvfb

COPY requirements.txt requirements.txt
COPY requirements.py requirements.py
RUN pip3 install -r requirements.txt
RUN npm install --save mineflayer-pathfinder
RUN python3 -m javascript --install PrismarineJS/node-canvas-webgl
RUN python3 requirements.py

COPY . .

EXPOSE 7000-7199

CMD xvfb-run --auto-servernum --server-num=1 --server-args='-ac -screen 0 1280x1024x24' stdbuf -oL -eL python3 -u ClientsManager.py >/dev/stdout 2>&1
