- `200` Success
- `401` No `version` Tag Found From Request
- `403` urllib Got Error
- `404` URL Request Not Found
- `404` Empty Response

To shutdown PBP Server, type:
> curl -d '{"version":1,"shutdown":1}' http://localhost:2020

The halt command will be removed in production.