# PatchedTaskBatchRequest

Serializer for TaskBatch model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**species_id** | **int** |  | [optional] 

## Example

```python
from openapi_client.models.patched_task_batch_request import PatchedTaskBatchRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchedTaskBatchRequest from a JSON string
patched_task_batch_request_instance = PatchedTaskBatchRequest.from_json(json)
# print the JSON string representation of the object
print(PatchedTaskBatchRequest.to_json())

# convert the object into a dict
patched_task_batch_request_dict = patched_task_batch_request_instance.to_dict()
# create an instance of PatchedTaskBatchRequest from a dict
patched_task_batch_request_from_dict = PatchedTaskBatchRequest.from_dict(patched_task_batch_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


