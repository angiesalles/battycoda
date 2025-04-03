#!/usr/bin/env Rscript
#
# Model Runner Module - Unified interface for running classifier models
#

# Load required packages
library(warbleR)
library(stringr)
library(mlr3)
library(mlr3learners)
library(kknn)  # For KNN

# Load common utilities
source("model_functions/utils_module.R")

# KNN model runner
run_knn_model <- function(wav_folder, model_path) {
  # Load the model
  debug_log(sprintf("Loading KNN model from %s", model_path))
  model_env <- load_model(model_path)
  
  # Check if we have the necessary model objects
  if (!exists("kknn_model", envir = model_env) || !exists("levels", envir = model_env)) {
    stop("Invalid model file: missing required objects")
  }
  
  # Extract model components
  kknn_model <- model_env$kknn_model
  levels <- model_env$levels
  
  debug_log(sprintf("KNN model loaded successfully. Call types: %s", paste(levels, collapse=", ")))
  
  # Extract features from all WAV files
  debug_log(sprintf("Processing WAV files in folder: %s", wav_folder))
  batch_results <- extract_features_batch(wav_folder)
  ftable <- batch_results$features
  
  # Check if we got features
  if (nrow(ftable) == 0) {
    stop("No features extracted from WAV files")
  }
  
  # Prepare data for prediction (remove first column with filenames)
  pred_data <- ftable[, -1]
  file_info <- ftable[, 1, drop=FALSE]
  
  # Make predictions
  debug_log("Making KNN predictions...")
  if ("predict_newdata" %in% names(kknn_model)) {
    # Using mlr3 model
    predictions <- kknn_model$predict_newdata(pred_data)
    
    # Get probability matrix for all classes
    prob_matrix <- predictions$prob
    
    # Get predicted classes
    pred_classes <- as.character(predictions$response)
    
    # Format and return results
    return(format_prediction_results(file_info, pred_classes, prob_matrix, "KNN"))
  } else {
    # Fallback error if mlr3 model isn't available
    stop("Model type not supported. Please use an mlr3 model.")
  }
}

# LDA model runner
run_lda_model <- function(wav_folder, model_path) {
  # Load the model
  debug_log(sprintf("Loading LDA model from %s", model_path))
  model_env <- load_model(model_path)
  
  # Check if we have the necessary model objects
  if (!exists("lda_model_info", envir = model_env)) {
    stop("Invalid model file: missing required lda_model_info object")
  }
  
  # Extract model components with debug info
  lda_model_info <- model_env$lda_model_info
  debug_log(sprintf("LDA model_info type: %s", class(lda_model_info)))
  
  # Ensure we have a proper list object
  if (!is.list(lda_model_info)) {
    stop(sprintf("lda_model_info is not a list but a %s", class(lda_model_info)))
  }
  
  # Debug model component structure
  debug_log(sprintf("LDA model_info components: %s", paste(names(lda_model_info), collapse=", ")))
  
  # Extract components safely
  lda_model <- lda_model_info$model
  levels <- lda_model_info$levels
  feature_means <- lda_model_info$feature_means
  feature_sds <- lda_model_info$feature_sds
  
  debug_log(sprintf("LDA model loaded successfully. Call types: %s", paste(levels, collapse=", ")))
  
  # Extract features from all WAV files
  debug_log(sprintf("Processing WAV files in folder: %s", wav_folder))
  batch_results <- extract_features_batch(wav_folder)
  ftable <- batch_results$features
  
  # Check if we got features
  if (nrow(ftable) == 0) {
    stop("No features extracted from WAV files")
  }
  
  # Prepare data for prediction (remove first column with filenames)
  file_info <- ftable[, 1, drop=FALSE]
  pred_data <- ftable[, -1]
  
  # Scale features using the same parameters as during training
  for (col in colnames(pred_data)) {
    if (col %in% names(feature_means) && col %in% names(feature_sds)) {
      pred_data[[col]] <- (pred_data[[col]] - feature_means[col]) / feature_sds[col]
    } else {
      # If for some reason this column wasn't in training, use basic scaling
      pred_data[[col]] <- scale(pred_data[[col]])
    }
  }
  
  # Make predictions using the standard MASS LDA model (not MLR3)
  debug_log("Making LDA predictions...")
  tryCatch({
    # Debug lda_model structure
    debug_log(sprintf("LDA model class: %s", class(lda_model)))
    
    # Use standard predict() function from MASS package
    debug_log("Calling predict() on LDA model...")
    predictions <- predict(lda_model, newdata = as.data.frame(pred_data))
    
    # Debug predictions structure
    debug_log(sprintf("Predictions class: %s", class(predictions)))
    debug_log(sprintf("Predictions components: %s", 
                     ifelse(is.list(predictions), 
                           paste(names(predictions), collapse=", "), 
                           "NOT A LIST")))
    
    # Get predicted classes
    debug_log("Extracting predicted classes...")
    if (!is.list(predictions)) {
      # If predictions is not a list, handle it differently
      debug_log("Predictions is not a list, creating manual structure")
      # Create predictions structure manually based on output
      debug_log(sprintf("Predictions is a %s, handling accordingly", class(predictions)[1]))
      
      # Handle factor type predictions
      if (is.factor(predictions)) {
        pred_classes <- as.character(predictions)
        debug_log(sprintf("Converted factor to character vector, classes: %s", 
                         paste(unique(pred_classes), collapse=", ")))
        
        # Create a probability matrix with 1.0 for predicted class
        prob_matrix <- matrix(0, nrow=length(pred_classes), ncol=length(levels))
        colnames(prob_matrix) <- levels
        
        # Set 1.0 probability for predicted class
        for (i in 1:length(pred_classes)) {
          col_idx <- which(levels == pred_classes[i])
          if (length(col_idx) > 0) {
            prob_matrix[i, col_idx] <- 1.0
          }
        }
        debug_log("Created probability matrix with 1.0 for predicted classes")
      }
      # Handle other vector types
      else if (is.vector(predictions)) {
        pred_classes <- predictions
        debug_log(sprintf("Using vector directly, classes: %s", 
                         paste(unique(pred_classes), collapse=", ")))
        
        # Create a probability matrix with 1.0 for predicted class
        prob_matrix <- matrix(0, nrow=length(pred_classes), ncol=length(levels))
        colnames(prob_matrix) <- levels
        
        # Set 1.0 probability for predicted class
        for (i in 1:length(pred_classes)) {
          col_idx <- which(levels == pred_classes[i])
          if (length(col_idx) > 0) {
            prob_matrix[i, col_idx] <- 1.0
          }
        }
      } 
      # If it's something else we don't expect
      else {
        stop(sprintf("Predictions has unexpected format: %s", class(predictions)[1]))
      }
    } else {
      # Normal extraction from list
      pred_classes <- predictions$class
      prob_matrix <- predictions$posterior
    }
    
    # Debug output to help diagnose any issues
    debug_log(paste("Prediction successful. Classes:", length(pred_classes), 
                   "First few classes:", paste(head(pred_classes), collapse=", ")))
    if (!is.null(dim(prob_matrix))) {
      debug_log(paste("Probabilities matrix dimensions:", dim(prob_matrix)[1], "x", dim(prob_matrix)[2]))
    } else {
      debug_log("Warning: prob_matrix has no dimensions")
    }
  }, error = function(e) {
    # Log the error details for debugging
    debug_log(paste("Error in LDA prediction:", e$message))
    stop(paste("Error in LDA prediction:", e$message))
  })
  
  # Format and return results
  return(format_prediction_results(file_info, pred_classes, prob_matrix, "LDA"))
}

# Unified model running interface
run_model <- function(wav_folder, model_path, model_type = NULL) {
  # If model_type is not specified, try to autodetect
  if (is.null(model_type)) {
    # Load model to check its contents
    model_env <- load_model(model_path)
    
    if (exists("kknn_model", envir = model_env)) {
      model_type <- "knn"
    } else if (exists("lda_model_info", envir = model_env)) {
      model_type <- "lda"
    } else {
      stop("Could not determine model type. Please specify model_type parameter.")
    }
  }
  
  # Call appropriate model runner
  if (model_type == "knn") {
    return(run_knn_model(wav_folder, model_path))
  } else if (model_type == "lda") {
    return(run_lda_model(wav_folder, model_path))
  } else {
    stop(paste("Unsupported model type:", model_type))
  }
}