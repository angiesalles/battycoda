# PatchedRecordingRequest

Serializer for Recording model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the recording | [optional] 
**description** | **str** | Description of the recording | [optional] 
**location** | **str** | Location where the recording was made | [optional] 
**recorded_date** | **date** | Date when the recording was made | [optional] 
**project_id** | **int** |  | [optional] 

## Example

```python
from openapi_client.models.patched_recording_request import PatchedRecordingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchedRecordingRequest from a JSON string
patched_recording_request_instance = PatchedRecordingRequest.from_json(json)
# print the JSON string representation of the object
print(PatchedRecordingRequest.to_json())

# convert the object into a dict
patched_recording_request_dict = patched_recording_request_instance.to_dict()
# create an instance of PatchedRecordingRequest from a dict
patched_recording_request_from_dict = PatchedRecordingRequest.from_dict(patched_recording_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


