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
#' @param min_window_length Minimum FFT window length to use (default: 50)
#' @return Dataframe with extracted features or NULL if processing failed
process_segment <- function(file_path, min_window_length = 50) {
  # Load the audio file
  tryCatch({
    # Get the base filename without path
    file_name <- basename(file_path)
    
    # Read the wav file directly
    wav <- readWave(file_path)
    
    # Enhanced diagnostics - gather audio file information
    sample_rate <- wav@samp.rate
    n_samples <- length(wav@left)
    duration_sec <- n_samples / sample_rate
    bit_depth <- wav@bit
    
    # Log file stats for extremely short files (potential problem source)
    if (duration_sec < 0.001) {  # Less than 1ms
      cat(sprintf("WARNING: Very short audio file %s - Duration: %.6f sec, Samples: %d, Rate: %d Hz\n", 
                 file_name, duration_sec, n_samples, sample_rate))
    }
    
    # Check for empty or near-silent files
    if (n_samples < 10) {
      cat(sprintf("ERROR: File %s has insufficient audio data - only %d samples\n", file_name, n_samples))
      return(NULL)
    }
    
    # Calculate frequency resolution
    freq_resolution <- sample_rate / min_window_length
    
    # Check if bandpass filter range (9-200 Hz) is appropriate for this sample rate
    nyquist_freq <- sample_rate / 2
    if (nyquist_freq < 200) {
      cat(sprintf("WARNING: File %s has Nyquist frequency %.1f Hz - below upper bandpass limit of 200 Hz\n", 
                 file_name, nyquist_freq))
    }
    
    # Create selection table with measured duration
    sel_table <- data.frame(
      sound.files = file_name,
      selec = 1,
      start = 0,
      end = duration_sec  # Use exact measured duration
    )
    
    # Create warbleR selection table
    original_dir <- getwd()
    file_dir <- dirname(file_path)
    setwd(file_dir)  # Change to file directory temporarily
    
    # Use verbose=FALSE to suppress validation messages
    selt <- selection_table(sel_table, verbose = FALSE)
    
    # Extract features with appropriate window size for short segments
    # Use a specific tryCatch for spectro_analysis to catch subscript issues
    features <- tryCatch({
      spectro_analysis(selt, bp = c(9, 200), threshold = 15, 
                      wl = min_window_length, ovlp = 50)
    }, error = function(se) {
      # Enhanced error diagnostics for subscript out of bounds
      if (grepl("subscript out of bounds", se$message, fixed = TRUE)) {
        cat(sprintf("SUBSCRIPT ERROR in %s: Duration=%.4fs, Samples=%d, Rate=%d Hz, WinLen=%d\n", 
                   file_name, duration_sec, n_samples, sample_rate, min_window_length))
        
        # Detailed diagnosis
        min_duration_needed <- (min_window_length / sample_rate) * 2  # Minimum for FFT
        if (duration_sec < min_duration_needed) {
          cat(sprintf("  Diagnosis: File too short (%.4fs) - needs minimum %.4fs for FFT window\n", 
                     duration_sec, min_duration_needed))
        } else if (n_samples < min_window_length) {
          cat(sprintf("  Diagnosis: Insufficient samples (%d) - needs at least %d for FFT window\n", 
                     n_samples, min_window_length))
        } else {
          cat(sprintf("  Diagnosis: Possible empty frequency bins in %.1f-200Hz range\n", 9.0))
        }
      }
      # Rethrow the error to be caught by outer tryCatch
      stop(se$message)
    })
    
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
