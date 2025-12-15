# Planview OKRs REST API – Objectives & Key Results

Merged documentation for Cursor and MCP usage.


---

## List Objectives API

### Page 1

List Objectives API
List Objectives
GET /api/rest/v1/objectives
Returns a paginated list of all objectives. Optional filters can be used to narr ow down r esults.
Query parameters
Parameter Type Required Default Description
ids String No — A comma-separated list of objective IDs to filter by .
limit Integer No 10 The number of r esults to r eturn. The maximum allowed is 500.
offset Integer No 0 The of fset for pagination.
Header parameters
Key Value Description Required
Authorization Bear er<token> The bear er token for authentication and access. Yes
Request examples
List default paginated objectives
The following example r equests a list of all objectives up to a maximum of 10 r esults with no pagination of fset (the
default parameter settings).
curl --location 'https://api-us.okrs.planview.com/api/rest/v1/objectives' \
--header 'Authorization: Bearer <token>'
List Objectives API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
1

### Page 2

List paginated objectives
The following example r equests a list of all objectives up to a maximum of 200 r esults.
curl --location 'https://api-us.okrs.planview.com/api/rest/v1/objectives?offset=0&limit=200' \
--header 'Authorization: Bearer <token>'
List objectives filter ed by ID
The following example r equests a list of only the objectives with objectives IDs of 28304 and 28305 with no pagination
offset.
curl --location 'https://api-us.okrs.planview.com/api/rest/v1/objectives?ids=28304,28305' \
--header 'Authorization: Bearer <token>'
Successful r esponse example
{
"fetch_objectives": {
"total_records": 1100,
"objectives": [
{
"id": 17841,
"name": "Increase customer satisfaction (NPS)",
"description": "Some description added",
"starts_at": "2025-01-01T00:00:00+00:00",
"ends_at": "2025-12-31T00:00:00+00:00",
"level_depth": 2,
"progress_percentage": 80,
"rolled_up_progress_percentage": 80,
"owned_by": "21f554b3-9954-45ba-bb24-276615a95e28",
"created_at": "2025-10-18T21:31:57.606585+00:00",
"parent_objective_id": null,
"work_item_container_id": 70,
"scope_id": "1223",
"scope_type": "Board"
}
]
}
}
Response fields
List Objectives API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
2

### Page 3

Top-level fields within fetch_objectives
Field Type Description
total_r ecords Integer The total number of objectives matching the query .
objectives Array of Objects A paginated list of objectives.
Fields within each objectives object
Field Type Description
id Integer The unique ID of the objective.
name String The title or name of the objective.
description String Additional details or context for the objective.
starts_at String
(ISO-8601)The start date for the overall tracking period of the objective.
ends_at String
(ISO-8601)The end date for the overall tracking period of the objective.
level_depth Integer The or ganization level this objective belongs in.
progress_per centage Integer The completion per centage based on the curr ent pr ogress of associated
key r esults. The maximum value is 100.
rolled_up_pr ogress_per centage Integer The completion percentage based on the curr ent pr ogress of associated
key r esults and child objectives. The maximum value is 100.
owned_by String The ID of the Planview Admin user who is assigned ownership of this key
result; this field may be null.
created_at String
(ISO-8601)The timestamp when the key r esult was cr eated.
parent_objective_id Integer The ID of the par ent objective.
work_item_container_id Integer The ID of the work item container that the objective belongs to. A work
item container can be an AgilePlace boar d,a Planview
Portfolios strategy , or a Planview Portfolios work item.
scope_id String The entity ID; this can be an AgilePlace boar d ID, a Planview Portfolios
strategy ID, or a Planview Portfolios work ID.
List Objectives API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
3

### Page 4

Field Type Description
NOTE
The data type is consider ed a string because some strategy or work
IDs may be in a string format.
scope_type String The entity type. Possible values ar eBoard (from AgilePlace) or Strategy
orWork (fromPlanview Portfolios).
List Objectives API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
4


---

## List Key Results for Objective API

### Page 1

List Key Results for Objective API
List Key Results for Objective
GET /api/rest/v1/objectives/ {objective_id} /key-results
Retrieves all key r esults associated with a specific objective.
Path parameters
Parameter Type Description
objective_id Integer The ID of the objective whose key r esults ar e to be r etrieved.
Header parameters
Key Value Description Required
Authorization Bear er<token> The bear er token for authentication and access. Yes
Request example
The following example r equests details on the key r esults associated with the objective with an objective ID of 17841.
curl --location 'https://api-us.okrs.planview.com/api/rest/v1/objectives/17841/key-results' \
--header 'Authorization: Bearer <token>'
List Key Results for Objective API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
1

### Page 2

Successful r esponse example
{
"key_results": [
{
"id": 28304,
"name": "Increase NPS Score",
"description": "Describe it further",
"objective_id": 17841,
"overall_starts_at": "2025-01-01T00:00:00+00:00",
"overall_ends_at": "2025-12-31T00:00:00+00:00",
"starting_value": 0,
"final_target_value": 1,
"created_at": "2025-10-18T21:37:29.445796+00:00",
"owned_by": null,
"progress_percentage": 80,
"targets": [
{
"id": 26547,
"starts_at": "2025-01-01T00:00:00+00:00",
"ends_at": "2025-12-31T00:00:00+00:00",
"value": 1
}
],
"progress_points": [
{
"id": 28633,
"measured_at": "2025-11-16",
"value": 0.8,
"comment": "Launched in-app survey to collect user sentiment"
},
{
"id": 27401,
"measured_at": "2025-10-18",
"value": 0.6,
"comment": "Received positive feedback after product update"
}
]
}
]
}
Response fields
Top-level field
The top-level key_r esults field is an array of objects.
List Key Results for Objective API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
2

### Page 3

Fields within each key_r esults object
Field Type Description
id Integer The unique ID of the key r esult.
name String The title or name of the key r esult.
description String Additional details or context for the key r esult.
objective_id Integer The ID of the objective this key r esult is associated with.
overall_starts_at String
(ISO-8601)The start date for the overall tracking period of the key r esult. This date is the same
as the starts_at value for the first tar get.
overall_ends_at String
(ISO-8601)The end date for the overall tracking period of the key r esult. This date is the same
as the ends_at value for the last tar get.
starting_value Float The initial value for the key r esult.
final_tar get_value Float The end goal for the key r esult (the final value to achieve). This is equal
tovalue forthe last targets object.
created_at String
(ISO-8601)The timestamp when the key r esult was cr eated.
owned_by String The ID of the Planview Admin user who is assigned ownership of this key r esult;
this field may be null.
progress_per centage Integer The completion per centage based on the curr ent pr ogress. This value can exceed
100.
targets Array of
objectsA list of tar gets associated with the key r esult.
progress_points Array of
objectsA list of r ecorded pr ogress data entries over time.
Fields within each targets object
Field Type Description
id Integer The unique ID of the tar get.
starts_at String (ISO-8601) The start date of the tar get's time period.
ends_at String (ISO-8601) The end date of the tar get's time period.
value Float The tar get value to be achieved by the ends_at date for the tar get.
List Key Results for Objective API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
3

### Page 4

Fields within each progress_points object
Field Type Description
id Integer The unique ID of the pr ogress point.
measur ed_at String (YYYY -MM-DD) The date when the pr ogress was r ecorded.
value Float The pr ogress value r ecorded on that date.
comment String An optional comment or note about the pr ogress update.
List Key Results for Objective API © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
4
