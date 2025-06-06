# PatchedProjectRequest

Serializer for Project model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**species_id** | **int** |  | [optional] 

## Example

```python
from openapi_client.models.patched_project_request import PatchedProjectRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchedProjectRequest from a JSON string
patched_project_request_instance = PatchedProjectRequest.from_json(json)
# print the JSON string representation of the object
print(PatchedProjectRequest.to_json())

# convert the object into a dict
patched_project_request_dict = patched_project_request_instance.to_dict()
# create an instance of PatchedProjectRequest from a dict
patched_project_request_from_dict = PatchedProjectRequest.from_dict(patched_project_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


