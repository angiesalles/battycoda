# RecordingsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**RecordingsCreate**](RecordingsApi.md#RecordingsCreate) | **POST** /api/recordings/ | 
[**RecordingsDestroy**](RecordingsApi.md#RecordingsDestroy) | **DELETE** /api/recordings/{id}/ | 
[**RecordingsList**](RecordingsApi.md#RecordingsList) | **GET** /api/recordings/ | 
[**RecordingsPartialUpdate**](RecordingsApi.md#RecordingsPartialUpdate) | **PATCH** /api/recordings/{id}/ | 
[**RecordingsRetrieve**](RecordingsApi.md#RecordingsRetrieve) | **GET** /api/recordings/{id}/ | 
[**RecordingsUpdate**](RecordingsApi.md#RecordingsUpdate) | **PUT** /api/recordings/{id}/ | 


# **RecordingsCreate**
> Recording RecordingsCreate(recording_request)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_recording_request <- RecordingRequest$new("name_example", "description_example", "location_example", "recorded_date_example", 123) # RecordingRequest | 

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$RecordingsCreate(var_recording_requestdata_file = "result.txt")
result <- api_instance$RecordingsCreate(var_recording_request)
dput(result)
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
| **201** |  |  -  |

# **RecordingsDestroy**
> RecordingsDestroy(id)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this Recording.

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
api_instance$RecordingsDestroy(var_id)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this Recording. | 

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

# **RecordingsList**
> PaginatedRecordingList RecordingsList(page = var.page)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_page <- 56 # integer | A page number within the paginated result set. (Optional)

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$RecordingsList(page = var_pagedata_file = "result.txt")
result <- api_instance$RecordingsList(page = var_page)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **integer**| A page number within the paginated result set. | [optional] 

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
| **200** |  |  -  |

# **RecordingsPartialUpdate**
> Recording RecordingsPartialUpdate(id, patched_recording_request = var.patched_recording_request)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this Recording.
var_patched_recording_request <- PatchedRecordingRequest$new("name_example", "description_example", "location_example", "recorded_date_example", 123) # PatchedRecordingRequest |  (Optional)

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$RecordingsPartialUpdate(var_id, patched_recording_request = var_patched_recording_requestdata_file = "result.txt")
result <- api_instance$RecordingsPartialUpdate(var_id, patched_recording_request = var_patched_recording_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this Recording. | 
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
| **200** |  |  -  |

# **RecordingsRetrieve**
> Recording RecordingsRetrieve(id)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this Recording.

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$RecordingsRetrieve(var_iddata_file = "result.txt")
result <- api_instance$RecordingsRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this Recording. | 

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
| **200** |  |  -  |

# **RecordingsUpdate**
> Recording RecordingsUpdate(id, recording_request)



ViewSet for managing recordings.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this Recording.
var_recording_request <- RecordingRequest$new("name_example", "description_example", "location_example", "recorded_date_example", 123) # RecordingRequest | 

api_instance <- RecordingsApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$RecordingsUpdate(var_id, var_recording_requestdata_file = "result.txt")
result <- api_instance$RecordingsUpdate(var_id, var_recording_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this Recording. | 
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
| **200** |  |  -  |

