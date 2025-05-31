# openapi_client.TaskBatchesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**task_batches_create**](TaskBatchesApi.md#task_batches_create) | **POST** /api/task-batches/ | 
[**task_batches_destroy**](TaskBatchesApi.md#task_batches_destroy) | **DELETE** /api/task-batches/{id}/ | 
[**task_batches_export_retrieve**](TaskBatchesApi.md#task_batches_export_retrieve) | **GET** /api/task-batches/{id}/export/ | 
[**task_batches_list**](TaskBatchesApi.md#task_batches_list) | **GET** /api/task-batches/ | 
[**task_batches_partial_update**](TaskBatchesApi.md#task_batches_partial_update) | **PATCH** /api/task-batches/{id}/ | 
[**task_batches_retrieve**](TaskBatchesApi.md#task_batches_retrieve) | **GET** /api/task-batches/{id}/ | 
[**task_batches_update**](TaskBatchesApi.md#task_batches_update) | **PUT** /api/task-batches/{id}/ | 


# **task_batches_create**
> TaskBatch task_batches_create(task_batch_request)

ViewSet for managing task batches.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.task_batch import TaskBatch
from openapi_client.models.task_batch_request import TaskBatchRequest
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    task_batch_request = openapi_client.TaskBatchRequest() # TaskBatchRequest | 

    try:
        api_response = api_instance.task_batches_create(task_batch_request)
        print("The response of TaskBatchesApi->task_batches_create:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_create: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_batch_request** | [**TaskBatchRequest**](TaskBatchRequest.md)|  | 

### Return type

[**TaskBatch**](TaskBatch.md)

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

# **task_batches_destroy**
> task_batches_destroy(id)

ViewSet for managing task batches.

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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    id = 56 # int | A unique integer value identifying this task batch.

    try:
        api_instance.task_batches_destroy(id)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_destroy: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this task batch. | 

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

# **task_batches_export_retrieve**
> TaskBatch task_batches_export_retrieve(id)

Export task batch data.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.task_batch import TaskBatch
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    id = 56 # int | A unique integer value identifying this task batch.

    try:
        api_response = api_instance.task_batches_export_retrieve(id)
        print("The response of TaskBatchesApi->task_batches_export_retrieve:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_export_retrieve: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this task batch. | 

### Return type

[**TaskBatch**](TaskBatch.md)

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

# **task_batches_list**
> PaginatedTaskBatchList task_batches_list(page=page)

ViewSet for managing task batches.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.paginated_task_batch_list import PaginatedTaskBatchList
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    page = 56 # int | A page number within the paginated result set. (optional)

    try:
        api_response = api_instance.task_batches_list(page=page)
        print("The response of TaskBatchesApi->task_batches_list:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_list: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional] 

### Return type

[**PaginatedTaskBatchList**](PaginatedTaskBatchList.md)

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

# **task_batches_partial_update**
> TaskBatch task_batches_partial_update(id, patched_task_batch_request=patched_task_batch_request)

ViewSet for managing task batches.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.patched_task_batch_request import PatchedTaskBatchRequest
from openapi_client.models.task_batch import TaskBatch
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    id = 56 # int | A unique integer value identifying this task batch.
    patched_task_batch_request = openapi_client.PatchedTaskBatchRequest() # PatchedTaskBatchRequest |  (optional)

    try:
        api_response = api_instance.task_batches_partial_update(id, patched_task_batch_request=patched_task_batch_request)
        print("The response of TaskBatchesApi->task_batches_partial_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_partial_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this task batch. | 
 **patched_task_batch_request** | [**PatchedTaskBatchRequest**](PatchedTaskBatchRequest.md)|  | [optional] 

### Return type

[**TaskBatch**](TaskBatch.md)

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

# **task_batches_retrieve**
> TaskBatch task_batches_retrieve(id)

ViewSet for managing task batches.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.task_batch import TaskBatch
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    id = 56 # int | A unique integer value identifying this task batch.

    try:
        api_response = api_instance.task_batches_retrieve(id)
        print("The response of TaskBatchesApi->task_batches_retrieve:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_retrieve: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this task batch. | 

### Return type

[**TaskBatch**](TaskBatch.md)

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

# **task_batches_update**
> TaskBatch task_batches_update(id, task_batch_request)

ViewSet for managing task batches.

### Example

* Api Key Authentication (cookieAuth):

```python
import openapi_client
from openapi_client.models.task_batch import TaskBatch
from openapi_client.models.task_batch_request import TaskBatchRequest
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
    api_instance = openapi_client.TaskBatchesApi(api_client)
    id = 56 # int | A unique integer value identifying this task batch.
    task_batch_request = openapi_client.TaskBatchRequest() # TaskBatchRequest | 

    try:
        api_response = api_instance.task_batches_update(id, task_batch_request)
        print("The response of TaskBatchesApi->task_batches_update:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TaskBatchesApi->task_batches_update: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this task batch. | 
 **task_batch_request** | [**TaskBatchRequest**](TaskBatchRequest.md)|  | 

### Return type

[**TaskBatch**](TaskBatch.md)

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

