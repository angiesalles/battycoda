#' Create a new RecordingRequest
#'
#' @description
#' Serializer for Recording model.
#'
#' @docType class
#' @title RecordingRequest
#' @description RecordingRequest Class
#' @format An \code{R6Class} generator object
#' @field name Name of the recording character
#' @field description Description of the recording character [optional]
#' @field location Location where the recording was made character [optional]
#' @field recorded_date Date when the recording was made character [optional]
#' @field project_id  integer [optional]
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
RecordingRequest <- R6::R6Class(
  "RecordingRequest",
  public = list(
    `name` = NULL,
    `description` = NULL,
    `location` = NULL,
    `recorded_date` = NULL,
    `project_id` = NULL,

    #' @description
    #' Initialize a new RecordingRequest class.
    #'
    #' @param name Name of the recording
    #' @param description Description of the recording
    #' @param location Location where the recording was made
    #' @param recorded_date Date when the recording was made
    #' @param project_id project_id
    #' @param ... Other optional arguments.
    initialize = function(`name`, `description` = NULL, `location` = NULL, `recorded_date` = NULL, `project_id` = NULL, ...) {
      if (!missing(`name`)) {
        if (!(is.character(`name`) && length(`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", `name`))
        }
        self$`name` <- `name`
      }
      if (!is.null(`description`)) {
        if (!(is.character(`description`) && length(`description`) == 1)) {
          stop(paste("Error! Invalid data for `description`. Must be a string:", `description`))
        }
        self$`description` <- `description`
      }
      if (!is.null(`location`)) {
        if (!(is.character(`location`) && length(`location`) == 1)) {
          stop(paste("Error! Invalid data for `location`. Must be a string:", `location`))
        }
        self$`location` <- `location`
      }
      if (!is.null(`recorded_date`)) {
        if (!is.character(`recorded_date`)) {
          stop(paste("Error! Invalid data for `recorded_date`. Must be a string:", `recorded_date`))
        }
        self$`recorded_date` <- `recorded_date`
      }
      if (!is.null(`project_id`)) {
        if (!(is.numeric(`project_id`) && length(`project_id`) == 1)) {
          stop(paste("Error! Invalid data for `project_id`. Must be an integer:", `project_id`))
        }
        self$`project_id` <- `project_id`
      }
    },

    #' @description
    #' Convert to an R object. This method is deprecated. Use `toSimpleType()` instead.
    toJSON = function() {
      .Deprecated(new = "toSimpleType", msg = "Use the '$toSimpleType()' method instead since that is more clearly named. Use '$toJSONString()' to get a JSON string")
      return(self$toSimpleType())
    },

    #' @description
    #' Convert to a List
    #'
    #' Convert the R6 object to a list to work more easily with other tooling.
    #'
    #' @return RecordingRequest as a base R list.
    #' @examples
    #' # convert array of RecordingRequest (x) to a data frame
    #' \dontrun{
    #' library(purrr)
    #' library(tibble)
    #' df <- x |> map(\(y)y$toList()) |> map(as_tibble) |> list_rbind()
    #' df
    #' }
    toList = function() {
      return(self$toSimpleType())
    },

    #' @description
    #' Convert RecordingRequest to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      RecordingRequestObject <- list()
      if (!is.null(self$`name`)) {
        RecordingRequestObject[["name"]] <-
          self$`name`
      }
      if (!is.null(self$`description`)) {
        RecordingRequestObject[["description"]] <-
          self$`description`
      }
      if (!is.null(self$`location`)) {
        RecordingRequestObject[["location"]] <-
          self$`location`
      }
      if (!is.null(self$`recorded_date`)) {
        RecordingRequestObject[["recorded_date"]] <-
          self$`recorded_date`
      }
      if (!is.null(self$`project_id`)) {
        RecordingRequestObject[["project_id"]] <-
          self$`project_id`
      }
      return(RecordingRequestObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of RecordingRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of RecordingRequest
    fromJSON = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      if (!is.null(this_object$`name`)) {
        self$`name` <- this_object$`name`
      }
      if (!is.null(this_object$`description`)) {
        self$`description` <- this_object$`description`
      }
      if (!is.null(this_object$`location`)) {
        self$`location` <- this_object$`location`
      }
      if (!is.null(this_object$`recorded_date`)) {
        self$`recorded_date` <- this_object$`recorded_date`
      }
      if (!is.null(this_object$`project_id`)) {
        self$`project_id` <- this_object$`project_id`
      }
      self
    },

    #' @description
    #' To JSON String
    #' 
    #' @param ... Parameters passed to `jsonlite::toJSON`
    #' @return RecordingRequest in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of RecordingRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of RecordingRequest
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`name` <- this_object$`name`
      self$`description` <- this_object$`description`
      self$`location` <- this_object$`location`
      self$`recorded_date` <- this_object$`recorded_date`
      self$`project_id` <- this_object$`project_id`
      self
    },

    #' @description
    #' Validate JSON input with respect to RecordingRequest and throw an exception if invalid
    #'
    #' @param input the JSON input
    validateJSON = function(input) {
      input_json <- jsonlite::fromJSON(input)
      # check the required field `name`
      if (!is.null(input_json$`name`)) {
        if (!(is.character(input_json$`name`) && length(input_json$`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", input_json$`name`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for RecordingRequest: the required field `name` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of RecordingRequest
    toString = function() {
      self$toJSONString()
    },

    #' @description
    #' Return true if the values in all fields are valid.
    #'
    #' @return true if the values in all fields are valid.
    isValid = function() {
      # check if the required `name` is null
      if (is.null(self$`name`)) {
        return(FALSE)
      }

      if (nchar(self$`name`) > 255) {
        return(FALSE)
      }
      if (nchar(self$`name`) < 1) {
        return(FALSE)
      }

      if (nchar(self$`location`) > 255) {
        return(FALSE)
      }

      TRUE
    },

    #' @description
    #' Return a list of invalid fields (if any).
    #'
    #' @return A list of invalid fields (if any).
    getInvalidFields = function() {
      invalid_fields <- list()
      # check if the required `name` is null
      if (is.null(self$`name`)) {
        invalid_fields["name"] <- "Non-nullable required field `name` cannot be null."
      }

      if (nchar(self$`name`) > 255) {
        invalid_fields["name"] <- "Invalid length for `name`, must be smaller than or equal to 255."
      }
      if (nchar(self$`name`) < 1) {
        invalid_fields["name"] <- "Invalid length for `name`, must be bigger than or equal to 1."
      }

      if (nchar(self$`location`) > 255) {
        invalid_fields["location"] <- "Invalid length for `location`, must be smaller than or equal to 255."
      }

      invalid_fields
    },

    #' @description
    #' Print the object
    print = function() {
      print(jsonlite::prettify(self$toJSONString()))
      invisible(self)
    }
  ),
  # Lock the class to prevent modifications to the method or field
  lock_class = TRUE
)
## Uncomment below to unlock the class to allow modifications of the method or field
# RecordingRequest$unlock()
#
## Below is an example to define the print function
# RecordingRequest$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# RecordingRequest$lock()

