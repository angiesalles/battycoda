# Automatically generated by openapi-generator (https://openapi-generator.tech)
# Please update as you see appropriate

context("Test TasksApi")

api_instance <- TasksApi$new()

test_that("TasksAnnotateCreate", {
  # tests for TasksAnnotateCreate
  # base path: http://localhost
  # Submit annotation for a task.
  # @param id integer A unique integer value identifying this task.
  # @param task_request TaskRequest 
  # @return [Task]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("TasksList", {
  # tests for TasksList
  # base path: http://localhost
  # ViewSet for viewing tasks (read-only).
  # @param page integer A page number within the paginated result set. (optional)
  # @return [PaginatedTaskList]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})

test_that("TasksRetrieve", {
  # tests for TasksRetrieve
  # base path: http://localhost
  # ViewSet for viewing tasks (read-only).
  # @param id integer A unique integer value identifying this task.
  # @return [Task]

  # uncomment below to test the operation
  #expect_equal(result, "EXPECTED_RESULT")
})
