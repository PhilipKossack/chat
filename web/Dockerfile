FROM python:3.10-slim-bullseye

WORKDIR /app
ADD . /app

RUN apt-get update \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        git \
        locales \
        sudo \
        build-essential \
        dpkg-dev \
        wget \
        openssh-server \
        nano \
    && rm -rf /var/lib/apt/lists/*
#RUN git clone https://github.com/ggerganov/llama.cpp
#WORKDIR /app/llama.cpp
#RUN make
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

CMD ["/bin/bash"]