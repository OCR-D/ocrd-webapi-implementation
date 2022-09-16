OCR-D webAPI implementation
===========================

Implementation of [OCR-D](https://ocr-d.de/en/) [webAPI](https://github.com/OCR-D/spec/blob/master/openapi.yml)

TODO: ToC


Run project
-----------
## Local
### clone
`git clone https://github.com/joschrew/ocrd-webapi-implementation.git`

### Create virtual environment
`make venv`

### start venv and install requirements:
`. venv/bin/activate`

`make requirements`

### run
`uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload`

## Docker
### clone
`git clone https://github.com/joschrew/ocrd-webapi-implementation.git`

### build
```
cd ocrd-webapi-implementation
docker build -t ocrd-webapi .
```

### run
`docker run -p "8000:80" --name ocrd-webapi -d ocrd-webapi`

Test this webAPI implementation
-------------------------------
### test if running
http://localhost:8000/

### postman
import file `webapi-tests.postman_collection.json` into postman to run example requests on running
Docker service. Test-Workspace-Zips are in `things/`

### curl
Get workspace list:
`curl http://localhost:8000/workspace`

Create new workspace:
`curl -X POST http://localhost:8000/workspace -F workspace=@tests/assets/example_ws.ocrd.zip`

Create new workspace with id:
`curl -X PUT 'http://localhost:8000/workspace/test4711' -F 'workspace=@tests/assets/example_ws.ocrd.zip'`

Update existing workspace:
`curl -X PUT 'http://localhost:8000/workspace/test4711' -F 'workspace=@tests/assets/example_ws2.ocrd.zip'`

Get single workspace:
`curl http://localhost:8000/workspace/test4711`

Upload workflow:
`curl -X POST http://localhost:8000/workflow --user {user}:{pw} -F nextflow_script=@things/nextflow.nf`

Run Workflow:
`curl -X POST http://localhost:8000/workflow/{workflow-id} -H 'Content-Type: application/json' -d '{"workspace_id":"{workspace-id}", "workflow_parameters": {}}'`

Request job status:
`curl http://localhost:8000/workflow/{workflow-id}/{job-id}`

Download Workspace ocrd.zip:
`curl http://localhost:8000/workspace/{workspace-id} -H "accept: application/vnd.ocrd+zip" --output foo.zip`

Links
------
<https://github.com/OCR-D/spec/blob/master/openapi.yml>
<https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1>


Dev-Server:
-----------
### start venv:
`. venv/bin/activate`

### Start Dev-Server
`uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload`


Run Server using docker-compose:
--------------------------------
`cp things/env-template .env`
# modiyfiy .env
`docker-compose build --no-cache`
`docker-compose up -d`



Miscellaneous
----------------

### connect to running container:
`docker exec -it ocrd-webapi bash`

### start mongodb for local testing
docker run -d -p 27017:27017 --name mongo-4-ocrd --mount type=bind,source="$HOME/zeugs-ohne-backup/ocrd_webapi/mongo-data",target=/data/db  mongo:latest
