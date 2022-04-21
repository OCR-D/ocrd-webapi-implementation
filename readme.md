### What is this repo about?
This is a first attempt to implement (some of) this api-calls with fastapi:
<https://github.com/OCR-D/spec/blob/master/openapi.yml>
<https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1>

### Templates for api-calls
generated with <https://github.com/koxudaxi/fastapi-code-generator>
`things/webapi_template_main.py` and `things/webapi_template_models.py`


### Start Dev-Server
`uvicorn ocrd-webapi-test.main:app --host 0.0.0.0 --reload`

### Example Requests with Curl:
Post/Upload Workspace:
`curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F
 file=@things/example_ws.ocrd.zip`

Post/Start Processor:
`curl -X POST http://localhost:8000/processor/ocrd-tesserocr-segment-region -H 'content-type: application/json' -d '@things/processor-request-example.json'`
