# openapi_client.SpeciesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**species_create**](SpeciesApi.md#species_create) | **POST** /api/species/ | 
[**species_destroy**](SpeciesApi.md#species_destroy) | **DELETE** /api/species/{id}/ | 
[**species_list**](SpeciesApi.md#species_list) | **GET** /api/species/ | 
[**species_partial_update**](SpeciesApi.md#species_partial_update) | **PATCH** /api/species/{id}/ | 
[**species_retrieve**](SpeciesApi.md#species_retrieve) | **GET** /api/species/{id}/ | 
[**species_update**](SpeciesApi.md#species_update) | **PUT** /api/species/{id}/ | 


# **species_create**
> Species species_create(species_request)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.species import Species
from openapi_client.models.species_request import SpeciesRequest
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    species_request = openapi_client.SpeciesRequest() # SpeciesRequest | 

    try:
        api_response = api_instance.species_create(species_request)
        print("The response of SpeciesApi->species_create:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_create: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **species_request** | [**SpeciesRequest**](SpeciesRequest.md)|  | 

### Return type

[**Species**](Species.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **species_destroy**
> species_destroy(id)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    id = 56 # int | A unique integer value identifying this species.

    try:
        api_instance.species_destroy(id)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_destroy: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this species. | 

### Return type

void (empty response body)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | No response body |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **species_list**
> PaginatedSpeciesList species_list(page=page)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.paginated_species_list import PaginatedSpeciesList
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    page = 56 # int | A page number within the paginated result set. (optional)

    try:
        api_response = api_instance.species_list(page=page)
        print("The response of SpeciesApi->species_list:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_list: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional] 

### Return type

[**PaginatedSpeciesList**](PaginatedSpeciesList.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **species_partial_update**
> Species species_partial_update(id, patched_species_request=patched_species_request)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.patched_species_request import PatchedSpeciesRequest
from openapi_client.models.species import Species
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    id = 56 # int | A unique integer value identifying this species.
    patched_species_request = openapi_client.PatchedSpeciesRequest() # PatchedSpeciesRequest |  (optional)

    try:
        api_response = api_instance.species_partial_update(id, patched_species_request=patched_species_request)
        print("The response of SpeciesApi->species_partial_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_partial_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this species. | 
 **patched_species_request** | [**PatchedSpeciesRequest**](PatchedSpeciesRequest.md)|  | [optional] 

### Return type

[**Species**](Species.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **species_retrieve**
> Species species_retrieve(id)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.species import Species
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    id = 56 # int | A unique integer value identifying this species.

    try:
        api_response = api_instance.species_retrieve(id)
        print("The response of SpeciesApi->species_retrieve:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_retrieve: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this species. | 

### Return type

[**Species**](Species.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **species_update**
> Species species_update(id, species_request)

ViewSet for managing species.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.species import Species
from openapi_client.models.species_request import SpeciesRequest
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.SpeciesApi(api_client)
    id = 56 # int | A unique integer value identifying this species.
    species_request = openapi_client.SpeciesRequest() # SpeciesRequest | 

    try:
        api_response = api_instance.species_update(id, species_request)
        print("The response of SpeciesApi->species_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpeciesApi->species_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this species. | 
 **species_request** | [**SpeciesRequest**](SpeciesRequest.md)|  | 

### Return type

[**Species**](Species.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

