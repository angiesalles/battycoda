# PaginatedRecordingList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** |  | 
**next** | **str** |  | [optional] 
**previous** | **str** |  | [optional] 
**results** | [**List[Recording]**](Recording.md) |  | 

## Example

```python
from openapi_client.models.paginated_recording_list import PaginatedRecordingList

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedRecordingList from a JSON string
paginated_recording_list_instance = PaginatedRecordingList.from_json(json)
# print the JSON string representation of the object
print(PaginatedRecordingList.to_json())

# convert the object into a dict
paginated_recording_list_dict = paginated_recording_list_instance.to_dict()
# create an instance of PaginatedRecordingList from a dict
paginated_recording_list_from_dict = PaginatedRecordingList.from_dict(paginated_recording_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


