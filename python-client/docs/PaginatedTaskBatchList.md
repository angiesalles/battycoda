# PaginatedTaskBatchList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** |  | 
**next** | **str** |  | [optional] 
**previous** | **str** |  | [optional] 
**results** | [**List[TaskBatch]**](TaskBatch.md) |  | 

## Example

```python
from openapi_client.models.paginated_task_batch_list import PaginatedTaskBatchList

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedTaskBatchList from a JSON string
paginated_task_batch_list_instance = PaginatedTaskBatchList.from_json(json)
# print the JSON string representation of the object
print(PaginatedTaskBatchList.to_json())

# convert the object into a dict
paginated_task_batch_list_dict = paginated_task_batch_list_instance.to_dict()
# create an instance of PaginatedTaskBatchList from a dict
paginated_task_batch_list_from_dict = PaginatedTaskBatchList.from_dict(paginated_task_batch_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


