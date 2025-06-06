# RecordingRequest

Serializer for Recording model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the recording | 
**description** | **str** | Description of the recording | [optional] 
**location** | **str** | Location where the recording was made | [optional] 
**recorded_date** | **date** | Date when the recording was made | [optional] 
**project_id** | **int** |  | [optional] 

## Example

```python
from openapi_client.models.recording_request import RecordingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of RecordingRequest from a JSON string
recording_request_instance = RecordingRequest.from_json(json)
# print the JSON string representation of the object
print(RecordingRequest.to_json())

# convert the object into a dict
recording_request_dict = recording_request_instance.to_dict()
# create an instance of RecordingRequest from a dict
recording_request_from_dict = RecordingRequest.from_dict(recording_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


