#' Create a new ProjectRequest
#'
#' @description
#' Serializer for Project model.
#'
#' @docType class
#' @title ProjectRequest
#' @description ProjectRequest Class
#' @format An \code{R6Class} generator object
#' @field name  character
#' @field description  character [optional]
#' @field species_id  integer
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
ProjectRequest <- R6::R6Class(
  "ProjectRequest",
  public = list(
    `name` = NULL,
    `description` = NULL,
    `species_id` = NULL,

    #' @description
    #' Initialize a new ProjectRequest class.
    #'
    #' @param name name
    #' @param species_id species_id
    #' @param description description
    #' @param ... Other optional arguments.
    initialize = function(`name`, `species_id`, `description` = NULL, ...) {
      if (!missing(`name`)) {
        if (!(is.character(`name`) && length(`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", `name`))
        }
        self$`name` <- `name`
      }
      if (!missing(`species_id`)) {
        if (!(is.numeric(`species_id`) && length(`species_id`) == 1)) {
          stop(paste("Error! Invalid data for `species_id`. Must be an integer:", `species_id`))
        }
        self$`species_id` <- `species_id`
      }
      if (!is.null(`description`)) {
        if (!(is.character(`description`) && length(`description`) == 1)) {
          stop(paste("Error! Invalid data for `description`. Must be a string:", `description`))
        }
        self$`description` <- `description`
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
    #' @return ProjectRequest as a base R list.
    #' @examples
    #' # convert array of ProjectRequest (x) to a data frame
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
    #' Convert ProjectRequest to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      ProjectRequestObject <- list()
      if (!is.null(self$`name`)) {
        ProjectRequestObject[["name"]] <-
          self$`name`
      }
      if (!is.null(self$`description`)) {
        ProjectRequestObject[["description"]] <-
          self$`description`
      }
      if (!is.null(self$`species_id`)) {
        ProjectRequestObject[["species_id"]] <-
          self$`species_id`
      }
      return(ProjectRequestObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of ProjectRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of ProjectRequest
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
    #' @return ProjectRequest in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of ProjectRequest
    #'
    #' @param input_json the JSON input
    #' @return the instance of ProjectRequest
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`name` <- this_object$`name`
      self$`description` <- this_object$`description`
      self$`species_id` <- this_object$`species_id`
      self
    },

    #' @description
    #' Validate JSON input with respect to ProjectRequest and throw an exception if invalid
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
        stop(paste("The JSON input `", input, "` is invalid for ProjectRequest: the required field `name` is missing."))
      }
      # check the required field `species_id`
      if (!is.null(input_json$`species_id`)) {
        if (!(is.numeric(input_json$`species_id`) && length(input_json$`species_id`) == 1)) {
          stop(paste("Error! Invalid data for `species_id`. Must be an integer:", input_json$`species_id`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for ProjectRequest: the required field `species_id` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of ProjectRequest
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

      # check if the required `species_id` is null
      if (is.null(self$`species_id`)) {
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

      # check if the required `species_id` is null
      if (is.null(self$`species_id`)) {
        invalid_fields["species_id"] <- "Non-nullable required field `species_id` cannot be null."
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
# ProjectRequest$unlock()
#
## Below is an example to define the print function
# ProjectRequest$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# ProjectRequest$lock()

