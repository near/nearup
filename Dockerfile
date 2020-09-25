from ubuntu:18.04

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PATH="/root/.local/bin:$PATH"
ENV HOME="/root"

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --upgrade pip

COPY . /root/nearup/
RUN cd /root/nearup && pip3 install --user .

COPY ./start.sh /root/start.sh
RUN chmod +x /root/start.sh

ENTRYPOINT ["/root/start.sh"]
