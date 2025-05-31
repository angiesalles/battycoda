# PaginatedProjectList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** |  | 
**next** | **str** |  | [optional] 
**previous** | **str** |  | [optional] 
**results** | [**List[Project]**](Project.md) |  | 

## Example

```python
from openapi_client.models.paginated_project_list import PaginatedProjectList

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedProjectList from a JSON string
paginated_project_list_instance = PaginatedProjectList.from_json(json)
# print the JSON string representation of the object
print(PaginatedProjectList.to_json())

# convert the object into a dict
paginated_project_list_dict = paginated_project_list_instance.to_dict()
# create an instance of PaginatedProjectList from a dict
paginated_project_list_from_dict = PaginatedProjectList.from_dict(paginated_project_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


