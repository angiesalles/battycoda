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
  end <- rep(1, length(wav_files))  # Default 1 second, will be updated
  
  wavtable <- cbind.data.frame(sound.files = wav_files, selec = selec, start = start, end = end)
  
  # Get actual length of sound files
  for (i in 1:nrow(wavtable)) {
    tryCatch({
      audio <- readWave(wavtable[i,1], header=TRUE)
      audiolength <- (audio$samples / audio$sample.rate)
      wavtable[i,4] <- audiolength
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
    
    # Extract features - maintain consistent parameters
    debug_log("Extracting acoustic features...")
    
    # We'll process files in smaller batches to skip problematic ones
    # while keeping the same parameters for all files
    all_features <- NULL
    batch_size <- 100
    num_files <- nrow(selt)
    
    # Process in batches
    for (i in seq(1, num_files, by=batch_size)) {
      end_idx <- min(i + batch_size - 1, num_files)
      current_batch <- selt[i:end_idx,]
      
      debug_log(sprintf("Processing batch %d-%d of %d files", i, end_idx, num_files))
      
      # Try to process this batch and catch errors
      batch_features <- tryCatch({
        spectro_analysis(current_batch, bp = c(9, 200), threshold = 15)
      }, error = function(e) {
        # If the entire batch fails, try one by one
        debug_log(sprintf("Error in batch %d-%d: %s", i, end_idx, e$message))
        debug_log("Processing files individually...")
        
        individual_features <- NULL
        
        for (j in i:end_idx) {
          single_file <- selt[j,,drop=FALSE]
          tryCatch({
            # Process individual file
            file_features <- spectro_analysis(single_file, bp = c(9, 200), threshold = 15)
            
            # Append to results
            if (is.null(individual_features)) {
              individual_features <- file_features
            } else {
              individual_features <- rbind(individual_features, file_features)
            }
          }, error = function(e2) {
            debug_log(sprintf("Skipping problematic file %s: %s", selt$sound.files[j], e2$message))
            # Skip this file and continue
          })
        }
        
        return(individual_features)
      })
      
      # Append batch results to the full results
      if (!is.null(batch_features) && nrow(batch_features) > 0) {
        if (is.null(all_features)) {
          all_features <- batch_features
        } else {
          all_features <- rbind(all_features, batch_features)
        }
      }
    }
    
    # Ensure we got some features
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