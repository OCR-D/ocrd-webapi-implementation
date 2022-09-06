FROM python:3.7

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ocrd_webapi /code/ocrd_webapi

CMD ["uvicorn", "ocrd_webapi.main:app", "--host", "0.0.0.0", "--port", "80"]
