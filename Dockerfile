FROM ocrd/all:maximum

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt \ 
    # install nextflow and java
	&& apt-get update \
    && apt-get install default-jdk -y \
    && curl -s https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/ \
    # do recommended? cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY ./ocrd_webapi /code/ocrd_webapi

CMD ["uvicorn", "ocrd_webapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
