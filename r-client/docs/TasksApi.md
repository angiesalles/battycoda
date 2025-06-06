# TasksApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**TasksAnnotateCreate**](TasksApi.md#TasksAnnotateCreate) | **POST** /api/tasks/{id}/annotate/ | 
[**TasksList**](TasksApi.md#TasksList) | **GET** /api/tasks/ | 
[**TasksRetrieve**](TasksApi.md#TasksRetrieve) | **GET** /api/tasks/{id}/ | 


# **TasksAnnotateCreate**
> Task TasksAnnotateCreate(id, task_request)



Submit annotation for a task.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task.
var_task_request <- TaskRequest$new(123, 123, StatusEnum$new(), "label_example", "notes_example") # TaskRequest | 

api_instance <- TasksApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TasksAnnotateCreate(var_id, var_task_requestdata_file = "result.txt")
result <- api_instance$TasksAnnotateCreate(var_id, var_task_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task. | 
 **task_request** | [**TaskRequest**](TaskRequest.md)|  | 

### Return type

[**Task**](Task.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

# **TasksList**
> PaginatedTaskList TasksList(page = var.page)



ViewSet for viewing tasks (read-only).

### Example
```R
library(openapi)

# prepare function argument(s)
var_page <- 56 # integer | A page number within the paginated result set. (Optional)

api_instance <- TasksApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TasksList(page = var_pagedata_file = "result.txt")
result <- api_instance$TasksList(page = var_page)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **integer**| A page number within the paginated result set. | [optional] 

### Return type

[**PaginatedTaskList**](PaginatedTaskList.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

# **TasksRetrieve**
> Task TasksRetrieve(id)



ViewSet for viewing tasks (read-only).

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this task.

api_instance <- TasksApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$TasksRetrieve(var_iddata_file = "result.txt")
result <- api_instance$TasksRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this task. | 

### Return type

[**Task**](Task.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

