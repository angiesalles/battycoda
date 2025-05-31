# PatchedSpeciesRequest

Serializer for Species model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.patched_species_request import PatchedSpeciesRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchedSpeciesRequest from a JSON string
patched_species_request_instance = PatchedSpeciesRequest.from_json(json)
# print the JSON string representation of the object
print(PatchedSpeciesRequest.to_json())

# convert the object into a dict
patched_species_request_dict = patched_species_request_instance.to_dict()
# create an instance of PatchedSpeciesRequest from a dict
patched_species_request_from_dict = PatchedSpeciesRequest.from_dict(patched_species_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


