# SpeciesRequest

Serializer for Species model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**description** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.species_request import SpeciesRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SpeciesRequest from a JSON string
species_request_instance = SpeciesRequest.from_json(json)
# print the JSON string representation of the object
print(SpeciesRequest.to_json())

# convert the object into a dict
species_request_dict = species_request_instance.to_dict()
# create an instance of SpeciesRequest from a dict
species_request_from_dict = SpeciesRequest.from_dict(species_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


