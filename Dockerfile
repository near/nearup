from ubuntu:18.04

COPY ./nearuplib/VERSION /root/VERSION
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --upgrade pip && \
    pip3 install --user tox && \
    pip3 install --user nearup==$(echo -n $(cat /root/VERSION))

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PATH="/root/.local/bin:$PATH"
ENV HOME="/root"
COPY ./start.sh /root/start.sh
RUN chmod +x /root/start.sh

ENTRYPOINT ["/root/start.sh"]
