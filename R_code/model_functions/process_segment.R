#!/usr/bin/env Rscript
#
# Segment processing utility for reliable feature extraction
#

#' Process a single audio segment with spectro_analysis
#' 
#' This function handles a single segment, ensuring precise duration measurement
#' and proper feature extraction parameters for very short segments.
#'
#' @param file_path Full path to the WAV file
#' @param min_window_length Minimum FFT window length to use (default: 128)
#' @return Dataframe with extracted features or NULL if processing failed
process_segment <- function(file_path, min_window_length = 128) {
  # Load the audio file
  tryCatch({
    # Get the base filename without path
    file_name <- basename(file_path)
    
    # Read the wav file directly
    wav <- readWave(file_path)
    
    # Calculate precise duration based on actual samples
    duration <- length(wav@left) / wav@samp.rate
    
    # Create selection table with measured duration
    sel_table <- data.frame(
      sound.files = file_name,
      selec = 1,
      start = 0,
      end = duration  # Use exact measured duration
    )
    
    # Create warbleR selection table
    original_dir <- getwd()
    file_dir <- dirname(file_path)
    setwd(file_dir)  # Change to file directory temporarily
    
    selt <- selection_table(sel_table)
    
    # Extract features with appropriate window size for short segments
    features <- spectro_analysis(selt, bp = c(9, 200), threshold = 15, 
                              wl = min_window_length, ovlp = 50)
    
    # Restore original directory
    setwd(original_dir)
    
    # Return extracted features
    return(features)
  }, error = function(e) {
    # Log error and return NULL
    cat(sprintf("Error processing file %s: %s\n", file_path, e$message))
    return(NULL)
  })
}

#' Process multiple audio segments reliably
#'
#' @param file_paths Vector of file paths to process
#' @param min_window_length Minimum FFT window length to use
#' @return Dataframe with combined features or NULL if all processing failed
process_segments <- function(file_paths, min_window_length = 128) {
  # Process each file individually
  all_features <- NULL
  
  for (file_path in file_paths) {
    # Process single file
    features <- process_segment(file_path, min_window_length)
    
    # Add to results if successful
    if (!is.null(features)) {
      if (is.null(all_features)) {
        all_features <- features
      } else {
        all_features <- rbind(all_features, features)
      }
    }
  }
  
  return(all_features)
}