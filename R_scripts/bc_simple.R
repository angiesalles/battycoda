#!/usr/bin/env Rscript
#
# BattyCoda Simple API - Super clean R interface
# 
# Usage:
#   bc_species(api_key="your_key", url="https://yourdomain.com")
#   bc_upload("file.wav", api_key="your_key", species_id=1)

library(httr)
library(jsonlite)

# List available species
bc_species <- function(api_key, url="https://your-domain.com") {
  response <- GET(paste0(url, "/simple-api/species/?api_key=", api_key))
  
  cat("Status Code:", status_code(response), "\n")
  cat("Content-Type:", headers(response)$`content-type`, "\n")
  
  if (status_code(response) != 200) {
    cat("Error:", status_code(response), "-", content(response, "text"), "\n")
    return(NULL)
  }
  
  # Check if we got JSON or HTML
  content_type <- headers(response)$`content-type`
  if (is.null(content_type) || !grepl("json", content_type)) {
    cat("Got non-JSON response. Content:\n")
    cat(substr(content(response, "text"), 1, 500), "\n")
    return(NULL)
  }
  
  data <- content(response, "parsed")
  cat("Parsed data structure:\n")
  str(data)
  
  if (!is.null(data$success) && data$success) {
    cat("Available Species:\n")
    cat("ID | Name\n")
    cat("---|-----\n")
    for(s in data$species) {
      cat(sprintf("%2d | %s\n", s$id, s$name))
    }
    return(data$species)
  } else {
    cat("Error:", if(!is.null(data$error)) data$error else "Unknown error", "\n")
    return(NULL)
  }
}

# List available projects
bc_projects <- function(api_key, url="https://your-domain.com") {
  response <- GET(paste0(url, "/simple-api/projects/?api_key=", api_key))
  
  if (status_code(response) != 200) {
    cat("Error:", status_code(response), "-", content(response, "text"), "\n")
    return(NULL)
  }
  
  data <- content(response, "parsed")
  if (data$success) {
    cat("Available Projects:\n")
    cat("ID | Name | Species\n")
    cat("---|------|--------\n")
    for(p in data$projects) {
      cat(sprintf("%2d | %s | %s\n", p$id, p$name, p$species_name))
    }
    return(data$projects)
  } else {
    cat("Error:", data$error, "\n")
    return(NULL)
  }
}

# List recordings
bc_recordings <- function(api_key, url="https://your-domain.com") {
  response <- GET(paste0(url, "/simple-api/recordings/?api_key=", api_key))
  
  if (status_code(response) != 200) {
    cat("Error:", status_code(response), "-", content(response, "text"), "\n")
    return(NULL)
  }
  
  data <- content(response, "parsed")
  if (data$success) {
    cat("Your Recordings:\n")
    cat("ID | Name | Duration | Species\n")
    cat("---|------|----------|--------\n")
    for(r in data$recordings) {
      duration_str <- if (is.null(r$duration)) "Unknown" else paste0(round(r$duration, 1), "s")
      cat(sprintf("%2d | %s | %s | %s\n", r$id, r$name, duration_str, r$species_name))
    }
    return(data$recordings)
  } else {
    cat("Error:", data$error, "\n")
    return(NULL)
  }
}

# Upload a recording
bc_upload <- function(wav_path, species_id, api_key, name=NULL, project_id=NULL, 
                     location=NULL, recorded_date=NULL, url="https://your-domain.com") {
  
  # Check file exists
  if (!file.exists(wav_path)) {
    cat("Error: File not found:", wav_path, "\n")
    return(NULL)
  }
  
  # Auto-generate name if not provided
  if (is.null(name)) {
    name <- tools::file_path_sans_ext(basename(wav_path))
  }
  
  cat("Uploading:", basename(wav_path), "->", name, "\n")
  
  # Prepare form data
  body_data <- list(
    name = name,
    species_id = species_id,
    api_key = api_key,
    wav_file = upload_file(wav_path)
  )
  
  # Add optional fields
  if (!is.null(project_id)) body_data$project_id <- project_id
  if (!is.null(location)) body_data$location <- location
  if (!is.null(recorded_date)) body_data$recorded_date <- recorded_date
  
  # Upload
  response <- POST(paste0(url, "/simple-api/upload/"), 
                  body = body_data, 
                  encode = "multipart")
  
  data <- content(response, "parsed")
  
  if (status_code(response) == 200 && data$success) {
    cat("✅ Upload successful! Recording ID:", data$recording$id, "\n")
    return(data$recording)
  } else {
    cat("❌ Upload failed:", data$error, "\n")
    return(NULL)
  }
}

# Get user info
bc_user <- function(api_key, url="https://your-domain.com") {
  response <- GET(paste0(url, "/simple-api/user/?api_key=", api_key))
  
  if (status_code(response) != 200) {
    cat("Error:", status_code(response), "-", content(response, "text"), "\n")
    return(NULL)
  }
  
  data <- content(response, "parsed")
  if (data$success) {
    user <- data$user
    cat("User Info:\n")
    cat("Username:", user$username, "\n")
    cat("Group:", user$group_name, "\n")
    cat("Admin:", user$is_group_admin, "\n")
    cat("API Key Active:", user$api_key_active, "\n")
    return(user)
  } else {
    cat("Error:", data$error, "\n")
    return(NULL)
  }
}

# Bulk upload directory
bc_bulk_upload <- function(directory, species_id, api_key, project_id=NULL, 
                          pattern="\\.wav$", url="https://your-domain.com") {
  
  # Find WAV files
  wav_files <- list.files(directory, pattern=pattern, ignore.case=TRUE, full.names=TRUE)
  
  if (length(wav_files) == 0) {
    cat("❌ No WAV files found in", directory, "\n")
    return(invisible())
  }
  
  cat("📂 Found", length(wav_files), "WAV files to upload\n")
  
  results <- list()
  success_count <- 0
  
  for (i in seq_along(wav_files)) {
    cat("\n[", i, "/", length(wav_files), "] ")
    
    result <- bc_upload(
      wav_path = wav_files[i],
      species_id = species_id,
      api_key = api_key,
      project_id = project_id,
      url = url
    )
    
    if (!is.null(result)) {
      success_count <- success_count + 1
      results[[length(results) + 1]] <- result
    }
    
    # Small delay to be nice to the server
    Sys.sleep(0.5)
  }
  
  cat("\n📊 Upload Summary:", success_count, "successful,", 
      length(wav_files) - success_count, "failed\n")
  
  return(results)
}

cat("📡 BattyCoda Simple API loaded!\n")
cat("Usage:\n")
cat("  bc_species(api_key)           - List species\n")
cat("  bc_projects(api_key)          - List projects\n") 
cat("  bc_recordings(api_key)        - List recordings\n")
cat("  bc_upload(file, species_id, api_key) - Upload file\n")
cat("  bc_bulk_upload(dir, species_id, api_key) - Upload folder\n")
cat("  bc_user(api_key)             - User info\n")