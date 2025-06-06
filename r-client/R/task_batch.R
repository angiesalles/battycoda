#' Create a new TaskBatch
#'
#' @description
#' Serializer for TaskBatch model.
#'
#' @docType class
#' @title TaskBatch
#' @description TaskBatch Class
#' @format An \code{R6Class} generator object
#' @field id  integer
#' @field name  character
#' @field description  character [optional]
#' @field species  \link{Species}
#' @field total_tasks  character
#' @field completed_tasks  character
#' @field pending_tasks  character
#' @field progress_percentage  character
#' @field created_at  character
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
TaskBatch <- R6::R6Class(
  "TaskBatch",
  public = list(
    `id` = NULL,
    `name` = NULL,
    `description` = NULL,
    `species` = NULL,
    `total_tasks` = NULL,
    `completed_tasks` = NULL,
    `pending_tasks` = NULL,
    `progress_percentage` = NULL,
    `created_at` = NULL,

    #' @description
    #' Initialize a new TaskBatch class.
    #'
    #' @param id id
    #' @param name name
    #' @param species species
    #' @param total_tasks total_tasks
    #' @param completed_tasks completed_tasks
    #' @param pending_tasks pending_tasks
    #' @param progress_percentage progress_percentage
    #' @param created_at created_at
    #' @param description description
    #' @param ... Other optional arguments.
    initialize = function(`id`, `name`, `species`, `total_tasks`, `completed_tasks`, `pending_tasks`, `progress_percentage`, `created_at`, `description` = NULL, ...) {
      if (!missing(`id`)) {
        if (!(is.numeric(`id`) && length(`id`) == 1)) {
          stop(paste("Error! Invalid data for `id`. Must be an integer:", `id`))
        }
        self$`id` <- `id`
      }
      if (!missing(`name`)) {
        if (!(is.character(`name`) && length(`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", `name`))
        }
        self$`name` <- `name`
      }
      if (!missing(`species`)) {
        stopifnot(R6::is.R6(`species`))
        self$`species` <- `species`
      }
      if (!missing(`total_tasks`)) {
        if (!(is.character(`total_tasks`) && length(`total_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `total_tasks`. Must be a string:", `total_tasks`))
        }
        self$`total_tasks` <- `total_tasks`
      }
      if (!missing(`completed_tasks`)) {
        if (!(is.character(`completed_tasks`) && length(`completed_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `completed_tasks`. Must be a string:", `completed_tasks`))
        }
        self$`completed_tasks` <- `completed_tasks`
      }
      if (!missing(`pending_tasks`)) {
        if (!(is.character(`pending_tasks`) && length(`pending_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `pending_tasks`. Must be a string:", `pending_tasks`))
        }
        self$`pending_tasks` <- `pending_tasks`
      }
      if (!missing(`progress_percentage`)) {
        if (!(is.character(`progress_percentage`) && length(`progress_percentage`) == 1)) {
          stop(paste("Error! Invalid data for `progress_percentage`. Must be a string:", `progress_percentage`))
        }
        self$`progress_percentage` <- `progress_percentage`
      }
      if (!missing(`created_at`)) {
        if (!(is.character(`created_at`) && length(`created_at`) == 1)) {
          stop(paste("Error! Invalid data for `created_at`. Must be a string:", `created_at`))
        }
        self$`created_at` <- `created_at`
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
    #' @return TaskBatch as a base R list.
    #' @examples
    #' # convert array of TaskBatch (x) to a data frame
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
    #' Convert TaskBatch to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      TaskBatchObject <- list()
      if (!is.null(self$`id`)) {
        TaskBatchObject[["id"]] <-
          self$`id`
      }
      if (!is.null(self$`name`)) {
        TaskBatchObject[["name"]] <-
          self$`name`
      }
      if (!is.null(self$`description`)) {
        TaskBatchObject[["description"]] <-
          self$`description`
      }
      if (!is.null(self$`species`)) {
        TaskBatchObject[["species"]] <-
          self$`species`$toSimpleType()
      }
      if (!is.null(self$`total_tasks`)) {
        TaskBatchObject[["total_tasks"]] <-
          self$`total_tasks`
      }
      if (!is.null(self$`completed_tasks`)) {
        TaskBatchObject[["completed_tasks"]] <-
          self$`completed_tasks`
      }
      if (!is.null(self$`pending_tasks`)) {
        TaskBatchObject[["pending_tasks"]] <-
          self$`pending_tasks`
      }
      if (!is.null(self$`progress_percentage`)) {
        TaskBatchObject[["progress_percentage"]] <-
          self$`progress_percentage`
      }
      if (!is.null(self$`created_at`)) {
        TaskBatchObject[["created_at"]] <-
          self$`created_at`
      }
      return(TaskBatchObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of TaskBatch
    #'
    #' @param input_json the JSON input
    #' @return the instance of TaskBatch
    fromJSON = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      if (!is.null(this_object$`id`)) {
        self$`id` <- this_object$`id`
      }
      if (!is.null(this_object$`name`)) {
        self$`name` <- this_object$`name`
      }
      if (!is.null(this_object$`description`)) {
        self$`description` <- this_object$`description`
      }
      if (!is.null(this_object$`species`)) {
        `species_object` <- Species$new()
        `species_object`$fromJSON(jsonlite::toJSON(this_object$`species`, auto_unbox = TRUE, digits = NA))
        self$`species` <- `species_object`
      }
      if (!is.null(this_object$`total_tasks`)) {
        self$`total_tasks` <- this_object$`total_tasks`
      }
      if (!is.null(this_object$`completed_tasks`)) {
        self$`completed_tasks` <- this_object$`completed_tasks`
      }
      if (!is.null(this_object$`pending_tasks`)) {
        self$`pending_tasks` <- this_object$`pending_tasks`
      }
      if (!is.null(this_object$`progress_percentage`)) {
        self$`progress_percentage` <- this_object$`progress_percentage`
      }
      if (!is.null(this_object$`created_at`)) {
        self$`created_at` <- this_object$`created_at`
      }
      self
    },

    #' @description
    #' To JSON String
    #' 
    #' @param ... Parameters passed to `jsonlite::toJSON`
    #' @return TaskBatch in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of TaskBatch
    #'
    #' @param input_json the JSON input
    #' @return the instance of TaskBatch
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`id` <- this_object$`id`
      self$`name` <- this_object$`name`
      self$`description` <- this_object$`description`
      self$`species` <- Species$new()$fromJSON(jsonlite::toJSON(this_object$`species`, auto_unbox = TRUE, digits = NA))
      self$`total_tasks` <- this_object$`total_tasks`
      self$`completed_tasks` <- this_object$`completed_tasks`
      self$`pending_tasks` <- this_object$`pending_tasks`
      self$`progress_percentage` <- this_object$`progress_percentage`
      self$`created_at` <- this_object$`created_at`
      self
    },

    #' @description
    #' Validate JSON input with respect to TaskBatch and throw an exception if invalid
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
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `id` is missing."))
      }
      # check the required field `name`
      if (!is.null(input_json$`name`)) {
        if (!(is.character(input_json$`name`) && length(input_json$`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", input_json$`name`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `name` is missing."))
      }
      # check the required field `species`
      if (!is.null(input_json$`species`)) {
        stopifnot(R6::is.R6(input_json$`species`))
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `species` is missing."))
      }
      # check the required field `total_tasks`
      if (!is.null(input_json$`total_tasks`)) {
        if (!(is.character(input_json$`total_tasks`) && length(input_json$`total_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `total_tasks`. Must be a string:", input_json$`total_tasks`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `total_tasks` is missing."))
      }
      # check the required field `completed_tasks`
      if (!is.null(input_json$`completed_tasks`)) {
        if (!(is.character(input_json$`completed_tasks`) && length(input_json$`completed_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `completed_tasks`. Must be a string:", input_json$`completed_tasks`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `completed_tasks` is missing."))
      }
      # check the required field `pending_tasks`
      if (!is.null(input_json$`pending_tasks`)) {
        if (!(is.character(input_json$`pending_tasks`) && length(input_json$`pending_tasks`) == 1)) {
          stop(paste("Error! Invalid data for `pending_tasks`. Must be a string:", input_json$`pending_tasks`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `pending_tasks` is missing."))
      }
      # check the required field `progress_percentage`
      if (!is.null(input_json$`progress_percentage`)) {
        if (!(is.character(input_json$`progress_percentage`) && length(input_json$`progress_percentage`) == 1)) {
          stop(paste("Error! Invalid data for `progress_percentage`. Must be a string:", input_json$`progress_percentage`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `progress_percentage` is missing."))
      }
      # check the required field `created_at`
      if (!is.null(input_json$`created_at`)) {
        if (!(is.character(input_json$`created_at`) && length(input_json$`created_at`) == 1)) {
          stop(paste("Error! Invalid data for `created_at`. Must be a string:", input_json$`created_at`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for TaskBatch: the required field `created_at` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of TaskBatch
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

      # check if the required `name` is null
      if (is.null(self$`name`)) {
        return(FALSE)
      }

      if (nchar(self$`name`) > 255) {
        return(FALSE)
      }

      # check if the required `species` is null
      if (is.null(self$`species`)) {
        return(FALSE)
      }

      # check if the required `total_tasks` is null
      if (is.null(self$`total_tasks`)) {
        return(FALSE)
      }

      # check if the required `completed_tasks` is null
      if (is.null(self$`completed_tasks`)) {
        return(FALSE)
      }

      # check if the required `pending_tasks` is null
      if (is.null(self$`pending_tasks`)) {
        return(FALSE)
      }

      # check if the required `progress_percentage` is null
      if (is.null(self$`progress_percentage`)) {
        return(FALSE)
      }

      # check if the required `created_at` is null
      if (is.null(self$`created_at`)) {
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

      # check if the required `name` is null
      if (is.null(self$`name`)) {
        invalid_fields["name"] <- "Non-nullable required field `name` cannot be null."
      }

      if (nchar(self$`name`) > 255) {
        invalid_fields["name"] <- "Invalid length for `name`, must be smaller than or equal to 255."
      }

      # check if the required `species` is null
      if (is.null(self$`species`)) {
        invalid_fields["species"] <- "Non-nullable required field `species` cannot be null."
      }

      # check if the required `total_tasks` is null
      if (is.null(self$`total_tasks`)) {
        invalid_fields["total_tasks"] <- "Non-nullable required field `total_tasks` cannot be null."
      }

      # check if the required `completed_tasks` is null
      if (is.null(self$`completed_tasks`)) {
        invalid_fields["completed_tasks"] <- "Non-nullable required field `completed_tasks` cannot be null."
      }

      # check if the required `pending_tasks` is null
      if (is.null(self$`pending_tasks`)) {
        invalid_fields["pending_tasks"] <- "Non-nullable required field `pending_tasks` cannot be null."
      }

      # check if the required `progress_percentage` is null
      if (is.null(self$`progress_percentage`)) {
        invalid_fields["progress_percentage"] <- "Non-nullable required field `progress_percentage` cannot be null."
      }

      # check if the required `created_at` is null
      if (is.null(self$`created_at`)) {
        invalid_fields["created_at"] <- "Non-nullable required field `created_at` cannot be null."
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
# TaskBatch$unlock()
#
## Below is an example to define the print function
# TaskBatch$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# TaskBatch$lock()

