#' Create a new TaskRequest
#'
#' @description
#' Serializer for Task model.
#'
#' @docType class
#' @title TaskRequest
#' @description TaskRequest Class
#' @format An \code{R6Class} generator object
#' @field status  \link{StatusEnum} [optional]
#' @field onset Start time of the segment in seconds numeric
#' @field offset End time of the segment in seconds numeric
#' @field label Final expert label assigned to this task character [optional]
#' @field notes Additional notes or observations about this task character [optional]
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
TaskRequest <- R6::R6Class(
  "TaskRequest",
  public = list(
    `status` = NULL,
    `onset` = NULL,
    `offset` = NULL,
    `label` = NULL,
    `notes` = NULL,

    #' @description
    #' Initialize a new TaskRequest class.
    #'
    #' @param onset Start time of the segment in seconds
    #' @param offset End time of the segment in seconds
    #' @param status status
    #' @param label Final expert label assigned to this task
    #' @param notes Additional notes or observations about this task
    #' @param ... Other optional arguments.
    initialize = function(`onset`, `offset`, `status` = NULL, `label` = NULL, `notes` = NULL, ...) {
      if (!missing(`onset`)) {
        if (!(is.numeric(`onset`) && length(`onset`) == 1)) {
          stop(paste("Error! Invalid data for `onset`. Must be a number:", `onset`))
        }
        self$`onset` <- `onset`
      }
      if (!missing(`offset`)) {
        if (!(is.numeric(`offset`) && length(`offset`) == 1)) {
          stop(paste("Error! Invalid data for `offset`. Must be a number:", `offset`))
        }
        self$`offset` <- `offset`
      }
      if (!is.null(`status`)) {
        if (!(`status` %in% c())) {
          stop(paste("Error! \"", `status`, "\" cannot be assigned to `status`. Must be .", sep = ""))
        }
        stopifnot(R6::is.R6(`status`))
        self$`status` <- `status`
      }
      if (!is.null(`label`)) {
        if (!(is.character(`label`) && length(`label`) == 1)) {
          stop(paste("Error! Invalid data for `label`. Must be a string:", `label`))
        }
        self$`label` <- `label`
      }
      if (!is.null(`notes`)) {
        if (!(is.character(`notes`) && length(`notes`) == 1)) {
          stop(paste("Error! Invalid data for `notes`. Must be a string:", `notes`))
        }
        self$`notes` <- `notes`
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
    #' @return TaskRequest as a base R list.
    #' @examples
    #' # convert array of TaskRequest (x) to a data frame
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
    #' Convert TaskRequest to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      TaskRequestObject <- list()
      if (!is.null(self$`status`)) {
        TaskRequestObject[["status"]] <-
          self$`status`$toSimpleType()
      }
      if (!is.null(self$`onset`)) {
        TaskRequestObject[["onset"]] <-
          self$`onset`
      }
      if (!is.null(self$`offset`)) {
        TaskRequestObject[["offset"]] <-
          self$`offset`
      }
      if (!is.null(self$`label`)) {
        TaskRequestObject[["label"]] <-
          self$`label`
      }
      if (!is.null(self$`notes`)) {
        TaskRequestObject[["notes"]] <-
          self$`notes`
      }
      return(TaskRequestObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of TaskRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of TaskRequest
    fromJSON = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      if (!is.null(this_object$`status`)) {
        `status_object` <- StatusEnum$new()
        `status_object`$fromJSON(jsonlite::toJSON(this_object$`status`, auto_unbox = TRUE, digits = NA))
        self$`status` <- `status_object`
      }
      if (!is.null(this_object$`onset`)) {
        self$`onset` <- this_object$`onset`
      }
      if (!is.null(this_object$`offset`)) {
        self$`offset` <- this_object$`offset`
      }
      if (!is.null(this_object$`label`)) {
        self$`label` <- this_object$`label`
      }
      if (!is.null(this_object$`notes`)) {
        self$`notes` <- this_object$`notes`
      }
      self
    },

    #' @description
    #' To JSON String
    #' 
    #' @param ... Parameters passed to `jsonlite::toJSON`
    #' @return TaskRequest in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of TaskRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of TaskRequest
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`status` <- StatusEnum$new()$fromJSON(jsonlite::toJSON(this_object$`status`, auto_unbox = TRUE, digits = NA))
      self$`onset` <- this_object$`onset`
      self$`offset` <- this_object$`offset`
      self$`label` <- this_object$`label`
      self$`notes` <- this_object$`notes`
      self
    },

    #' @description
    #' Validate JSON input with respect to TaskRequest and throw an exception if invalid
    #'
    #' @param input the JSON input
    validateJSON = function(input) {
      input_json <- jsonlite::fromJSON(input)
      # check the required field `onset`
      if (!is.null(input_json$`onset`)) {
        if (!(is.numeric(input_json$`onset`) && length(input_json$`onset`) == 1)) {
          stop(paste("Error! Invalid data for `onset`. Must be a number:", input_json$`onset`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskRequest: the required field `onset` is missing."))
      }
      # check the required field `offset`
      if (!is.null(input_json$`offset`)) {
        if (!(is.numeric(input_json$`offset`) && length(input_json$`offset`) == 1)) {
          stop(paste("Error! Invalid data for `offset`. Must be a number:", input_json$`offset`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskRequest: the required field `offset` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of TaskRequest
    toString = function() {
      self$toJSONString()
    },

    #' @description
    #' Return true if the values in all fields are valid.
    #'
    #' @return true if the values in all fields are valid.
    isValid = function() {
      # check if the required `onset` is null
      if (is.null(self$`onset`)) {
        return(FALSE)
      }

      # check if the required `offset` is null
      if (is.null(self$`offset`)) {
        return(FALSE)
      }

      if (nchar(self$`label`) > 255) {
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
      # check if the required `onset` is null
      if (is.null(self$`onset`)) {
        invalid_fields["onset"] <- "Non-nullable required field `onset` cannot be null."
      }

      # check if the required `offset` is null
      if (is.null(self$`offset`)) {
        invalid_fields["offset"] <- "Non-nullable required field `offset` cannot be null."
      }

      if (nchar(self$`label`) > 255) {
        invalid_fields["label"] <- "Invalid length for `label`, must be smaller than or equal to 255."
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
# TaskRequest$unlock()
#
## Below is an example to define the print function
# TaskRequest$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# TaskRequest$lock()

