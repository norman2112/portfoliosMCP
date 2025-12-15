# Planview SOAP API Behaviors and Warnings

This document explains common behaviors and warnings you may encounter when using the Planview Portfolios MCP server tools.

## Overview

The Planview SOAP API has several behaviors that may seem unexpected but are normal:

1. **Response payloads may be incomplete** - The API doesn't always echo back full data
2. **Warnings are non-fatal** - Configuration warnings don't prevent successful operations
3. **Null fields in responses** - Some fields may be null even though data was persisted

## 1. Financial Plan Upsert Response Behavior

### What You See
When calling `upsert_financial_plan`, the response may show:
```json
{
  "success": true,
  "data": {
    "Key": "key://12/8874",
    "Lines": {
      "FinancialPlanLineDto": []
    }
  }
}
```

### Why This Happens
The SOAP API doesn't always echo back the full payload in the response. This is a design decision by Planview - the API confirms the operation succeeded but doesn't return the complete data structure.

### Impact
**Zero impact on functionality** - The financial plan data IS persisted correctly in Planview. The empty Lines array is just a response quirk.

### How to Verify
Use `read_financial_plan()` to verify the data was saved:
```python
# After upsert
plan_info = await read_financial_plan(ctx, entity_key="key://2/$Plan/17326", version_key="key://14/1")
# This will show the actual persisted lines
```

## 2. Task Creation Response Behavior

### What You See
When calling `create_task`, the response may show null for many fields:
```json
{
  "success": true,
  "data": {
    "Key": "key://2/$Plan/17346",
    "ActualFinishDate": null,
    "Duration": null,
    "ScheduleFinishDate": null,
    "ScheduleStartDate": null
  }
}
```

Even though you submitted:
```json
{
  "Description": "My Task",
  "ScheduleStartDate": "2024-01-01T08:00:00",
  "ScheduleFinishDate": "2024-01-15T17:00:00"
}
```

### Why This Happens
The SOAP API response DTO doesn't always populate all fields, even though the task was created successfully with those values. This is normal SOAP API behavior.

### Impact
**None** - Tasks are correctly scheduled in Planview. The null fields are just a response representation issue.

### How to Verify
Use `read_task()` to verify the task was created correctly:
```python
# After create_task
task_info = await read_task(ctx, task_key="key://2/$Plan/17346")
# This will show the actual task data with dates
```

## 3. Invalid Structure Code Warning

### What You See
```
Meta Warning: "InvalidStructureCode" - (2263) is not a valid choice for Region
```

### Why This Happens
Planview tried to apply a default structure code (2263) for the Region field, but that code isn't configured as a valid choice in your Planview instance.

### Impact
**Non-fatal** - Projects are created successfully. This is just a configuration warning indicating that the default region code needs to be set up in Planview administration.

### What to Do
- **Option 1**: Ignore it - Projects work fine without it
- **Option 2**: Configure the default region code in Planview administration
- **Option 3**: Explicitly set a valid region code when creating projects

## 4. Invalid Default Values Warning

### What You See
```
Meta Warning: "InvalidDefaultValues" - Encountered (1) warnings while applying attribute default values
```

### Why This Happens
Planview tried to apply default attribute values that aren't configured in your environment. This typically happens when:
- Custom attributes don't have defaults set up
- The Planview instance has customized attributes that weren't initialized

### Impact
**Non-fatal** - Projects are created successfully with all required fields (scheduleStart, scheduleFinish, description). The warning just indicates some optional defaults couldn't be applied.

### What to Do
- **Option 1**: Ignore it - Projects work fine
- **Option 2**: Configure default values for custom attributes in Planview administration
- **Option 3**: Explicitly set attribute values when creating projects

## 5. How Warnings Are Returned

All tools that use the SOAP API return warnings in the response:

```json
{
  "success": true,
  "data": { ... },
  "warnings": [
    {
      "code": "InvalidStructureCode",
      "error_message": "(2263) is not a valid choice for Region",
      "source_index": 0
    }
  ]
}
```

Check the `warnings` array in any response to see non-fatal warnings.

## Best Practices

1. **Always check the `warnings` array** - It contains useful information about configuration issues
2. **Use read operations to verify** - After creating/updating, use the corresponding read tool to verify data
3. **Don't rely on response payloads** - The SOAP API doesn't always echo back full data
4. **Warnings are informational** - They indicate configuration opportunities, not failures

## Summary

| Behavior | Impact | Action Required |
|----------|--------|-----------------|
| Empty Lines array in financial plan response | None - data is persisted | Use `read_financial_plan()` to verify |
| Null fields in task response | None - task is created correctly | Use `read_task()` to verify |
| InvalidStructureCode warning | None - project created successfully | Optional: Configure default region |
| InvalidDefaultValues warning | None - project created successfully | Optional: Configure attribute defaults |

All of these behaviors are **normal SOAP API quirks** and don't indicate problems with your code or data. The operations succeed - the responses just don't always show the full picture.

