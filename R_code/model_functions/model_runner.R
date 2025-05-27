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
run_knn_model <- function(wav_folder, model_path, export_features_path = NULL) {
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
  
  # Export features if requested
  if (!is.null(export_features_path)) {
    debug_log(sprintf("Exporting features to: %s", export_features_path))
    write.csv(ftable, file = export_features_path, row.names = FALSE)
  }
  
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
run_lda_model <- function(wav_folder, model_path, export_features_path = NULL) {
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
  
  # Export features if requested
  if (!is.null(export_features_path)) {
    debug_log(sprintf("Exporting features to: %s", export_features_path))
    write.csv(ftable, file = export_features_path, row.names = FALSE)
  }
  
  # Check if we got features
  if (nrow(ftable) == 0) {
    stop("No features extracted from WAV files")
  }
  
  # Prepare data for prediction (remove first column with filenames)
  file_info <- ftable[, 1, drop=FALSE]
  pred_data <- ftable[, -1]
  
  # Handle missing values first, then scale features
  # Get feature columns (all except 'selec' if it exists)
  feature_cols <- colnames(pred_data)
  if ('selec' %in% feature_cols) {
    feature_cols <- setdiff(feature_cols, 'selec')
  }
  
  # First, handle missing values - just like in the trainer
  missing_counts <- sapply(pred_data[feature_cols], function(x) sum(is.na(x)))
  if (sum(missing_counts) > 0) {
    debug_log(sprintf("Found %d missing values across %d columns. Imputing...", 
                     sum(missing_counts), sum(missing_counts > 0)))
    
    # Impute missing values with means from the training data
    for (col in feature_cols) {
      if (sum(is.na(pred_data[[col]])) > 0) {
        # Use feature mean from training if available
        if (col %in% names(feature_means)) {
          impute_value <- feature_means[col]
          debug_log(sprintf("Imputing %d missing values in '%s' with %.4f from training", 
                           sum(is.na(pred_data[[col]])), col, impute_value))
        } else {
          # Calculate column mean if not available from training
          impute_value <- mean(pred_data[[col]], na.rm = TRUE)
          if (is.na(impute_value)) impute_value <- 0 # Fallback if all values are NA
          debug_log(sprintf("Imputing %d missing values in '%s' with %.4f (calculated)", 
                           sum(is.na(pred_data[[col]])), col, impute_value))
        }
        
        # Replace missing values
        pred_data[[col]][is.na(pred_data[[col]])] <- impute_value
      }
    }
  }
  
  # Now scale features using the same parameters as during training
  for (col in colnames(pred_data)) {
    if (col %in% names(feature_means) && col %in% names(feature_sds)) {
      pred_data[[col]] <- (pred_data[[col]] - feature_means[col]) / feature_sds[col]
    } else if (col != 'selec') {
      # If for some reason this column wasn't in training, use basic scaling
      pred_data[[col]] <- scale(pred_data[[col]])
    }
  }
  
  # Make predictions using the mlr3 model
  debug_log("Making LDA predictions...")
  tryCatch({
    # Debug lda_model structure
    debug_log(sprintf("LDA model class: %s", class(lda_model)))
    
    # Use mlr3 predict_newdata method
    debug_log("Calling predict_newdata() on LDA model...")
    predictions <- lda_model$predict_newdata(as.data.frame(pred_data))
    
    # Debug predictions structure
    debug_log(sprintf("Predictions class: %s", class(predictions)))
    if ("prob" %in% names(predictions)) {
      debug_log(sprintf("Probability matrix dimensions: %d x %d", 
               nrow(predictions$prob), ncol(predictions$prob)))
    }
    
    # Extract class predictions and probabilities from mlr3 prediction object
    pred_classes <- as.character(predictions$response)
    prob_matrix <- predictions$prob
    
    debug_log(sprintf("Extracted %d predictions with %d probability classes", 
              length(pred_classes), ncol(prob_matrix)))
    
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
run_model <- function(wav_folder, model_path, model_type = NULL, export_features_path = NULL) {
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
    return(run_knn_model(wav_folder, model_path, export_features_path))
  } else if (model_type == "lda") {
    return(run_lda_model(wav_folder, model_path, export_features_path))
  } else {
    stop(paste("Unsupported model type:", model_type))
  }
}