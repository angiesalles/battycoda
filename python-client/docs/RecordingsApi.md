# openapi_client.RecordingsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**recordings_create**](RecordingsApi.md#recordings_create) | **POST** /api/recordings/ | 
[**recordings_destroy**](RecordingsApi.md#recordings_destroy) | **DELETE** /api/recordings/{id}/ | 
[**recordings_list**](RecordingsApi.md#recordings_list) | **GET** /api/recordings/ | 
[**recordings_partial_update**](RecordingsApi.md#recordings_partial_update) | **PATCH** /api/recordings/{id}/ | 
[**recordings_retrieve**](RecordingsApi.md#recordings_retrieve) | **GET** /api/recordings/{id}/ | 
[**recordings_update**](RecordingsApi.md#recordings_update) | **PUT** /api/recordings/{id}/ | 


# **recordings_create**
> Recording recordings_create(recording_request)

ViewSet for managing recordings.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.recording import Recording
from openapi_client.models.recording_request import RecordingRequest
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
    api_instance = openapi_client.RecordingsApi(api_client)
    recording_request = openapi_client.RecordingRequest() # RecordingRequest | 

    try:
        api_response = api_instance.recordings_create(recording_request)
        print("The response of RecordingsApi->recordings_create:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_create: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **recording_request** | [**RecordingRequest**](RecordingRequest.md)|  | 

### Return type

[**Recording**](Recording.md)

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

# **recordings_destroy**
> recordings_destroy(id)

ViewSet for managing recordings.

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
    api_instance = openapi_client.RecordingsApi(api_client)
    id = 56 # int | A unique integer value identifying this Recording.

    try:
        api_instance.recordings_destroy(id)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_destroy: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this Recording. | 

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

# **recordings_list**
> PaginatedRecordingList recordings_list(page=page)

ViewSet for managing recordings.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.paginated_recording_list import PaginatedRecordingList
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
    api_instance = openapi_client.RecordingsApi(api_client)
    page = 56 # int | A page number within the paginated result set. (optional)

    try:
        api_response = api_instance.recordings_list(page=page)
        print("The response of RecordingsApi->recordings_list:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_list: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional] 

### Return type

[**PaginatedRecordingList**](PaginatedRecordingList.md)

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

# **recordings_partial_update**
> Recording recordings_partial_update(id, patched_recording_request=patched_recording_request)

ViewSet for managing recordings.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.patched_recording_request import PatchedRecordingRequest
from openapi_client.models.recording import Recording
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
    api_instance = openapi_client.RecordingsApi(api_client)
    id = 56 # int | A unique integer value identifying this Recording.
    patched_recording_request = openapi_client.PatchedRecordingRequest() # PatchedRecordingRequest |  (optional)

    try:
        api_response = api_instance.recordings_partial_update(id, patched_recording_request=patched_recording_request)
        print("The response of RecordingsApi->recordings_partial_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_partial_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this Recording. | 
 **patched_recording_request** | [**PatchedRecordingRequest**](PatchedRecordingRequest.md)|  | [optional] 

### Return type

[**Recording**](Recording.md)

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

# **recordings_retrieve**
> Recording recordings_retrieve(id)

ViewSet for managing recordings.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.recording import Recording
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
    api_instance = openapi_client.RecordingsApi(api_client)
    id = 56 # int | A unique integer value identifying this Recording.

    try:
        api_response = api_instance.recordings_retrieve(id)
        print("The response of RecordingsApi->recordings_retrieve:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_retrieve: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this Recording. | 

### Return type

[**Recording**](Recording.md)

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

# **recordings_update**
> Recording recordings_update(id, recording_request)

ViewSet for managing recordings.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.recording import Recording
from openapi_client.models.recording_request import RecordingRequest
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
    api_instance = openapi_client.RecordingsApi(api_client)
    id = 56 # int | A unique integer value identifying this Recording.
    recording_request = openapi_client.RecordingRequest() # RecordingRequest | 

    try:
        api_response = api_instance.recordings_update(id, recording_request)
        print("The response of RecordingsApi->recordings_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RecordingsApi->recordings_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this Recording. | 
 **recording_request** | [**RecordingRequest**](RecordingRequest.md)|  | 

### Return type

[**Recording**](Recording.md)

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

