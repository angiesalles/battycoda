# SpeciesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SpeciesCreate**](SpeciesApi.md#SpeciesCreate) | **POST** /api/species/ | 
[**SpeciesDestroy**](SpeciesApi.md#SpeciesDestroy) | **DELETE** /api/species/{id}/ | 
[**SpeciesList**](SpeciesApi.md#SpeciesList) | **GET** /api/species/ | 
[**SpeciesPartialUpdate**](SpeciesApi.md#SpeciesPartialUpdate) | **PATCH** /api/species/{id}/ | 
[**SpeciesRetrieve**](SpeciesApi.md#SpeciesRetrieve) | **GET** /api/species/{id}/ | 
[**SpeciesUpdate**](SpeciesApi.md#SpeciesUpdate) | **PUT** /api/species/{id}/ | 


# **SpeciesCreate**
> Species SpeciesCreate(species_request)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_species_request <- SpeciesRequest$new("name_example", "description_example") # SpeciesRequest | 

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$SpeciesCreate(var_species_requestdata_file = "result.txt")
result <- api_instance$SpeciesCreate(var_species_request)
dput(result)
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
| **201** |  |  -  |

# **SpeciesDestroy**
> SpeciesDestroy(id)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this species.

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
api_instance$SpeciesDestroy(var_id)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this species. | 

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

# **SpeciesList**
> PaginatedSpeciesList SpeciesList(page = var.page)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_page <- 56 # integer | A page number within the paginated result set. (Optional)

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$SpeciesList(page = var_pagedata_file = "result.txt")
result <- api_instance$SpeciesList(page = var_page)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **integer**| A page number within the paginated result set. | [optional] 

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
| **200** |  |  -  |

# **SpeciesPartialUpdate**
> Species SpeciesPartialUpdate(id, patched_species_request = var.patched_species_request)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this species.
var_patched_species_request <- PatchedSpeciesRequest$new("name_example", "description_example") # PatchedSpeciesRequest |  (Optional)

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$SpeciesPartialUpdate(var_id, patched_species_request = var_patched_species_requestdata_file = "result.txt")
result <- api_instance$SpeciesPartialUpdate(var_id, patched_species_request = var_patched_species_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this species. | 
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
| **200** |  |  -  |

# **SpeciesRetrieve**
> Species SpeciesRetrieve(id)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this species.

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$SpeciesRetrieve(var_iddata_file = "result.txt")
result <- api_instance$SpeciesRetrieve(var_id)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this species. | 

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
| **200** |  |  -  |

# **SpeciesUpdate**
> Species SpeciesUpdate(id, species_request)



ViewSet for managing species.

### Example
```R
library(openapi)

# prepare function argument(s)
var_id <- 56 # integer | A unique integer value identifying this species.
var_species_request <- SpeciesRequest$new("name_example", "description_example") # SpeciesRequest | 

api_instance <- SpeciesApi$new()
# Configure API key authorization: cookieAuth
api_instance$api_client$api_keys["sessionid"] <- Sys.getenv("API_KEY")
# to save the result into a file, simply add the optional `data_file` parameter, e.g.
# result <- api_instance$SpeciesUpdate(var_id, var_species_requestdata_file = "result.txt")
result <- api_instance$SpeciesUpdate(var_id, var_species_request)
dput(result)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **integer**| A unique integer value identifying this species. | 
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
| **200** |  |  -  |

