#!/usr/bin/env Rscript
#
# BattyCoda Duplicate Segmentation Manager
# 
# This script helps Jessica identify and manage duplicate segmentation runs.
# It connects to the BattyCoda API to find segmentations with identical settings
# and provides options to delete older duplicates while keeping the newest ones.
#
# Author: Claude (AI Assistant)
# Created for: Jessica's duplicate segmentation management request

# Load required libraries
library(httr)
library(jsonlite)
library(dplyr)
library(lubridate)

# Configuration
BATTYCODA_BASE_URL <- "https://your-battycoda-domain.com"  # Update this!
API_KEY <- Sys.getenv("BATTYCODA_API_KEY")  # Set this environment variable

# Helper function to authenticate and get session cookies
authenticate_session <- function(username, password) {
  # Get CSRF token first
  csrf_response <- GET(paste0(BATTYCODA_BASE_URL, "/auth/login/"))
  csrf_token <- content(csrf_response, "text") %>%
    stringr::str_extract('name="csrfmiddlewaretoken"\\s+value="([^"]+)"') %>%
    stringr::str_extract('[^"]+$')
  
  # Login with credentials
  login_response <- POST(
    paste0(BATTYCODA_BASE_URL, "/auth/login/"),
    body = list(
      username = username,
      password = password,
      csrfmiddlewaretoken = csrf_token
    ),
    encode = "form",
    add_headers(
      "Referer" = paste0(BATTYCODA_BASE_URL, "/auth/login/"),
      "User-Agent" = "BattyCoda-R-Script/1.0"
    )
  )
  
  if (status_code(login_response) == 200) {
    cat("✓ Authentication successful\n")
    return(cookies(login_response))
  } else {
    stop("Authentication failed. Please check your credentials.")
  }
}

# Function to get all recordings accessible to the user
get_all_recordings <- function(session_cookies) {
  cat("Fetching recordings...\n")
  
  all_recordings <- list()
  page <- 1
  
  repeat {
    response <- GET(
      paste0(BATTYCODA_BASE_URL, "/api/recordings/"),
      query = list(page = page),
      add_headers(
        "User-Agent" = "BattyCoda-R-Script/1.0"
      ),
      set_cookies(.cookies = session_cookies)
    )
    
    if (status_code(response) != 200) {
      warning(paste("Failed to fetch recordings page", page))
      break
    }
    
    data <- content(response, "parsed")
    
    if (length(data$results) == 0) {
      break
    }
    
    all_recordings <- c(all_recordings, data$results)
    
    if (is.null(data$`next`)) {
      break
    }
    
    page <- page + 1
  }
  
  cat(paste("✓ Found", length(all_recordings), "recordings\n"))
  return(all_recordings)
}

# Function to get segmentations for a specific recording (via Django shell)
get_recording_segmentations <- function(recording_id, session_cookies) {
  # Since the API doesn't expose Segmentation objects directly,
  # we'll need to use a custom endpoint or Django shell access
  # For now, we'll simulate this with a theoretical API endpoint
  
  response <- GET(
    paste0(BATTYCODA_BASE_URL, "/api/recordings/", recording_id, "/segmentations/"),
    add_headers("User-Agent" = "BattyCoda-R-Script/1.0"),
    set_cookies(.cookies = session_cookies)
  )
  
  if (status_code(response) == 200) {
    return(content(response, "parsed"))
  } else {
    # If the endpoint doesn't exist, return empty list
    # In practice, you'd need to implement this endpoint in Django
    warning(paste("Could not fetch segmentations for recording", recording_id))
    return(list())
  }
}

# Function to identify duplicate segmentations
identify_duplicate_segmentations <- function(segmentations) {
  if (length(segmentations) <= 1) {
    return(list())
  }
  
  # Convert to data frame for easier manipulation
  seg_df <- do.call(rbind, lapply(segmentations, function(seg) {
    data.frame(
      id = seg$id,
      recording_id = seg$recording_id,
      algorithm_id = ifelse(is.null(seg$algorithm), NA, seg$algorithm$id),
      algorithm_name = ifelse(is.null(seg$algorithm), "Manual", seg$algorithm$name),
      min_duration_ms = seg$min_duration_ms,
      smooth_window = seg$smooth_window,
      threshold_factor = seg$threshold_factor,
      created_at = as.POSIXct(seg$created_at, format = "%Y-%m-%dT%H:%M:%OSZ"),
      name = seg$name,
      status = seg$status,
      manually_edited = seg$manually_edited,
      segments_created = seg$segments_created,
      stringsAsFactors = FALSE
    )
  }))
  
  # Group by algorithm and parameters to find duplicates
  duplicate_groups <- seg_df %>%
    group_by(
      recording_id, 
      algorithm_id, 
      min_duration_ms, 
      smooth_window, 
      threshold_factor
    ) %>%
    filter(n() > 1) %>%
    arrange(desc(created_at)) %>%
    group_split()
  
  return(duplicate_groups)
}

# Function to analyze and summarize duplicates
analyze_duplicates <- function(recordings, session_cookies) {
  cat("Analyzing segmentations for duplicates...\n")
  
  all_duplicates <- list()
  summary_stats <- list(
    total_recordings = length(recordings),
    recordings_with_duplicates = 0,
    total_duplicate_groups = 0,
    total_duplicate_segmentations = 0,
    potential_space_savings = 0
  )
  
  for (recording in recordings) {
    segmentations <- get_recording_segmentations(recording$id, session_cookies)
    
    if (length(segmentations) > 1) {
      duplicates <- identify_duplicate_segmentations(segmentations)
      
      if (length(duplicates) > 0) {
        summary_stats$recordings_with_duplicates <- summary_stats$recordings_with_duplicates + 1
        summary_stats$total_duplicate_groups <- summary_stats$total_duplicate_groups + length(duplicates)
        
        for (dup_group in duplicates) {
          summary_stats$total_duplicate_segmentations <- 
            summary_stats$total_duplicate_segmentations + (nrow(dup_group) - 1)  # -1 because we keep the newest
          
          all_duplicates[[length(all_duplicates) + 1]] <- list(
            recording_name = recording$name,
            recording_id = recording$id,
            duplicates = dup_group
          )
        }
      }
    }
  }
  
  return(list(
    duplicates = all_duplicates,
    summary = summary_stats
  ))
}

# Function to display duplicate analysis results
display_duplicate_analysis <- function(analysis_results) {
  cat("\n" %>% rep(2) %>% paste(collapse = ""))
  cat("=== DUPLICATE SEGMENTATION ANALYSIS ===\n")
  cat("========================================\n\n")
  
  summary <- analysis_results$summary
  
  cat("Summary Statistics:\n")
  cat(paste("• Total recordings analyzed:", summary$total_recordings, "\n"))
  cat(paste("• Recordings with duplicates:", summary$recordings_with_duplicates, "\n"))
  cat(paste("• Total duplicate groups found:", summary$total_duplicate_groups, "\n"))
  cat(paste("• Total duplicate segmentations:", summary$total_duplicate_segmentations, "\n"))
  
  if (summary$total_duplicate_segmentations > 0) {
    cat(paste("• Segmentations that could be removed:", summary$total_duplicate_segmentations, "\n"))
  }
  
  cat("\n")
  
  if (length(analysis_results$duplicates) > 0) {
    cat("Detailed Duplicate Groups:\n")
    cat("-" %>% rep(25) %>% paste(collapse = "") %>% paste0("\n"))
    
    for (i in seq_along(analysis_results$duplicates)) {
      dup_info <- analysis_results$duplicates[[i]]
      dup_group <- dup_info$duplicates
      
      cat(paste0("\n", i, ". Recording: ", dup_info$recording_name, "\n"))
      cat(paste("   Algorithm:", dup_group$algorithm_name[1], "\n"))
      cat(paste("   Parameters: min_duration =", dup_group$min_duration_ms[1], 
                "ms, smooth_window =", dup_group$smooth_window[1],
                ", threshold_factor =", dup_group$threshold_factor[1], "\n"))
      cat(paste("   Duplicate segmentations found:", nrow(dup_group), "\n"))
      
      cat("   Details:\n")
      for (j in 1:nrow(dup_group)) {
        row <- dup_group[j, ]
        status_icon <- if (j == 1) "✓ KEEP" else "✗ DELETE"
        cat(paste0("     ", status_icon, " ID:", row$id, 
                   " | Created:", format(row$created_at, "%Y-%m-%d %H:%M"), 
                   " | Status:", row$status,
                   " | Segments:", row$segments_created, 
                   " | Name: '", row$name, "'\n"))
      }
    }
  }
}

# Function to delete duplicate segmentations (keeping the newest)
delete_duplicate_segmentations <- function(analysis_results, session_cookies, dry_run = TRUE) {
  if (length(analysis_results$duplicates) == 0) {
    cat("No duplicates found to delete.\n")
    return()
  }
  
  if (dry_run) {
    cat("\n=== DRY RUN MODE (No actual deletions) ===\n")
  } else {
    cat("\n=== DELETING DUPLICATE SEGMENTATIONS ===\n")
  }
  
  total_deleted <- 0
  
  for (dup_info in analysis_results$duplicates) {
    dup_group <- dup_info$duplicates
    
    # Skip the first (newest) segmentation, delete the rest
    for (i in 2:nrow(dup_group)) {
      seg_id <- dup_group$id[i]
      seg_name <- dup_group$name[i]
      
      if (dry_run) {
        cat(paste("Would delete segmentation ID:", seg_id, "- Name:", seg_name, "\n"))
      } else {
        # Actual deletion via API (if endpoint exists)
        # Note: You'll need to implement a DELETE endpoint for segmentations
        delete_response <- DELETE(
          paste0(BATTYCODA_BASE_URL, "/api/segmentations/", seg_id, "/"),
          add_headers("User-Agent" = "BattyCoda-R-Script/1.0"),
          set_cookies(.cookies = session_cookies)
        )
        
        if (status_code(delete_response) == 204) {
          cat(paste("✓ Deleted segmentation ID:", seg_id, "- Name:", seg_name, "\n"))
          total_deleted <- total_deleted + 1
        } else {
          cat(paste("✗ Failed to delete segmentation ID:", seg_id, "- Name:", seg_name, "\n"))
        }
      }
    }
  }
  
  if (!dry_run) {
    cat(paste("\nTotal segmentations deleted:", total_deleted, "\n"))
  }
}

# Main function
main <- function() {
  cat("BattyCoda Duplicate Segmentation Manager\n")
  cat("=======================================\n\n")
  
  # Check for required environment variables
  if (BATTYCODA_BASE_URL == "https://your-battycoda-domain.com") {
    cat("⚠ Please update BATTYCODA_BASE_URL in the script with your actual domain.\n")
    return()
  }
  
  # Get credentials
  cat("Please enter your BattyCoda credentials:\n")
  username <- readline(prompt = "Username: ")
  password <- getPass::getPass(prompt = "Password: ")
  
  # Authenticate
  tryCatch({
    session_cookies <- authenticate_session(username, password)
  }, error = function(e) {
    cat("Authentication failed:", e$message, "\n")
    return()
  })
  
  # Get all recordings
  recordings <- get_all_recordings(session_cookies)
  
  if (length(recordings) == 0) {
    cat("No recordings found. Nothing to analyze.\n")
    return()
  }
  
  # Analyze for duplicates
  analysis_results <- analyze_duplicates(recordings, session_cookies)
  
  # Display results
  display_duplicate_analysis(analysis_results)
  
  # Ask user what they want to do
  if (analysis_results$summary$total_duplicate_segmentations > 0) {
    cat("\nWhat would you like to do?\n")
    cat("1. Dry run (show what would be deleted)\n")
    cat("2. Actually delete duplicates (keeping newest)\n")
    cat("3. Exit without changes\n")
    
    choice <- readline(prompt = "Enter choice (1-3): ")
    
    if (choice == "1") {
      delete_duplicate_segmentations(analysis_results, session_cookies, dry_run = TRUE)
    } else if (choice == "2") {
      cat("\n⚠ WARNING: This will permanently delete duplicate segmentations!\n")
      confirm <- readline(prompt = "Type 'YES' to confirm: ")
      
      if (confirm == "YES") {
        delete_duplicate_segmentations(analysis_results, session_cookies, dry_run = FALSE)
      } else {
        cat("Operation cancelled.\n")
      }
    } else {
      cat("Exiting without changes.\n")
    }
  }
  
  cat("\nDone!\n")
}

# Helper function to set up the script for Jessica
setup_script <- function() {
  cat("BattyCoda Duplicate Segmentation Manager - Setup\n")
  cat("==============================================\n\n")
  
  cat("This script helps you identify and remove duplicate segmentation runs.\n")
  cat("Before using it, you need to:\n\n")
  
  cat("1. Update the BATTYCODA_BASE_URL variable in this script\n")
  cat("2. Install required R packages:\n")
  cat("   install.packages(c('httr', 'jsonlite', 'dplyr', 'lubridate', 'getPass'))\n\n")
  
  cat("3. Note: This script requires API endpoints that may need to be added to BattyCoda:\n")
  cat("   - GET /api/recordings/{id}/segmentations/\n")
  cat("   - DELETE /api/segmentations/{id}/\n\n")
  
  cat("Once setup is complete, run: main()\n")
}

# Export functions for interactive use
if (!interactive()) {
  # If running as script, show setup instructions
  setup_script()
} else {
  # If in interactive mode, you can call main() directly
  cat("Script loaded. Call main() to start or setup_script() for instructions.\n")
}