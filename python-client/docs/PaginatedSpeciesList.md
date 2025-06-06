# PaginatedSpeciesList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** |  | 
**next** | **str** |  | [optional] 
**previous** | **str** |  | [optional] 
**results** | [**List[Species]**](Species.md) |  | 

## Example

```python
from openapi_client.models.paginated_species_list import PaginatedSpeciesList

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedSpeciesList from a JSON string
paginated_species_list_instance = PaginatedSpeciesList.from_json(json)
# print the JSON string representation of the object
print(PaginatedSpeciesList.to_json())

# convert the object into a dict
paginated_species_list_dict = paginated_species_list_instance.to_dict()
# create an instance of PaginatedSpeciesList from a dict
paginated_species_list_from_dict = PaginatedSpeciesList.from_dict(paginated_species_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


