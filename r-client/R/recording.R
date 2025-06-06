#' Create a new Recording
#'
#' @description
#' Serializer for Recording model.
#'
#' @docType class
#' @title Recording
#' @description Recording Class
#' @format An \code{R6Class} generator object
#' @field id  integer
#' @field name Name of the recording character
#' @field description Description of the recording character [optional]
#' @field location Location where the recording was made character [optional]
#' @field recorded_date Date when the recording was made character [optional]
#' @field duration Duration of the recording in seconds numeric
#' @field sample_rate Sample rate of the recording in Hz integer
#' @field project  \link{Project}
#' @field wav_file_url  character
#' @field created_at  character
#' @importFrom R6 R6Class
#' @importFrom jsonlite fromJSON toJSON
#' @export
Recording <- R6::R6Class(
  "Recording",
  public = list(
    `id` = NULL,
    `name` = NULL,
    `description` = NULL,
    `location` = NULL,
    `recorded_date` = NULL,
    `duration` = NULL,
    `sample_rate` = NULL,
    `project` = NULL,
    `wav_file_url` = NULL,
    `created_at` = NULL,

    #' @description
    #' Initialize a new Recording class.
    #'
    #' @param id id
    #' @param name Name of the recording
    #' @param duration Duration of the recording in seconds
    #' @param sample_rate Sample rate of the recording in Hz
    #' @param project project
    #' @param wav_file_url wav_file_url
    #' @param created_at created_at
    #' @param description Description of the recording
    #' @param location Location where the recording was made
    #' @param recorded_date Date when the recording was made
    #' @param ... Other optional arguments.
    initialize = function(`id`, `name`, `duration`, `sample_rate`, `project`, `wav_file_url`, `created_at`, `description` = NULL, `location` = NULL, `recorded_date` = NULL, ...) {
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
      if (!missing(`duration`)) {
        if (!(is.numeric(`duration`) && length(`duration`) == 1)) {
          stop(paste("Error! Invalid data for `duration`. Must be a number:", `duration`))
        }
        self$`duration` <- `duration`
      }
      if (!missing(`sample_rate`)) {
        if (!(is.numeric(`sample_rate`) && length(`sample_rate`) == 1)) {
          stop(paste("Error! Invalid data for `sample_rate`. Must be an integer:", `sample_rate`))
        }
        self$`sample_rate` <- `sample_rate`
      }
      if (!missing(`project`)) {
        stopifnot(R6::is.R6(`project`))
        self$`project` <- `project`
      }
      if (!missing(`wav_file_url`)) {
        if (!(is.character(`wav_file_url`) && length(`wav_file_url`) == 1)) {
          stop(paste("Error! Invalid data for `wav_file_url`. Must be a string:", `wav_file_url`))
        }
        self$`wav_file_url` <- `wav_file_url`
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
    #' @return Recording as a base R list.
    #' @examples
    #' # convert array of Recording (x) to a data frame
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
    #' Convert Recording to a base R type
    #'
    #' @return A base R type, e.g. a list or numeric/character array.
    toSimpleType = function() {
      RecordingObject <- list()
      if (!is.null(self$`id`)) {
        RecordingObject[["id"]] <-
          self$`id`
      }
      if (!is.null(self$`name`)) {
        RecordingObject[["name"]] <-
          self$`name`
      }
      if (!is.null(self$`description`)) {
        RecordingObject[["description"]] <-
          self$`description`
      }
      if (!is.null(self$`location`)) {
        RecordingObject[["location"]] <-
          self$`location`
      }
      if (!is.null(self$`recorded_date`)) {
        RecordingObject[["recorded_date"]] <-
          self$`recorded_date`
      }
      if (!is.null(self$`duration`)) {
        RecordingObject[["duration"]] <-
          self$`duration`
      }
      if (!is.null(self$`sample_rate`)) {
        RecordingObject[["sample_rate"]] <-
          self$`sample_rate`
      }
      if (!is.null(self$`project`)) {
        RecordingObject[["project"]] <-
          self$`project`$toSimpleType()
      }
      if (!is.null(self$`wav_file_url`)) {
        RecordingObject[["wav_file_url"]] <-
          self$`wav_file_url`
      }
      if (!is.null(self$`created_at`)) {
        RecordingObject[["created_at"]] <-
          self$`created_at`
      }
      return(RecordingObject)
    },

    #' @description
    #' Deserialize JSON string into an instance of Recording
    #'
    #' @param input_json the JSON input
    #' @return the instance of Recording
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
      if (!is.null(this_object$`location`)) {
        self$`location` <- this_object$`location`
      }
      if (!is.null(this_object$`recorded_date`)) {
        self$`recorded_date` <- this_object$`recorded_date`
      }
      if (!is.null(this_object$`duration`)) {
        self$`duration` <- this_object$`duration`
      }
      if (!is.null(this_object$`sample_rate`)) {
        self$`sample_rate` <- this_object$`sample_rate`
      }
      if (!is.null(this_object$`project`)) {
        `project_object` <- Project$new()
        `project_object`$fromJSON(jsonlite::toJSON(this_object$`project`, auto_unbox = TRUE, digits = NA))
        self$`project` <- `project_object`
      }
      if (!is.null(this_object$`wav_file_url`)) {
        self$`wav_file_url` <- this_object$`wav_file_url`
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
    #' @return Recording in JSON format
    toJSONString = function(...) {
      simple <- self$toSimpleType()
      json <- jsonlite::toJSON(simple, auto_unbox = TRUE, digits = NA, ...)
      return(as.character(jsonlite::minify(json)))
    },

    #' @description
    #' Deserialize JSON string into an instance of Recording
    #'
    #' @param input_json the JSON input
    #' @return the instance of Recording
    fromJSONString = function(input_json) {
      this_object <- jsonlite::fromJSON(input_json)
      self$`id` <- this_object$`id`
      self$`name` <- this_object$`name`
      self$`description` <- this_object$`description`
      self$`location` <- this_object$`location`
      self$`recorded_date` <- this_object$`recorded_date`
      self$`duration` <- this_object$`duration`
      self$`sample_rate` <- this_object$`sample_rate`
      self$`project` <- Project$new()$fromJSON(jsonlite::toJSON(this_object$`project`, auto_unbox = TRUE, digits = NA))
      self$`wav_file_url` <- this_object$`wav_file_url`
      self$`created_at` <- this_object$`created_at`
      self
    },

    #' @description
    #' Validate JSON input with respect to Recording and throw an exception if invalid
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
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `id` is missing."))
      }
      # check the required field `name`
      if (!is.null(input_json$`name`)) {
        if (!(is.character(input_json$`name`) && length(input_json$`name`) == 1)) {
          stop(paste("Error! Invalid data for `name`. Must be a string:", input_json$`name`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `name` is missing."))
      }
      # check the required field `duration`
      if (!is.null(input_json$`duration`)) {
        if (!(is.numeric(input_json$`duration`) && length(input_json$`duration`) == 1)) {
          stop(paste("Error! Invalid data for `duration`. Must be a number:", input_json$`duration`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `duration` is missing."))
      }
      # check the required field `sample_rate`
      if (!is.null(input_json$`sample_rate`)) {
        if (!(is.numeric(input_json$`sample_rate`) && length(input_json$`sample_rate`) == 1)) {
          stop(paste("Error! Invalid data for `sample_rate`. Must be an integer:", input_json$`sample_rate`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `sample_rate` is missing."))
      }
      # check the required field `project`
      if (!is.null(input_json$`project`)) {
        stopifnot(R6::is.R6(input_json$`project`))
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `project` is missing."))
      }
      # check the required field `wav_file_url`
      if (!is.null(input_json$`wav_file_url`)) {
        if (!(is.character(input_json$`wav_file_url`) && length(input_json$`wav_file_url`) == 1)) {
          stop(paste("Error! Invalid data for `wav_file_url`. Must be a string:", input_json$`wav_file_url`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `wav_file_url` is missing."))
      }
      # check the required field `created_at`
      if (!is.null(input_json$`created_at`)) {
        if (!(is.character(input_json$`created_at`) && length(input_json$`created_at`) == 1)) {
          stop(paste("Error! Invalid data for `created_at`. Must be a string:", input_json$`created_at`))
        }
      } else {
        stop(paste("The JSON input `", input, "` is invalid for Recording: the required field `created_at` is missing."))
      }
    },

    #' @description
    #' To string (JSON format)
    #'
    #' @return String representation of Recording
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

      if (nchar(self$`location`) > 255) {
        return(FALSE)
      }

      # check if the required `project` is null
      if (is.null(self$`project`)) {
        return(FALSE)
      }

      # check if the required `wav_file_url` is null
      if (is.null(self$`wav_file_url`)) {
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

      if (nchar(self$`location`) > 255) {
        invalid_fields["location"] <- "Invalid length for `location`, must be smaller than or equal to 255."
      }

      # check if the required `project` is null
      if (is.null(self$`project`)) {
        invalid_fields["project"] <- "Non-nullable required field `project` cannot be null."
      }

      # check if the required `wav_file_url` is null
      if (is.null(self$`wav_file_url`)) {
        invalid_fields["wav_file_url"] <- "Non-nullable required field `wav_file_url` cannot be null."
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
# Recording$unlock()
#
## Below is an example to define the print function
# Recording$set("public", "print", function(...) {
#   print(jsonlite::prettify(self$toJSONString()))
#   invisible(self)
# })
## Uncomment below to lock the class to prevent modifications to the method or field
# Recording$lock()

