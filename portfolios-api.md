# Planview Portfolios REST API — Combined Markdown

## 1. OAuth Endpoint API

### Overview
The OAuth endpoint provides authentication and authorization for all Portfolios REST APIs.

### GET /public-api/v1/oauth/ping
Secured ping endpoint requiring a valid OAuth token.

**Returns:**  
`pong`

**Responses**
- 200 Success
- 401 Unauthorized

### POST /public-api/v1/oauth/token
Generates a bearer token.

**Notes**
- Token valid for 60 minutes
- Uses client_credentials grant
- Requires client_id and client_secret

**Sample Request**
```json
POST /token
{
  "grant_type": "client_credentials",
  "client_id": "YourClientIdGoesHere",
  "client_secret": "YourClientSecretGoesHere"
}
```

**Sample Response**
```json
{
  "access_token": "access_token",
  "token_type": "bearer",
  "expires_in": 0
}
```

---

## 2. Project Endpoint API

### Overview
APIs for interacting with Projects at the Primary Planning Level (PPL).

### General Notes
- Attribute metadata available at `/projects/attributes/available`
- Query params support filtering
- Values are case-sensitive
- APIs process one record at a time (no batching)

### GET /public-api/v1/projects/attributes/available
Returns available project attributes.

### GET /public-api/v1/projects/{id}
Retrieves a project by ID.

**Params**
- id (required)
- attributes (optional)

### POST /public-api/v1/projects
Creates a new project.

**Notes**
- JSON only
- Defaults may override values
- Duration auto-calculated
- Actual dates cannot be set
- Parent structure code required

### PATCH /public-api/v1/projects/{id}
Updates a project.  
Only include fields to be changed.

**Example**
```json
PATCH /projects/12345
{
  "Wbs37": {
    "structureCode": "3276",
    "description": null,
    "isNull": false
  }
}
```

---

## 3. Work Endpoint API

### Overview
APIs for Work items (tasks and lower-level planning entities).

### GET /public-api/v1/work/attributes/available
Returns metadata for all Work attributes.

### GET /public-api/v1/work
Returns filtered work items.

**Query**
- filter (required)
- attributes (optional)

### GET /public-api/v1/work/{id}
Returns a single work item.

**Params**
- id (required)
- attributes (optional)
