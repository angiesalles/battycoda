#' Create a new PatchedTaskBatchRequest
#'
#' @description
#' Serializer for TaskBatch model.
#'
#' @docType class
#' @title PatchedTaskBatchRequest
#' @description PatchedTaskBatchRequest Class
#' @format An \code{R6Class} generator object
#' @field name  character [optional]
#' @field description  character [optional]
#' @field species_id  integer [optional]
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
PatchedTaskBatchRequest <- R6::R6Class(
  "PatchedTaskBatchRequest",
  public = list(
    `name` = NULL,
    `description` = NULL,
    `species_id` = NULL,

    #' @description
    #' Initialize a new PatchedTaskBatchRequest class.
    #'
    #' @param name name
    #' @param description description
    #' @param species_id species_id
    #' @param ... Other optional arguments.
    initialize = function(`name` = NULL, `description` = NULL, `species_id` = NULL, ...) {
      if (!is.null(`name`)) {
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
      if (!is.null(`species_id`)) {
        if (!(is.numeric(`species_id`) && length(`species_id`) == 1)) {
          stop(paste("Error! Invalid data for `species_id`. Must be an integer:", `species_id`))
        }
        self$`species_id` <- `species_id`
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
    #' @return PatchedTaskBatchRequest as a base R list.
    #' @examples
    #' # convert array of PatchedTaskBatchRequest (x) to a data frame
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
    #' Convert PatchedTaskBatchRequest to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      PatchedTaskBatchRequestObject <- list()
      if (!is.null(self$`name`)) {
        PatchedTaskBatchRequestObject[["name"]] <-
          self$`name`
      }
      if (!is.null(self$`description`)) {
        PatchedTaskBatchRequestObject[["description"]] <-
          self$`description`
      }
      if (!is.null(self$`species_id`)) {
        PatchedTaskBatchRequestObject[["species_id"]] <-
          self$`species_id`
      }
      return(PatchedTaskBatchRequestObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of PatchedTaskBatchRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of PatchedTaskBatchRequest
    fromJSON = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      if (!is.null(this_object$`name`)) {
        self$`name` <- this_object$`name`
      }
      if (!is.null(this_object$`description`)) {
        self$`description` <- this_object$`description`
      }
      if (!is.null(this_object$`species_id`)) {
        self$`species_id` <- this_object$`species_id`
      }
      self
    },

    #' @description
    #' To JSON String
    #' 
    #' @param ... Parameters passed to `jsonlite::toJSON`
    #' @return PatchedTaskBatchRequest in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of PatchedTaskBatchRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of PatchedTaskBatchRequest
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`name` <- this_object$`name`
      self$`description` <- this_object$`description`
      self$`species_id` <- this_object$`species_id`
      self
    },

    #' @description
    #' Validate JSON input with respect to PatchedTaskBatchRequest and throw an exception if invalid
    #'
    #' @param input the JSON input
    validateJSON = function(input) {
      input_json <- jsonlite::fromJSON(input)
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of PatchedTaskBatchRequest
    toString = function() {
      self$toJSONString()
    },

    #' @description
    #' Return true if the values in all fields are valid.
    #'
    #' @return true if the values in all fields are valid.
    isValid = function() {
      if (nchar(self$`name`) > 255) {
        return(FALSE)
      }
      if (nchar(self$`name`) < 1) {
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
      if (nchar(self$`name`) > 255) {
        invalid_fields["name"] <- "Invalid length for `name`, must be smaller than or equal to 255."
      }
      if (nchar(self$`name`) < 1) {
        invalid_fields["name"] <- "Invalid length for `name`, must be bigger than or equal to 1."
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
# PatchedTaskBatchRequest$unlock()
#
## Below is an example to define the print function
# PatchedTaskBatchRequest$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# PatchedTaskBatchRequest$lock()

