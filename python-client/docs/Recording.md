# Recording

Serializer for Recording model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | [readonly] 
**name** | **str** | Name of the recording | 
**description** | **str** | Description of the recording | [optional] 
**location** | **str** | Location where the recording was made | [optional] 
**recorded_date** | **date** | Date when the recording was made | [optional] 
**duration** | **float** | Duration of the recording in seconds | [readonly] 
**sample_rate** | **int** | Sample rate of the recording in Hz | [readonly] 
**project** | [**Project**](Project.md) |  | [readonly] 
**wav_file_url** | **str** |  | [readonly] 
**created_at** | **datetime** |  | [readonly] 

## Example

```python
from openapi_client.models.recording import Recording

# TODO update the JSON string below
json = "{}"
# create an instance of Recording from a JSON string
recording_instance = Recording.from_json(json)
# print the JSON string representation of the object
print(Recording.to_json())

# convert the object into a dict
recording_dict = recording_instance.to_dict()
# create an instance of Recording from a dict
recording_from_dict = Recording.from_dict(recording_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


