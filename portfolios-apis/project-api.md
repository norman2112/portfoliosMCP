# Project Endpoint API

## Project Endpoint Description

##### NOTE

```
All documentation for Portfolios REST APIs is available in Swagger. For the optimal experience with theREST API
documentation, Planview recommends accessing the Swagger page for your Portfolios environment. For more
information on how to access the Portfolios REST API documentation in Swagger, see theUsing Swagger for API
Documentation and Testing.
```
The Project endpoint supports REST APIs related toprojects for the Planview Portfolios product. A project can be

defined as a planning entity (work) located at the Primary Planning Level (PPL) of the planning entity structure.

## Notes on API Behavior

- Project REST APIs support interaction with attributes available as returned in theGET /projects/attributes/available
    API,which will return a list of all available attributes along with metadata information on format, edibility, and more
    related to this endpoint.
- The read project API for a single project ID(GET /projects/{id}) returns a standard set of attributes available for the
    specified project as well as any additional attributes included as a string in the API request.
- Filter parameters for these REST APIs are structured in a query string within the API call. The following sections
    includeexamplesfor supported filter parameters.
- Attributeand parameter values are case-sensitive.
- The REST APIs are currently designed for transactional system-to-system integrations (in other words, one at a
    time). The APIs do not accept batch requests where multiple requests are sent in an array. If you send a batch
    request,the API accepts only oneto write to thePlanview Portfolios database.

## GET /public-api/v1/projects/attributes/available

Get a list of all available project attributes ( **publicApiV1ProjectsAttributesAvailableGet** ).

## Return Type

AttributeDtoPublicResponseEnvelopeModel

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Example Data

Content-Type: application/json

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

## GET /public-api/v1/projects/{id}

Get a single project ( **publicApiV1ProjectsIdGet** )

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Path Parameters

```
Parameter Description Required or Optional
```
```
id The project ID. Required
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

ProjectDtoPublicResponseEnvelopeModel

### Example Data

Content-Type: application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

##### {

```
"data": [
{
"shortName": "string",
"productInvestmentApproval": {
"structureCode": "string",
"description": "string"
},
"requestedStart": "2022-12-06T16:34:06.812Z",
"requestedFinish": "2022-12-06T16:34:06.812Z",
"createdOn": "2022-12-06T16:34:06.812Z",
"createdBy": {
"userName": "string",
"fullName": "string"
},
"lifecycleAdminUser": {
"userName": "string",
"fullName": "string"
},
"isLifecycleEnabled": true,
"hasLifecycle": true,
"structureCode": "string",
"scheduleStart": "2022-12-06T16:34:06.812Z",
"scheduleFinish": "2022-12-06T16:34:06.812Z",
"scheduleDuration": 0,
"actualStart": "2022-12-06T16:34:06.812Z",
"actualFinish": "2022-12-06T16:34:06.812Z",
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
"constraintDate": "2022-12-06T16:34:06.812Z",
"constraintType": "ASAP",
"progressAsPlanned": true,
"enterStatus": true,
"ticketable": true,
"doNotProgress": true,
```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved


```
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

conveyed by the Content-Type response header.

- application/json

### Responses

(^200) Success
**401** Unauthorized
**403** Forbidden
**404** Not Found

## POST /public-api/v1/projects

Create a project.( **publicApiV1ProjectsPost** )

### Notes for Creating a Project

- Requests must beproperly formatted JSON with the core fields, custom fields, attributes, and/or alternate
    structures (where a structure code is used to identify those alternate structure objects).For examples, see the
    Swagger page for the Project endpoint in your environment.
- Attributes for a newproject may not match the request because of values controlled by the product, default values,
    and other changes the product makes based on user input.
- If youusea custom value for a field in your request, the custom value overrides the default value, even if the value is
    null or blank. Otherwise, the API uses the default valuewhere possible, such as for fields thatPlanview Portfolios
    populates automatically whencreating a project.
- Duration is calculated automatically from the schedule start and schedule finish dates; anycustom valuefor
    Durationin your request is not used.
- You cannot set actual start, actual finish, and percent complete values with this API.
- Planview Portfolios business rules take precedence when processing requested values; therefore,values in the

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

```
response may differ from the request. For example, requested dates for schedule start and schedule finish will be
aligned to the specified or default calendar and may differ in the response as a result.
```
- The API uses the permissions (such as access permissions and user role features) of the user who created or owns
    the client credentials used to generate the access token.
- For preferences, the API uses system default and global settings, such asfor the time zone and currency, instead
    ofthe user's preferences.
- You can use the API to create a project with lifecycles enabled unless the lifecycle has financial steps.
- If your request contains a parameter, attribute, field, or other element that is unsupported or not valid, the API
    might react in one of the following ways:
       - The API creates the project successfullyusing the valid elements and returns warning messages about the
          elements that are unsupported or not valid.
       - The request fails with a 400 error and help text specifying why the request failed.

### Prerequisites

- To use this API call to create a project in Planview Portfolios, you must have the structure code of the parent work
    item under which you want to create the project. To find the structure code, follow the steps inFinding a Structure
    Code for a Work Itemand navigate to the work item you want to be the parent in the Plan structure hierarchy. You
    must be an administrator to access perform this task.
- The parent work item should be one level above theprimary planning level(PPL-1)in theWork Breakdown
    Structure (WBS).
- You also need the Work Description for the new project.

#### User Role FeaturUser Role Featureses

The following features must be enabled on your user role.

- Add/Delete Projects
- Modify Project Attributes
- View Project & Resource Mgmt.
- View Strategic Management

#### PermissionsPermissions

- You must have editing permissions (read/write)to the parent work item.

### Consumes

This API call consumes the following media types via the Content-Type request header:

- application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Path Parameters

None.

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

CreateProjectDtoPublic

### Example Data

Content-Type: application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

##### {

```
"data" : [ {
"hasChildren" : true,
"description" : "description",
"requestedFinish" : "2000-01-23T04:56:07.000+00:00",
"createdOn" : "2000-01-23T04:56:07.000+00:00",
"hasLifecycle" : true,
"constraintType" : "ASAP",
"productInvestmentApproval" : {
"structureCode" : "structureCode",
"description" : "description"
},
"scheduleStart" : "2000-01-23T04:56:07.000+00:00",
"place" : 5,
"progressAsPlanned" : true,
"scheduleFinish" : "2000-01-23T04:56:07.000+00:00",
"isMilestone" : true,
"isLifecycleEnabled" : true,
"actualFinish" : "2000-01-23T04:56:07.000+00:00",
"enterStatus" : true,
"hasTimeReported" : true,
"requestedStart" : "2000-01-23T04:56:07.000+00:00",
"structureCode" : "structureCode",
"depth" : 5,
"constraintDate" : "2000-01-23T04:56:07.000+00:00",
"createdBy" : {
"fullName" : "fullName",
"userName" : "userName"
},
"ticketable" : true,
"doNotProgress" : true,
"attributes" : {
"key" : ""
},
"scheduleDuration" : 1,
"shortName" : "shortName",
"actualStart" : "2000-01-23T04:56:07.000+00:00"
}, {
"hasChildren" : true,
"description" : "description",
"requestedFinish" : "2000-01-23T04:56:07.000+00:00",
"createdOn" : "2000-01-23T04:56:07.000+00:00",
"hasLifecycle" : true,
"constraintType" : "ASAP",
"productInvestmentApproval" : {
"structureCode" : "structureCode",
"description" : "description"
},
"scheduleStart" : "2000-01-23T04:56:07.000+00:00",
"place" : 5,
"progressAsPlanned" : true,
"scheduleFinish" : "2000-01-23T04:56:07.000+00:00",
"isMilestone" : true,
"isLifecycleEnabled" : true,
```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved


```
"actualFinish" : "2000-01-23T04:56:07.000+00:00",
"enterStatus" : true,
"hasTimeReported" : true,
"requestedStart" : "2000-01-23T04:56:07.000+00:00",
"structureCode" : "structureCode",
"depth" : 5,
"constraintDate" : "2000-01-23T04:56:07.000+00:00",
"createdBy" : {
"fullName" : "fullName",
"userName" : "userName"
},
"ticketable" : true,
"doNotProgress" : true,
"attributes" : {
"key" : ""
},
"scheduleDuration" : 1,
"shortName" : "shortName",
"actualStart" : "2000-01-23T04:56:07.000+00:00"
} ],
"meta" : {
"next" : {
"total" : 6,
"start" : "http://example.com/aeiou",
"page" : "http://example.com/aeiou"
},
"trace" : {
"id" : "046b6c7f-0b8a-43b9-b35d-6489e6daee91"
},
"warnings" : [ null, null ],
"errors" : [ {
"codeDesc" : "codeDesc",
"code" : 0,
"message" : "message"
}, {
"codeDesc" : "codeDesc",
"code" : 0,
"message" : "message"
} ]
}
}
```
### Produces

This API call produces the following media types according to theAcceptrequest header; the media type will be

conveyed by theContent-Typeresponse header.

- application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Responses

```
200 SuccessProjectDtoPublicResponseEnvelopeModel
```
```
401 Unauthorized
```
```
403 Forbidden
```
```
404 Not Found
```
## PATCH/public-api/v1/projects{id}

Update an existing project.( **publicApiV1ProjectsIdPatch** )

### Notes forUpdatinga Project

- You only needto include only the fields and values that you want changed in the request; you do not have to send
    theentire data transfer object (DTO).
- Attributes for an updated project may not match the request because of values controlled by the product, default
    values, and other changes the product makes based on user input.
- You cannotuse the API to update alifecycle-controlled Work Status because thatstatus is set automatically through
    the lifecycle process.

### Prerequisites

#### User Role FeaturUser Role Featureses

The following features must be enabled on your user role.

- Add/Delete Projects
- Modify Project Attributes
- View Project & Resource Mgmt.
- View Strategic Management

#### PermissionsPermissions

- You must have editing permissions (read/write)to the work item (project).

### Sample API Call

The following example shows an update to a single-select attribute in a project:

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

```
PATCH /projects/
{
"Wbs37": {
"structureCode": "3276",
"description": null,
"isNull": false
}
}
```
### Consumes

This API call consumes the following media types via the Content-Type request header:

- application/json

### Path Parameters

```
Parameter Description Required or Optional
```
```
id The project ID. Required
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
##### NOTE

```
The array includes custom attributes as well as the standard attributes.
```
```
Optional
```
### Return Type

ProjectDtoPublicResponseEnvelopeModel

### Example Data

Content-Type: application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

##### {

```
"data" : [ {
"hasChildren" : true,
"description" : "description",
"requestedFinish" : "2000-01-23T04:56:07.000+00:00",
"createdOn" : "2000-01-23T04:56:07.000+00:00",
"hasLifecycle" : true,
"constraintType" : "ASAP",
"productInvestmentApproval" : {
"structureCode" : "structureCode",
"description" : "description"
},
"scheduleStart" : "2000-01-23T04:56:07.000+00:00",
"place" : 5,
"progressAsPlanned" : true,
"scheduleFinish" : "2000-01-23T04:56:07.000+00:00",
"isMilestone" : true,
"isLifecycleEnabled" : true,
"actualFinish" : "2000-01-23T04:56:07.000+00:00",
"enterStatus" : true,
"hasTimeReported" : true,
"requestedStart" : "2000-01-23T04:56:07.000+00:00",
"structureCode" : "structureCode",
"depth" : 5,
"constraintDate" : "2000-01-23T04:56:07.000+00:00",
"createdBy" : {
"fullName" : "fullName",
"userName" : "userName"
},
"ticketable" : true,
"doNotProgress" : true,
"attributes" : {
"key" : ""
},
"scheduleDuration" : 1,
"shortName" : "shortName",
"actualStart" : "2000-01-23T04:56:07.000+00:00"
}, {
"hasChildren" : true,
"description" : "description",
"requestedFinish" : "2000-01-23T04:56:07.000+00:00",
"createdOn" : "2000-01-23T04:56:07.000+00:00",
"hasLifecycle" : true,
"constraintType" : "ASAP",
"productInvestmentApproval" : {
"structureCode" : "structureCode",
"description" : "description"
},
"scheduleStart" : "2000-01-23T04:56:07.000+00:00",
"place" : 5,
"progressAsPlanned" : true,
"scheduleFinish" : "2000-01-23T04:56:07.000+00:00",
"isMilestone" : true,
"isLifecycleEnabled" : true,
```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved


```
"actualFinish" : "2000-01-23T04:56:07.000+00:00",
"enterStatus" : true,
"hasTimeReported" : true,
"requestedStart" : "2000-01-23T04:56:07.000+00:00",
"structureCode" : "structureCode",
"depth" : 5,
"constraintDate" : "2000-01-23T04:56:07.000+00:00",
"createdBy" : {
"fullName" : "fullName",
"userName" : "userName"
},
"ticketable" : true,
"doNotProgress" : true,
"attributes" : {
"key" : ""
},
"scheduleDuration" : 1,
"shortName" : "shortName",
"actualStart" : "2000-01-23T04:56:07.000+00:00"
} ],
"meta" : {
"next" : {
"total" : 6,
"start" : "http://example.com/aeiou",
"page" : "http://example.com/aeiou"
},
"trace" : {
"id" : "046b6c7f-0b8a-43b9-b35d-6489e6daee91"
},
"warnings" : [ null, null ],
"errors" : [ {
"codeDesc" : "codeDesc",
"code" : 0,
"message" : "message"
}, {
"codeDesc" : "codeDesc",
"code" : 0,
"message" : "message"
} ]
}
}
```
### Produces

This API call produces the following media types according to theAcceptrequest header; the media type will be

conveyed by theContent-Typeresponse header.

- application/json

```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

### Responses

```
200 SuccessProjectDtoPublicResponseEnvelopeModel
```
```
401 Unauthorized
```
```
403 Forbidden
```
```
404 Not Found
```
```
Project Endpoint API © 2025 Planview, Inc.
Planview Confidential | All Rights Reserved
```

