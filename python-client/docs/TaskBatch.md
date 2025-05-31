# TaskBatch

Serializer for TaskBatch model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | [readonly] 
**name** | **str** |  | 
**description** | **str** |  | [optional] 
**species** | [**Species**](Species.md) |  | [readonly] 
**total_tasks** | **str** |  | [readonly] 
**completed_tasks** | **str** |  | [readonly] 
**pending_tasks** | **str** |  | [readonly] 
**progress_percentage** | **str** |  | [readonly] 
**created_at** | **datetime** |  | [readonly] 

## Example

```python
from openapi_client.models.task_batch import TaskBatch

# TODO update the JSON string below
json = "{}"
# create an instance of TaskBatch from a JSON string
task_batch_instance = TaskBatch.from_json(json)
# print the JSON string representation of the object
print(TaskBatch.to_json())

# convert the object into a dict
task_batch_dict = task_batch_instance.to_dict()
# create an instance of TaskBatch from a dict
task_batch_from_dict = TaskBatch.from_dict(task_batch_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


