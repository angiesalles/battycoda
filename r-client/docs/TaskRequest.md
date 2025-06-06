# openapi::TaskRequest

Serializer for Task model.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**StatusEnum**](StatusEnum.md) |  | [optional] [Enum: ] 
**onset** | **numeric** | Start time of the segment in seconds | 
**offset** | **numeric** | End time of the segment in seconds | 
**label** | **character** | Final expert label assigned to this task | [optional] [Max. length: 255] 
**notes** | **character** | Additional notes or observations about this task | [optional] 


