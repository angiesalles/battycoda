# openapi::Recording

Serializer for Recording model.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **integer** |  | [readonly] 
**name** | **character** | Name of the recording | [Max. length: 255] 
**description** | **character** | Description of the recording | [optional] 
**location** | **character** | Location where the recording was made | [optional] [Max. length: 255] 
**recorded_date** | **character** | Date when the recording was made | [optional] 
**duration** | **numeric** | Duration of the recording in seconds | [readonly] 
**sample_rate** | **integer** | Sample rate of the recording in Hz | [readonly] 
**project** | [**Project**](Project.md) |  | [readonly] 
**wav_file_url** | **character** |  | [readonly] 
**created_at** | **character** |  | [readonly] 


