from ubuntu:18.04

RUN apt-get update && apt-get install -y python3 python3-pip && pip3 install --upgrade pip && pip3 install --user nearup==0.4.2

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8     
ENV PATH="/root/.local/bin:$PATH"
COPY ./start.sh /root/start.sh
RUN chmod +x /root/start.sh

ENTRYPOINT ["/root/start.sh"]
