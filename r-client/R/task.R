#' Create a new Task
#'
#' @description
#' Serializer for Task model.
#'
#' @docType class
#' @title Task
#' @description Task Class
#' @format An \code{R6Class} generator object
#' @field id  integer
#' @field batch  \link{TaskBatch}
#' @field status  \link{StatusEnum} [optional]
#' @field onset Start time of the segment in seconds numeric
#' @field offset End time of the segment in seconds numeric
#' @field label Final expert label assigned to this task character [optional]
#' @field notes Additional notes or observations about this task character [optional]
#' @field created_at  character
#' @field updated_at  character
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
Task <- R6::R6Class(
  "Task",
  public = list(
    `id` = NULL,
    `batch` = NULL,
    `status` = NULL,
    `onset` = NULL,
    `offset` = NULL,
    `label` = NULL,
    `notes` = NULL,
    `created_at` = NULL,
    `updated_at` = NULL,

    #' @description
    #' Initialize a new Task class.
    #'
    #' @param id id
    #' @param batch batch
    #' @param onset Start time of the segment in seconds
    #' @param offset End time of the segment in seconds
    #' @param created_at created_at
    #' @param updated_at updated_at
    #' @param status status
    #' @param label Final expert label assigned to this task
    #' @param notes Additional notes or observations about this task
    #' @param ... Other optional arguments.
    initialize = function(`id`, `batch`, `onset`, `offset`, `created_at`, `updated_at`, `status` = NULL, `label` = NULL, `notes` = NULL, ...) {
      if (!missing(`id`)) {
        if (!(is.numeric(`id`) && length(`id`) == 1)) {
          stop(paste("Error! Invalid data for `id`. Must be an integer:", `id`))
        }
        self$`id` <- `id`
      }
      if (!missing(`batch`)) {
        stopifnot(R6::is.R6(`batch`))
        self$`batch` <- `batch`
      }
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
      if (!missing(`created_at`)) {
        if (!(is.character(`created_at`) && length(`created_at`) == 1)) {
          stop(paste("Error! Invalid data for `created_at`. Must be a string:", `created_at`))
        }
        self$`created_at` <- `created_at`
      }
      if (!missing(`updated_at`)) {
        if (!(is.character(`updated_at`) && length(`updated_at`) == 1)) {
          stop(paste("Error! Invalid data for `updated_at`. Must be a string:", `updated_at`))
        }
        self$`updated_at` <- `updated_at`
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
    #' @return Task as a base R list.
    #' @examples
    #' # convert array of Task (x) to a data frame
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
    #' Convert Task to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      TaskObject <- list()
      if (!is.null(self$`id`)) {
        TaskObject[["id"]] <-
          self$`id`
      }
      if (!is.null(self$`batch`)) {
        TaskObject[["batch"]] <-
          self$`batch`$toSimpleType()
      }
      if (!is.null(self$`status`)) {
        TaskObject[["status"]] <-
          self$`status`$toSimpleType()
      }
      if (!is.null(self$`onset`)) {
        TaskObject[["onset"]] <-
          self$`onset`
      }
      if (!is.null(self$`offset`)) {
        TaskObject[["offset"]] <-
          self$`offset`
      }
      if (!is.null(self$`label`)) {
        TaskObject[["label"]] <-
          self$`label`
      }
      if (!is.null(self$`notes`)) {
        TaskObject[["notes"]] <-
          self$`notes`
      }
      if (!is.null(self$`created_at`)) {
        TaskObject[["created_at"]] <-
          self$`created_at`
      }
      if (!is.null(self$`updated_at`)) {
        TaskObject[["updated_at"]] <-
          self$`updated_at`
      }
      return(TaskObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of Task
    #'
    #' @param input_json the JSON input
    #' @return the instance of Task
    fromJSON = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      if (!is.null(this_object$`id`)) {
        self$`id` <- this_object$`id`
      }
      if (!is.null(this_object$`batch`)) {
        `batch_object` <- TaskBatch$new()
        `batch_object`$fromJSON(jsonlite::toJSON(this_object$`batch`, auto_unbox = TRUE, digits = NA))
        self$`batch` <- `batch_object`
      }
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
      if (!is.null(this_object$`created_at`)) {
        self$`created_at` <- this_object$`created_at`
      }
      if (!is.null(this_object$`updated_at`)) {
        self$`updated_at` <- this_object$`updated_at`
      }
      self
    },

    #' @description
    #' To JSON String
    #' 
    #' @param ... Parameters passed to `jsonlite::toJSON`
    #' @return Task in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of Task
    #'
    #' @param input_json the JSON input
    #' @return the instance of Task
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`id` <- this_object$`id`
      self$`batch` <- TaskBatch$new()$fromJSON(jsonlite::toJSON(this_object$`batch`, auto_unbox = TRUE, digits = NA))
      self$`status` <- StatusEnum$new()$fromJSON(jsonlite::toJSON(this_object$`status`, auto_unbox = TRUE, digits = NA))
      self$`onset` <- this_object$`onset`
      self$`offset` <- this_object$`offset`
      self$`label` <- this_object$`label`
      self$`notes` <- this_object$`notes`
      self$`created_at` <- this_object$`created_at`
      self$`updated_at` <- this_object$`updated_at`
      self
    },

    #' @description
    #' Validate JSON input with respect to Task and throw an exception if invalid
    #'
    #' @param input the JSON input
    validateJSON = function(input) {
      input_json <- jsonlite::fromJSON(input)
      # check the required field `id`
      if (!is.null(input_json$`id`)) {
        if (!(is.numeric(input_json$`id`) && length(input_json$`id`) == 1)) {
          stop(paste("Error! Invalid data for `id`. Must be an integer:", input_json$`id`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `id` is missing."))
      }
      # check the required field `batch`
      if (!is.null(input_json$`batch`)) {
        stopifnot(R6::is.R6(input_json$`batch`))
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `batch` is missing."))
      }
      # check the required field `onset`
      if (!is.null(input_json$`onset`)) {
        if (!(is.numeric(input_json$`onset`) && length(input_json$`onset`) == 1)) {
          stop(paste("Error! Invalid data for `onset`. Must be a number:", input_json$`onset`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `onset` is missing."))
      }
      # check the required field `offset`
      if (!is.null(input_json$`offset`)) {
        if (!(is.numeric(input_json$`offset`) && length(input_json$`offset`) == 1)) {
          stop(paste("Error! Invalid data for `offset`. Must be a number:", input_json$`offset`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `offset` is missing."))
      }
      # check the required field `created_at`
      if (!is.null(input_json$`created_at`)) {
        if (!(is.character(input_json$`created_at`) && length(input_json$`created_at`) == 1)) {
          stop(paste("Error! Invalid data for `created_at`. Must be a string:", input_json$`created_at`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `created_at` is missing."))
      }
      # check the required field `updated_at`
      if (!is.null(input_json$`updated_at`)) {
        if (!(is.character(input_json$`updated_at`) && length(input_json$`updated_at`) == 1)) {
          stop(paste("Error! Invalid data for `updated_at`. Must be a string:", input_json$`updated_at`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Task: the required field `updated_at` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of Task
    toString = function() {
      self$toJSONString()
    },

    #' @description
    #' Return true if the values in all fields are valid.
    #'
    #' @return true if the values in all fields are valid.
    isValid = function() {
      # check if the required `id` is null
      if (is.null(self$`id`)) {
        return(FALSE)
      }

      # check if the required `batch` is null
      if (is.null(self$`batch`)) {
        return(FALSE)
      }

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

      # check if the required `created_at` is null
      if (is.null(self$`created_at`)) {
        return(FALSE)
      }

      # check if the required `updated_at` is null
      if (is.null(self$`updated_at`)) {
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
      # check if the required `id` is null
      if (is.null(self$`id`)) {
        invalid_fields["id"] <- "Non-nullable required field `id` cannot be null."
      }

      # check if the required `batch` is null
      if (is.null(self$`batch`)) {
        invalid_fields["batch"] <- "Non-nullable required field `batch` cannot be null."
      }

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

      # check if the required `created_at` is null
      if (is.null(self$`created_at`)) {
        invalid_fields["created_at"] <- "Non-nullable required field `created_at` cannot be null."
      }

      # check if the required `updated_at` is null
      if (is.null(self$`updated_at`)) {
        invalid_fields["updated_at"] <- "Non-nullable required field `updated_at` cannot be null."
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
# Task$unlock()
#
## Below is an example to define the print function
# Task$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# Task$lock()

