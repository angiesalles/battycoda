#!/usr/bin/env Rscript
#
# Common Utilities Module - Shared functions for bat call processing
#

# Load required packages for feature extraction
library(warbleR)
library(stringr)

# Debug logging function
debug_log <- function(...) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  message <- paste(...)
  cat(sprintf("[DEBUG %s] %s\n", timestamp, message))
}

# Function to extract acoustic features from a folder of WAV files
extract_features_batch <- function(wav_folder) {
  # Verify folder exists
  if (!dir.exists(wav_folder)) {
    stop(paste("WAV folder not found:", wav_folder))
  }
  
  # Get list of WAV files
  original_dir <- getwd()
  on.exit(setwd(original_dir))  # Ensure we return to original directory
  
  setwd(wav_folder)
  wav_files <- list.files(pattern = "\\.wav$")
  
  if (length(wav_files) == 0) {
    stop(paste("No WAV files found in folder:", wav_folder))
  }
  
  debug_log(sprintf("Found %d WAV files in %s", length(wav_files), wav_folder))
  
  # Create selection table for all files
  # We'll use 0 to end of file for all files
  selec <- seq_along(wav_files)
  start <- rep(0, length(wav_files))
  end <- rep(0, length(wav_files))  # Will be filled with exact durations
  
  wavtable <- cbind.data.frame(sound.files = wav_files, selec = selec, start = start, end = end)
  
  # Get actual length of sound files - use full Wave object for precision
  for (i in 1:nrow(wavtable)) {
    tryCatch({
      # Read full wave file for precise duration calculation
      wav <- readWave(wavtable[i,1])
      # Calculate exact duration based on actual samples
      exact_duration <- length(wav@left) / wav@samp.rate
      # Update end time with precise duration
      wavtable[i,4] <- exact_duration
      if (i %% 10 == 0) {
        debug_log(sprintf("Processed %d/%d files", i, nrow(wavtable)))
      }
    }, error = function(e) {
      warning(paste("Error processing file", wavtable[i,1], ":", e$message))
      # Keep default end value for problematic files
    })
  }
  
  # Create selection table with error handling
  debug_log("Creating selection table...")
  tryCatch({
    selt <- selection_table(wavtable)
    
    # Extract features using reliable segment processor
    debug_log("Extracting acoustic features...")
    
    # Load segment processor functions with absolute path to the R code directory
    processor_path <- "/app/R_code/model_functions/process_segment.R"
    source(processor_path)
    
    # Get full file paths for processing
    current_dir <- getwd()
    file_paths <- file.path(current_dir, selt$sound.files)
    
    # Process all files using our robust processor
    debug_log("Using robust segment processor for feature extraction")
    all_features <- process_segments(file_paths)
    
    # Check if any features were extracted
    if (is.null(all_features) || nrow(all_features) == 0) {
      stop("Failed to extract features from any files")
    }
    
    debug_log(sprintf("Successfully extracted features from %d files", nrow(all_features)))
    
    # Return to original directory
    setwd(original_dir)
    return(list(features = all_features, files = wav_files))
    
  }, error = function(e) {
    # Set directory back before propagating error
    setwd(original_dir)
    stop(paste("Error in feature extraction:", e$message))
  })
}

# Common function to load any model from file
load_model <- function(model_path) {
  if (!file.exists(model_path)) {
    stop(paste("Model file not found:", model_path))
  }
  
  # Load the model
  model_env <- new.env()
  load(model_path, envir = model_env)
  
  # Return the model objects
  return(model_env)
}

# Format prediction results consistently
format_prediction_results <- function(file_info, pred_classes, prob_matrix, model_type) {
  # Prepare results
  results <- list()
  
  for (i in 1:nrow(prob_matrix)) {
    file_name <- as.character(file_info[i, 1])
    
    # Get probabilities for this file
    file_probs <- as.list(prob_matrix[i, ])
    
    # Calculate confidence
    pred_class <- as.character(pred_classes[i])
    confidence <- file_probs[[pred_class]] * 100
    
    # Format probabilities as percentages
    prob_percents <- lapply(file_probs, function(x) x * 100)
    
    # Add to results
    results[[file_name]] <- list(
      file_name = file_name,
      predicted_class = pred_class,
      confidence = confidence,
      class_probabilities = prob_percents
    )
  }
  
  # Calculate summary statistics
  class_counts <- table(pred_classes)
  class_percents <- (class_counts / length(pred_classes)) * 100
  
  # Format summary
  summary <- list()
  for (class_name in names(class_counts)) {
    summary[[class_name]] <- list(
      count = as.integer(class_counts[class_name]),
      percent = class_percents[class_name]
    )
  }
  
  # Return combined results
  return(list(
    status = "success",
    model_type = model_type,
    processed_files = length(pred_classes),
    summary = summary,
    file_results = results
  ))
}