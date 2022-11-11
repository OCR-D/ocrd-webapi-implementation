FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY . /code

RUN apt-get update
RUN apt-get -y install \
    ca-certificates \
    software-properties-common \
    python3-dev \
    python3-pip \
    make \
    wget \
    time \
    curl \
    sudo \
    git \ 
    default-jdk \
    && curl -s https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/
    
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools 
RUN python3 -m pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip3 install .

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["uvicorn", "ocrd_webapi.main:app", "--host", "0.0.0.0", "--port", "8000"]

