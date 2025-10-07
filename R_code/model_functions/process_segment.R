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
    
    # Adaptive parameters based on sample rate
    nyquist_freq <- sample_rate / 2
    
    # Choose appropriate parameters for different sample rates and file durations
    if (sample_rate >= 150000) {
      # High sample rate (Rousettus): optimize for speed and bat calls
      # But adapt window length based on file duration
      if (duration_sec >= 0.1) {
        adaptive_wl <- 1024  # Large window for longer files
      } else if (duration_sec >= 0.05) {
        adaptive_wl <- 512   # Medium window for medium files
      } else {
        adaptive_wl <- 256   # Smaller window for very short files
      }
      adaptive_bp <- c(1, 95)  # Very wide range (kHz) - use almost full spectrum
      adaptive_threshold <- 10  # Lower threshold for weak bat calls
    } else if (sample_rate >= 80000) {
      # Medium-high sample rate: moderate optimization
      adaptive_wl <- 512
      adaptive_bp <- c(1, nyquist_freq * 0.95 / 1000)  # Use most of available spectrum (kHz)
      adaptive_threshold <- 12
    } else {
      # Lower sample rate (Carollia/Efuscus): use original parameters
      adaptive_wl <- min_window_length  # Keep original (50)
      adaptive_bp <- c(9, 200)  # Keep original bandpass filter (kHz)
      adaptive_threshold <- 15  # Keep original threshold
    }
    
    # Final safety check: ensure window length doesn't exceed half the file length
    max_safe_wl <- n_samples / 4  # Conservative: window should be at most 1/4 of file
    if (adaptive_wl > max_safe_wl) {
      adaptive_wl <- max(50, floor(max_safe_wl))  # Use smaller window, but at least 50
    }
    
    freq_resolution <- sample_rate / adaptive_wl
    
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
    
    # Extract features with adaptive parameters based on sample rate
    # Use a specific tryCatch for spectro_analysis to catch subscript issues
    features <- tryCatch({
      # Always use bandpass filter, but with appropriate ranges for each sample rate
      spectro_analysis(selt, bp = adaptive_bp, threshold = adaptive_threshold, 
                      wl = adaptive_wl, ovlp = 50)
    }, error = function(se) {
      # Enhanced error diagnostics for subscript out of bounds
      if (grepl("subscript out of bounds", se$message, fixed = TRUE)) {
        cat(sprintf("SUBSCRIPT ERROR in %s: Duration=%.4fs, Samples=%d, Rate=%d Hz, WinLen=%d\n", 
                   file_name, duration_sec, n_samples, sample_rate, adaptive_wl))
        
        # Detailed diagnosis
        min_duration_needed <- (adaptive_wl / sample_rate) * 2  # Minimum for FFT
        if (duration_sec < min_duration_needed) {
          cat(sprintf("  Diagnosis: File too short (%.4fs) - needs minimum %.4fs for FFT window\n", 
                     duration_sec, min_duration_needed))
        } else if (n_samples < adaptive_wl) {
          cat(sprintf("  Diagnosis: Insufficient samples (%d) - needs at least %d for FFT window\n", 
                     n_samples, adaptive_wl))
        } else {
          cat(sprintf("  Diagnosis: Possible empty frequency bins in %.1f-%.1fHz range\n", 
                     adaptive_bp[1], adaptive_bp[2]))
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
