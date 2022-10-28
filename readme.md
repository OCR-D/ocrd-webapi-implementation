OCR-D webAPI implementation
===========================

Implementation of [OCR-D](https://ocr-d.de/en/) [webAPI](https://github.com/OCR-D/spec/blob/master/openapi.yml)

TODO: ToC


Run project
-----------
## Docker
### clone
`git clone https://github.com/OCR-D/ocrd-webapi-implementation.git`
`cd ocrd-webapi-implementation`

### install nextflow
- necessarry if workflows should be run
- https://www.nextflow.io/docs/latest/getstarted.html

### start docker
- carefully: downloads ocrd-all:maximum which is huge (17 GB currently)
- TODO: maybe switch image to minimum or medium and just offer contained processors
```
docker-compose --env-file things/env-template-docker up -d
```

### test if running:
- `curl localhost:5050`
- `curl localhost:5050/workspaces`

## Locally for development
- TODO: this is not working. Especially setting the environment variables must be thougth about
### clone
`git clone https://github.com/OCR-D/ocrd-webapi-implementation.git`
`cd ocrd-webapi-implementation`

### Create virtual environment and start it
`make venv`
`. venv/bin/activate`
- TODO: this does not work if python3.7 is not present as on my own machine. How to get a python
  3.7 on any linux distro?

### start mongodb
- `make start-mongo`

### run
`uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload`



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


Explanation env-variables:
--------------------------
### OCRD_WEBAPI_SERVER_PATH
When users query a workspace, they get a url where to retreive it. Only therefore this variable is
needed. It does not cause errors, if wrong "just" users cannot retreive their data and have to
modify themselfs

### OCRD_WEBAPI_PORT
Only docker. This is the port where the webapi will be available on localhost

### OCRD_WEBAPI_MONGO_PORT
Only docker. This is the port where the mongodb will be available on localhost. When developing
locally or running tests, this must fit to OCRD_WEBAPI_DB_URL

### OCRD_WEBAPI_DATADIR_HOST
Only docker. This is the host-part of two volume-mounts. Here the data from mongdb and the data
from the webapi are mounted. If running in development mode here the mongdb-stuff is accessible.

### OCRD_WEBAPI_DB_URL
Important: This is the url where the webapi expects the mongdb to run

### OCRD_WEBAPI_STORAGE_DIR
Important: Here the webapi stores its workspaces etc. Additionally this is used in docker-compose.
This is the container-part of a volume mount so that from the host-machine it is possible to access
the data stored with the webapi
