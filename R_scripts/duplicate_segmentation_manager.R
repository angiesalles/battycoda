#!/usr/bin/env Rscript
#
# BattyCoda Duplicate Segmentation Manager
# 
# This script helps Jessica identify and manage duplicate segmentation runs using
# the BattyCoda API. It provides a clean interface to find and optionally delete
# duplicate segmentations while keeping the newest ones.
#
# Usage:
#   1. Set your BattyCoda domain in the BATTYCODA_BASE_URL variable
#   2. Run the script and provide your login credentials
#   3. The script will find duplicates and offer options to delete them
#
# Author: Claude (AI Assistant)
# Created for: Jessica's duplicate segmentation management request

# Load required libraries
suppressPackageStartupMessages({
  if (!require(httr)) stop("Please install httr package: install.packages('httr')")
  if (!require(jsonlite)) stop("Please install jsonlite package: install.packages('jsonlite')")
  if (!require(dplyr)) stop("Please install dplyr package: install.packages('dplyr')")
  if (!require(getPass)) stop("Please install getPass package: install.packages('getPass')")
})

# Configuration - UPDATE THIS WITH YOUR DOMAIN
BATTYCODA_BASE_URL <- "https://your-battycoda-domain.com"  # CHANGE THIS!

# Global variable to store session cookies
session_cookies <- NULL

# Helper function to authenticate and get session cookies
authenticate_session <- function(username, password) {
  cat("🔐 Authenticating...\n")
  
  # Get login page to extract CSRF token
  login_page <- GET(paste0(BATTYCODA_BASE_URL, "/auth/login/"))
  
  if (status_code(login_page) != 200) {
    stop("Failed to access login page. Please check your BATTYCODA_BASE_URL.")
  }
  
  # Extract CSRF token from the login page
  page_content <- content(login_page, "text")
  csrf_pattern <- 'name="csrfmiddlewaretoken"\\s+value="([^"]+)"'
  csrf_match <- regmatches(page_content, regexpr(csrf_pattern, page_content))
  
  if (length(csrf_match) == 0) {
    stop("Could not find CSRF token on login page.")
  }
  
  csrf_token <- gsub('.*value="([^"]+)".*', '\\1', csrf_match)
  
  # Perform login
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
      "User-Agent" = "BattyCoda-R-DuplicateManager/1.0"
    ),
    handle = handle("")
  )
  
  # Check if login was successful by looking at the response
  if (status_code(login_response) == 200 && 
      !grepl("login", content(login_response, "text"), ignore.case = TRUE)) {
    cat("✅ Authentication successful!\n")
    return(cookies(login_response))
  } else {
    stop("❌ Authentication failed. Please check your username and password.")
  }
}

# Function to make authenticated API requests
api_request <- function(endpoint, method = "GET", body = NULL) {
  url <- paste0(BATTYCODA_BASE_URL, "/api/", endpoint)
  
  if (method == "GET") {
    response <- GET(
      url,
      add_headers("User-Agent" = "BattyCoda-R-DuplicateManager/1.0"),
      set_cookies(.cookies = session_cookies)
    )
  } else if (method == "DELETE") {
    response <- DELETE(
      url,
      add_headers("User-Agent" = "BattyCoda-R-DuplicateManager/1.0"),
      set_cookies(.cookies = session_cookies)
    )
  } else if (method == "POST") {
    response <- POST(
      url,
      body = body,
      encode = "json",
      add_headers(
        "User-Agent" = "BattyCoda-R-DuplicateManager/1.0",
        "Content-Type" = "application/json"
      ),
      set_cookies(.cookies = session_cookies)
    )
  }
  
  if (status_code(response) == 401) {
    stop("❌ Unauthorized. Please check your authentication.")
  }
  
  return(response)
}

# Function to get duplicate segmentations
get_duplicate_segmentations <- function() {
  cat("🔍 Searching for duplicate segmentations...\n")
  
  response <- api_request("segmentations/duplicates/")
  
  if (status_code(response) != 200) {
    stop(paste("Failed to get duplicates:", status_code(response)))
  }
  
  duplicates_data <- content(response, "parsed")
  
  cat(paste("✅ Found", duplicates_data$total_groups, "groups with", 
            duplicates_data$total_duplicates, "duplicate segmentations\n"))
  
  return(duplicates_data)
}

# Function to display duplicate analysis
display_duplicates <- function(duplicates_data) {
  if (duplicates_data$total_groups == 0) {
    cat("\n🎉 No duplicate segmentations found!\n")
    cat("All your segmentations have unique settings.\n")
    return(FALSE)
  }
  
  cat("\n")
  cat("=" %>% rep(50) %>% paste(collapse = ""), "\n")
  cat("  DUPLICATE SEGMENTATION ANALYSIS\n")
  cat("=" %>% rep(50) %>% paste(collapse = ""), "\n\n")
  
  cat("📊 Summary:\n")
  cat(paste("   • Duplicate groups found:", duplicates_data$total_groups, "\n"))
  cat(paste("   • Total segmentations that could be removed:", duplicates_data$total_duplicates, "\n"))
  cat(paste("   • Potential space/cleanup benefit: Significant\n\n"))
  
  cat("📋 Detailed Analysis:\n")
  cat("-" %>% rep(50) %>% paste(collapse = ""), "\n\n")
  
  for (i in seq_along(duplicates_data$duplicate_groups)) {
    group <- duplicates_data$duplicate_groups[[i]]
    
    cat(paste0("Group ", i, ": ", group$recording_name, "\n"))
    cat(paste("   Algorithm:", group$algorithm_name, "\n"))
    cat(paste("   Parameters: min_duration =", group$parameters$min_duration_ms, 
              "ms, smooth_window =", group$parameters$smooth_window,
              ", threshold =", group$parameters$threshold_factor, "\n"))
    cat(paste("   Duplicates found:", length(group$duplicates), "\n"))
    
    cat("   Details:\n")
    for (j in seq_along(group$duplicates)) {
      dup <- group$duplicates[[j]]
      status_icon <- if (j == 1) "✅ KEEP  " else "❌ DELETE"
      
      # Parse and format the creation date
      created_date <- as.POSIXct(dup$created_at, format = "%Y-%m-%dT%H:%M:%OSZ")
      formatted_date <- format(created_date, "%Y-%m-%d %H:%M")
      
      # Additional flags
      flags <- c()
      if (dup$is_active) flags <- c(flags, "ACTIVE")
      if (dup$manually_edited) flags <- c(flags, "EDITED")
      flag_str <- if (length(flags) > 0) paste0(" [", paste(flags, collapse = ","), "]") else ""
      
      cat(paste0("     ", status_icon, " ID:", sprintf("%3d", dup$id), 
                 " | ", formatted_date,
                 " | Status: ", dup$status,
                 " | Segments: ", dup$segments_count,
                 " | By: ", dup$created_by_username,
                 flag_str,
                 " | '", dup$name, "'\n"))
    }
    cat("\n")
  }
  
  return(TRUE)
}

# Function to delete duplicate segmentations
delete_duplicates <- function(duplicates_data, dry_run = TRUE) {
  if (duplicates_data$total_groups == 0) {
    return()
  }
  
  mode_text <- if (dry_run) "🧪 DRY RUN MODE" else "🗑️  DELETION MODE"
  cat(paste("\n", mode_text, "\n"))
  cat("=" %>% rep(50) %>% paste(collapse = ""), "\n")
  
  if (dry_run) {
    cat("This is a dry run - no actual deletions will be performed.\n")
  } else {
    cat("⚠️  WARNING: This will permanently delete segmentations!\n")
  }
  cat("\n")
  
  total_to_delete <- 0
  total_deleted <- 0
  
  for (group in duplicates_data$duplicate_groups) {
    # Skip the first (newest) segmentation in each group
    duplicates_to_delete <- group$duplicates[2:length(group$duplicates)]
    total_to_delete <- total_to_delete + length(duplicates_to_delete)
    
    cat(paste0("Group: ", group$recording_name, " - ", group$algorithm_name, "\n"))
    
    for (dup in duplicates_to_delete) {
      created_date <- as.POSIXct(dup$created_at, format = "%Y-%m-%dT%H:%M:%OSZ")
      formatted_date <- format(created_date, "%Y-%m-%d %H:%M")
      
      if (dry_run) {
        cat(paste0("   Would delete: ID ", dup$id, " - '", dup$name, 
                   "' (", formatted_date, ")\n"))
      } else {
        cat(paste0("   Deleting: ID ", dup$id, " - '", dup$name, 
                   "' (", formatted_date, ")... "))
        
        tryCatch({
          delete_response <- api_request(paste0("segmentations/", dup$id, "/"), method = "DELETE")
          
          if (status_code(delete_response) == 204) {
            cat("✅ Success\n")
            total_deleted <- total_deleted + 1
          } else {
            cat(paste("❌ Failed (HTTP", status_code(delete_response), ")\n"))
          }
        }, error = function(e) {
          cat(paste("❌ Error:", e$message, "\n"))
        })
      }
    }
    cat("\n")
  }
  
  if (dry_run) {
    cat(paste("📋 Summary: Would delete", total_to_delete, "segmentations\n"))
  } else {
    cat(paste("📋 Summary: Successfully deleted", total_deleted, "out of", total_to_delete, "segmentations\n"))
  }
}

# Function to show prevention tips
show_prevention_tips <- function() {
  cat("\n")
  cat("💡 TIPS TO PREVENT FUTURE DUPLICATES\n")
  cat("=" %>% rep(40) %>% paste(collapse = ""), "\n\n")
  
  cat("1. 🏷️  USE DESCRIPTIVE NAMES:\n")
  cat("   Instead of: 'Segmentation 1', 'Test', 'New segmentation'\n")
  cat("   Use: 'Threshold_0.5_MinDur_10ms', 'Manual_Edit_2024-01-15'\n\n")
  
  cat("2. 🔍 CHECK EXISTING SEGMENTATIONS:\n")
  cat("   Before creating new segmentations, review existing ones\n")
  cat("   for the same recording with similar parameters.\n\n")
  
  cat("3. ♻️  REUSE OR UPDATE:\n")
  cat("   Instead of creating new segmentations with minor changes,\n")
  cat("   consider updating the name of existing ones to reflect\n")
  cat("   parameter changes.\n\n")
  
  cat("4. 🗂️  ORGANIZE BY PURPOSE:\n")
  cat("   Use naming conventions like:\n")
  cat("   'Experiment_A_v1', 'Final_Settings', 'Test_LowThreshold'\n\n")
  
  cat("5. 🔄 USE THIS SCRIPT REGULARLY:\n")
  cat("   Run this duplicate finder periodically to keep your\n")
  cat("   segmentations organized and save storage space.\n\n")
}

# Main execution function
main <- function() {
  cat("BattyCoda Duplicate Segmentation Manager\n")
  cat("=======================================\n\n")
  
  # Check configuration
  if (BATTYCODA_BASE_URL == "https://your-battycoda-domain.com") {
    cat("❌ Configuration Error:\n")
    cat("   Please update BATTYCODA_BASE_URL in this script with your actual domain.\n")
    cat("   Example: BATTYCODA_BASE_URL <- \"https://battycoda.example.com\"\n")
    return(invisible())
  }
  
  cat("This script will help you find and manage duplicate segmentation runs.\n")
  cat("Duplicates are defined as segmentations with identical:\n")
  cat("• Recording • Algorithm • Parameters (min_duration, smooth_window, threshold)\n\n")
  
  # Get credentials
  username <- readline(prompt = "👤 Username: ")
  password <- getPass("🔑 Password: ")
  
  # Authenticate
  tryCatch({
    session_cookies <<- authenticate_session(username, password)
  }, error = function(e) {
    cat("❌ Authentication failed:", e$message, "\n")
    return(invisible())
  })
  
  # Get duplicates
  tryCatch({
    duplicates_data <- get_duplicate_segmentations()
  }, error = function(e) {
    cat("❌ Failed to get duplicates:", e$message, "\n")
    return(invisible())
  })
  
  # Display results
  has_duplicates <- display_duplicates(duplicates_data)
  
  if (!has_duplicates) {
    show_prevention_tips()
    return(invisible())
  }
  
  # Interactive menu
  repeat {
    cat("\n🤔 What would you like to do?\n")
    cat("1. 🧪 Dry run (show what would be deleted)\n")
    cat("2. 🗑️  Delete duplicates (keeping newest in each group)\n")
    cat("3. 💡 Show prevention tips\n")
    cat("4. 🚪 Exit\n")
    
    choice <- readline(prompt = "Enter choice (1-4): ")
    
    if (choice == "1") {
      delete_duplicates(duplicates_data, dry_run = TRUE)
    } else if (choice == "2") {
      cat("\n⚠️  FINAL WARNING: This will permanently delete duplicate segmentations!\n")
      cat("The NEWEST segmentation in each group will be kept.\n")
      confirm <- readline(prompt = "Type 'DELETE' to confirm: ")
      
      if (confirm == "DELETE") {
        delete_duplicates(duplicates_data, dry_run = FALSE)
        cat("\n✅ Deletion complete! Consider running the script again to verify.\n")
        break
      } else {
        cat("❌ Deletion cancelled.\n")
      }
    } else if (choice == "3") {
      show_prevention_tips()
    } else if (choice == "4") {
      cat("👋 Goodbye!\n")
      break
    } else {
      cat("❌ Invalid choice. Please enter 1, 2, 3, or 4.\n")
    }
  }
}

# Helper function for setup instructions
setup_instructions <- function() {
  cat("BattyCoda Duplicate Segmentation Manager - Setup\n")
  cat("==============================================\n\n")
  
  cat("📋 Before using this script:\n\n")
  
  cat("1. 🔧 INSTALL REQUIRED R PACKAGES:\n")
  cat("   install.packages(c('httr', 'jsonlite', 'dplyr', 'getPass'))\n\n")
  
  cat("2. ⚙️  UPDATE CONFIGURATION:\n")
  cat("   Edit this script and change BATTYCODA_BASE_URL to your domain\n")
  cat("   Example: BATTYCODA_BASE_URL <- \"https://battycoda.example.com\"\n\n")
  
  cat("3. 🚀 RUN THE SCRIPT:\n")
  cat("   main()  # Start the interactive duplicate manager\n\n")
  
  cat("4. 🔐 AUTHENTICATION:\n")
  cat("   You'll need your BattyCoda username and password\n\n")
  
  cat("5. ✨ NEW API ENDPOINTS:\n")
  cat("   This script uses new API endpoints for segmentation management:\n")
  cat("   • GET /api/segmentations/duplicates/ - Find duplicates\n")
  cat("   • DELETE /api/segmentations/{id}/ - Delete a segmentation\n")
  cat("   • GET /api/recordings/{id}/segmentations/ - Get recording segmentations\n\n")
  
  cat("💡 The script provides safe duplicate detection and optional deletion,\n")
  cat("   always keeping the newest segmentation in each duplicate group.\n")
}

# Export the main function and show setup if running non-interactively
if (!interactive()) {
  setup_instructions()
} else {
  cat("🚀 BattyCoda Duplicate Segmentation Manager loaded!\n")
  cat("   Call main() to start, or setup_instructions() for help.\n")
}