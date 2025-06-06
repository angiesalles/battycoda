# Task

Serializer for Task model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | [readonly] 
**batch** | [**TaskBatch**](TaskBatch.md) |  | [readonly] 
**status** | [**StatusEnum**](StatusEnum.md) |  | [optional] 
**onset** | **float** | Start time of the segment in seconds | 
**offset** | **float** | End time of the segment in seconds | 
**label** | **str** | Final expert label assigned to this task | [optional] 
**notes** | **str** | Additional notes or observations about this task | [optional] 
**created_at** | **datetime** |  | [readonly] 
**updated_at** | **datetime** |  | [readonly] 

## Example

```python
from openapi_client.models.task import Task

# TODO update the JSON string below
json = "{}"
# create an instance of Task from a JSON string
task_instance = Task.from_json(json)
# print the JSON string representation of the object
print(Task.to_json())

# convert the object into a dict
task_dict = task_instance.to_dict()
# create an instance of Task from a dict
task_from_dict = Task.from_dict(task_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


