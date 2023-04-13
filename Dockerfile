FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /code
COPY . /code

RUN apt-get update && apt-get -y install \
    curl \
    default-jdk \
    make \
    python3-dev \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash nextflow

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools
RUN python3 -m pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip3 install .

USER nextflow
RUN cd $HOME \
    && curl -s https://get.nextflow.io | bash \
    && mkdir -p $HOME/.local/bin \
    && mv nextflow $HOME/.local/bin/

ENV PATH "${PATH}:/home/nextflow/.local/bin"

CMD ["uvicorn", "ocrd_webapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
