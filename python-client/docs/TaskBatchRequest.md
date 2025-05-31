# TaskBatchRequest

Serializer for TaskBatch model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**description** | **str** |  | [optional] 
**species_id** | **int** |  | 

## Example

```python
from openapi_client.models.task_batch_request import TaskBatchRequest

# TODO update the JSON string below
json = "{}"
# create an instance of TaskBatchRequest from a JSON string
task_batch_request_instance = TaskBatchRequest.from_json(json)
# print the JSON string representation of the object
print(TaskBatchRequest.to_json())

# convert the object into a dict
task_batch_request_dict = task_batch_request_instance.to_dict()
# create an instance of TaskBatchRequest from a dict
task_batch_request_from_dict = TaskBatchRequest.from_dict(task_batch_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


