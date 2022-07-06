OCR-D webAPI implementation
===========================

Implementation of [OCR-D](https://ocr-d.de/en/) [webAPI](https://github.com/OCR-D/spec/blob/master/openapi.yml)

TODO: ToC


Run project
-----------
### clone
`git clone https://github.com/joschrew/ocrd-webapi-implementation.git`

### build
`cd ocrd-webapi-implementation`
`docker build -t ocrd-webapi .`

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



Links
------
<https://github.com/OCR-D/spec/blob/master/openapi.yml>
<https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1>


Dev-Server:
-----------
### Start Dev-Server
`uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload`

### Example Requests with Curl:


Miscellaneous
----------------

### connect to running container:
`docker exec -it ocrd-webapi bash`

