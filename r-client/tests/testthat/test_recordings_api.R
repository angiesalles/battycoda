# Automatically generated by openapi-generator (https://openapi-generator.tech)
# Please update as you see appropriate

context("Test RecordingsApi")

api_instance <- RecordingsApi$new()

test_that("RecordingsCreate", {
  # tests for RecordingsCreate
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param recording_request RecordingRequest 
  # @return [Recording]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("RecordingsDestroy", {
  # tests for RecordingsDestroy
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param id integer A unique integer value identifying this Recording.
  # @return [Void]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("RecordingsList", {
  # tests for RecordingsList
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param page integer A page number within the paginated result set. (optional)
  # @return [PaginatedRecordingList]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("RecordingsPartialUpdate", {
  # tests for RecordingsPartialUpdate
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param id integer A unique integer value identifying this Recording.
  # @param patched_recording_request PatchedRecordingRequest  (optional)
  # @return [Recording]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("RecordingsRetrieve", {
  # tests for RecordingsRetrieve
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param id integer A unique integer value identifying this Recording.
  # @return [Recording]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("RecordingsUpdate", {
  # tests for RecordingsUpdate
  # base path: http://localhost
  # ViewSet for managing recordings.
  # @param id integer A unique integer value identifying this Recording.
  # @param recording_request RecordingRequest 
  # @return [Recording]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})
