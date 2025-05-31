# TaskBatchesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**TaskBatchesCreate**](TaskBatchesApi.md#TaskBatchesCreate) | **POST** /api/task-batches/ | 
[**TaskBatchesDestroy**](TaskBatchesApi.md#TaskBatchesDestroy) | **DELETE** /api/task-batches/{id}/ | 
[**TaskBatchesExportRetrieve**](TaskBatchesApi.md#TaskBatchesExportRetrieve) | **GET** /api/task-batches/{id}/export/ | 
[**TaskBatchesList**](TaskBatchesApi.md#TaskBatchesList) | **GET** /api/task-batches/ | 
[**TaskBatchesPartialUpdate**](TaskBatchesApi.md#TaskBatchesPartialUpdate) | **PATCH** /api/task-batches/{id}/ | 
[**TaskBatchesRetrieve**](TaskBatchesApi.md#TaskBatchesRetrieve) | **GET** /api/task-batches/{id}/ | 
[**TaskBatchesUpdate**](TaskBatchesApi.md#TaskBatchesUpdate) | **PUT** /api/task-batches/{id}/ | 


# **TaskBatchesCreate**
> TaskBatch TaskBatchesCreate(task_batch_request)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_task_batch_request <- TaskBatchRequest$new("name_example", 123, "description_example") # TaskBatchRequest | 

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesCreate(var_task_batch_requestdata_file = "result.txt")
result <- api_instance$TaskBatchesCreate(var_task_batch_request)
dput(result)
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
| **201** |  |  -  |

# **TaskBatchesDestroy**
> TaskBatchesDestroy(id)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task batch.

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
api_instance$TaskBatchesDestroy(var_id)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task batch. | 

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
| **204** | No response body |  -  |

# **TaskBatchesExportRetrieve**
> TaskBatch TaskBatchesExportRetrieve(id)



Export task batch data.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task batch.

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesExportRetrieve(var_iddata_file = "result.txt")
result <- api_instance$TaskBatchesExportRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task batch. | 

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
| **200** |  |  -  |

# **TaskBatchesList**
> PaginatedTaskBatchList TaskBatchesList(page = var.page)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_page <- 56 # integer | A page number within the paginated result set. (Optional)

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesList(page = var_pagedata_file = "result.txt")
result <- api_instance$TaskBatchesList(page = var_page)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **integer**| A page number within the paginated result set. | [optional] 

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
| **200** |  |  -  |

# **TaskBatchesPartialUpdate**
> TaskBatch TaskBatchesPartialUpdate(id, patched_task_batch_request = var.patched_task_batch_request)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task batch.
var_patched_task_batch_request <- PatchedTaskBatchRequest$new("name_example", "description_example", 123) # PatchedTaskBatchRequest |  (Optional)

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesPartialUpdate(var_id, patched_task_batch_request = var_patched_task_batch_requestdata_file = "result.txt")
result <- api_instance$TaskBatchesPartialUpdate(var_id, patched_task_batch_request = var_patched_task_batch_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task batch. | 
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
| **200** |  |  -  |

# **TaskBatchesRetrieve**
> TaskBatch TaskBatchesRetrieve(id)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task batch.

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesRetrieve(var_iddata_file = "result.txt")
result <- api_instance$TaskBatchesRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task batch. | 

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
| **200** |  |  -  |

# **TaskBatchesUpdate**
> TaskBatch TaskBatchesUpdate(id, task_batch_request)



ViewSet for managing task batches.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task batch.
var_task_batch_request <- TaskBatchRequest$new("name_example", 123, "description_example") # TaskBatchRequest | 

api_instance <- TaskBatchesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TaskBatchesUpdate(var_id, var_task_batch_requestdata_file = "result.txt")
result <- api_instance$TaskBatchesUpdate(var_id, var_task_batch_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task batch. | 
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
| **200** |  |  -  |

