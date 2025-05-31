# ProjectsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ProjectsCreate**](ProjectsApi.md#ProjectsCreate) | **POST** /api/projects/ | 
[**ProjectsDestroy**](ProjectsApi.md#ProjectsDestroy) | **DELETE** /api/projects/{id}/ | 
[**ProjectsList**](ProjectsApi.md#ProjectsList) | **GET** /api/projects/ | 
[**ProjectsPartialUpdate**](ProjectsApi.md#ProjectsPartialUpdate) | **PATCH** /api/projects/{id}/ | 
[**ProjectsRetrieve**](ProjectsApi.md#ProjectsRetrieve) | **GET** /api/projects/{id}/ | 
[**ProjectsUpdate**](ProjectsApi.md#ProjectsUpdate) | **PUT** /api/projects/{id}/ | 


# **ProjectsCreate**
> Project ProjectsCreate(project_request)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_project_request <- ProjectRequest$new("name_example", 123, "description_example") # ProjectRequest | 

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$ProjectsCreate(var_project_requestdata_file = "result.txt")
result <- api_instance$ProjectsCreate(var_project_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_request** | [**ProjectRequest**](ProjectRequest.md)|  | 

### Return type

[**Project**](Project.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** |  |  -  |

# **ProjectsDestroy**
> ProjectsDestroy(id)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this project.

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
api_instance$ProjectsDestroy(var_id)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this project. | 

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

# **ProjectsList**
> PaginatedProjectList ProjectsList(page = var.page)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_page <- 56 # integer | A page number within the paginated result set. (Optional)

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$ProjectsList(page = var_pagedata_file = "result.txt")
result <- api_instance$ProjectsList(page = var_page)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **integer**| A page number within the paginated result set. | [optional] 

### Return type

[**PaginatedProjectList**](PaginatedProjectList.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

# **ProjectsPartialUpdate**
> Project ProjectsPartialUpdate(id, patched_project_request = var.patched_project_request)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this project.
var_patched_project_request <- PatchedProjectRequest$new("name_example", "description_example", 123) # PatchedProjectRequest |  (Optional)

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$ProjectsPartialUpdate(var_id, patched_project_request = var_patched_project_requestdata_file = "result.txt")
result <- api_instance$ProjectsPartialUpdate(var_id, patched_project_request = var_patched_project_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this project. | 
 **patched_project_request** | [**PatchedProjectRequest**](PatchedProjectRequest.md)|  | [optional] 

### Return type

[**Project**](Project.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

# **ProjectsRetrieve**
> Project ProjectsRetrieve(id)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this project.

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$ProjectsRetrieve(var_iddata_file = "result.txt")
result <- api_instance$ProjectsRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this project. | 

### Return type

[**Project**](Project.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

# **ProjectsUpdate**
> Project ProjectsUpdate(id, project_request)



ViewSet for managing projects.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this project.
var_project_request <- ProjectRequest$new("name_example", 123, "description_example") # ProjectRequest | 

api_instance <- ProjectsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$ProjectsUpdate(var_id, var_project_requestdata_file = "result.txt")
result <- api_instance$ProjectsUpdate(var_id, var_project_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this project. | 
 **project_request** | [**ProjectRequest**](ProjectRequest.md)|  | 

### Return type

[**Project**](Project.md)

### Authorization

[cookieAuth](../README.md#cookieAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** |  |  -  |

