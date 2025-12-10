# Work Endpoint API

## Work Endpoint Description

##### NOTE

```
All documentation for Portfolios REST APIs is available in Swagger. For the optimal experience with theREST API
documentation, Planview recommends accessing the Swagger page for your Portfolios environment. For more
information on how to access the Portfolios REST API documentation in Swagger, see theUsing Swagger for API
Documentation and Testing.
```
The Work endpoint supports REST APIs related towork items for Planview Portfolios. Work items are planning entities,

including projects and tasks located below theprimary planning level (PPL). For details aboutthe differences between

projects and work as theyrelateto the Planview Portfolios and these API endpoints, seeProjects and Work.

## Notes on API Behavior

- Work REST APIs support interaction with attributes available as returned in theGET /work/attributes/availableAPI,
    which returns a list of all available attributes along with metadata information on format, edibility, and more related
    to this endpoint.
- The read work API for a single work ID(GET /work/{id}) returns a standard set of attributes available for the
    specified work as well as any additional attributes included as a string in API request.
- Filter parameters for these REST APIs are structured in a query string within the API call. The following sections
    includeexamplesfor the supported filter parameters.
- Attributeand parameter values are case-sensitive.
- The REST APIs are currently designed for transactional system-to-system integrations (in other words, one at a
    time). The APIs do not accept batch requests where multiple requests are sent in an array. If you send a batch
    request,the API accepts only oneto write to thePlanview Portfolios database.

## GET /public-api/v1/work/attributes/available

Get a list of all available attributes ( **publicApiV1WorkAttributesAvailableGet** ).

## Return Type

AttributeDtoPublicResponseEnvelopeModel

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Example Data

**Content-Type** : application/json

##### {

```
"data": [
{
"id": "string",
"title": "string",
"helpText": "string",
"editFeature": "string",
"viewFeature": "string",
"type": "Void",
"defaultValue": "string",
"isSystemControlled": true,
"primaryPlanningLevelOnly": true,
"maxLength": 0
}
]
}
```
### Produces

This API call produces the following media types according to the Accept request header; the media type will be

conveyed by the Content-Type response header:

- application/json

### Responses

(^200) Success
**401** Unauthorized
**403** Forbidden
**404** Not Found

## GET /public-api/v1/work

Get all work based on a filter. (e.g. all work for a single project) ( **publicApiV1WorkGet** ).

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Query Parameters

```
Parameter Description
Required or
Optional
```
#### filter A filter parameter, such asproject.Id .eq 1906 Required

```
attributes An array of attributes to return values for. If not specified, the core set of attributes
will be returned.
```
```
Optional
```
### Return Type

WorkDtoPublicResponseEnvelopeModel

### Example Data

**Content-Type** : application/json

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

##### {

```
"data": [
{
"structureCode": "string",
"scheduleStart": "2022-12-05T22:55:47.087Z",
"scheduleFinish": "2022-12-05T22:55:47.087Z",
"scheduleDuration": 0,
"actualStart": "2022-12-05T22:55:47.087Z",
"actualFinish": "2022-12-05T22:55:47.087Z",
"calendar": {
"structureCode": "string",
"description": "string"
},
"status": {
"structureCode": "string",
"description": "string"
},
"isMilestone": true,
"project": {
"structureCode": "string",
"description": "string"
},
"place": 0,
"parent": {
"structureCode": "string",
"description": "string"
},
"description": "string",
"hasChildren": true,
"depth": 0,
"constraintDate": "2022-12-05T22:55:47.087Z",
"constraintType": "ASAP",
"progressAsPlanned": true,
"enterStatus": true,
"ticketable": true,
"doNotProgress": true,
"attributes": {
"additionalProp1": "string",
"additionalProp2": "string",
"additionalProp3": "string"
}
}
]
}
```
### Produces

This API call produces the following media types according to the Accept request header; the media type will be

conveyed by the Content-Type response header:

- application/json

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Responses

(^200) Success
**400** Bad Request
**401** Unauthorized
**403** Forbidden
**404** Not Found

## GET /public-api/v1/work/{id}

Get a single item of **work (publicApiV1WorkIdGet).**

### Path Parameters

```
Parameter Description Required or Optional
```
```
id The structure code. Required
```
### Query Parameters

```
Parameter Description
Required or
Optional
```
```
attributes An array of attributes to return values for. If not specified, the core set of attributes
will be returned.
```
```
Optional
```
### Return Type

WorkDtoPublicResponseEnvelopeModel

### Example Data

**Content-Type** : application/json

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

##### {

```
"data": [
{
"structureCode": "string",
"scheduleStart": "2022-12-05T22:56:25.723Z",
"scheduleFinish": "2022-12-05T22:56:25.723Z",
"scheduleDuration": 0,
"actualStart": "2022-12-05T22:56:25.723Z",
"actualFinish": "2022-12-05T22:56:25.723Z",
"calendar": {
"structureCode": "string",
"description": "string"
},
"status": {
"structureCode": "string",
"description": "string"
},
"isMilestone": true,
"project": {
"structureCode": "string",
"description": "string"
},
"place": 0,
"parent": {
"structureCode": "string",
"description": "string"
},
"description": "string",
"hasChildren": true,
"depth": 0,
"constraintDate": "2022-12-05T22:56:25.723Z",
"constraintType": "ASAP",
"progressAsPlanned": true,
"enterStatus": true,
"ticketable": true,
"doNotProgress": true,
"attributes": {
"additionalProp1": "string",
"additionalProp2": "string",
"additionalProp3": "string"
}
}
]
}
```
### Produces

This API call produces the following media types according to the Accept request header; the media type will be

conveyed by the Content-Type response header:

- application/json

```
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Responses

(^200) Success
**401** Unauthorized
**403** Forbidden
**404** Not Found
Work Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved


