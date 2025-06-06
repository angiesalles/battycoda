# ProjectRequest

Serializer for Project model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**description** | **str** |  | [optional] 
**species_id** | **int** |  | 

## Example

```python
from openapi_client.models.project_request import ProjectRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ProjectRequest from a JSON string
project_request_instance = ProjectRequest.from_json(json)
# print the JSON string representation of the object
print(ProjectRequest.to_json())

# convert the object into a dict
project_request_dict = project_request_instance.to_dict()
# create an instance of ProjectRequest from a dict
project_request_from_dict = ProjectRequest.from_dict(project_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


