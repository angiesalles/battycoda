#!/usr/bin/env Rscript
# BattyCoda WAV Uploader - Usage: upload("file.wav", "username", "password", species_id=1)
library(httr)
library(tools)

upload <- function(wav_path, user, pass, species_id, name=NULL, url="https://your-domain.com") {
  # Check file exists
  if (!file.exists(wav_path)) stop("File not found: ", wav_path)
  if (is.null(name)) name <- file_path_sans_ext(basename(wav_path))
  
  # Get login page and CSRF token
  cat("Getting login page...\n")
  login_page <- GET(paste0(url, "/auth/login/"))
  if (status_code(login_page) != 200) stop("Failed to access login page")
  
  page_content <- content(login_page, "text")
  csrf_match <- regmatches(page_content, regexpr('name="csrfmiddlewaretoken"\\s+value="([^"]+)"', page_content))
  if (length(csrf_match) == 0) stop("Could not find CSRF token")
  csrf_token <- gsub('.*value="([^"]+)".*', '\\1', csrf_match)
  
  # Login
  cat("Logging in...\n")
  login_response <- POST(paste0(url, "/auth/login/"), 
                        body=list(username=user, password=pass, csrfmiddlewaretoken=csrf_token), 
                        encode="form")
  if (status_code(login_response) != 200) stop("Login failed")
  
  # Upload file
  cat("Uploading", basename(wav_path), "...\n")
  upload_response <- POST(paste0(url, "/api/recordings/"),
                         body=list(name=name, species_id=species_id, wav_file=upload_file(wav_path)),
                         encode="multipart",
                         set_cookies(.cookies=cookies(login_response)))
  
  if (status_code(upload_response) == 201) {
    result <- content(upload_response)
    cat("✅ Success! Recording ID:", result$id, "\n")
    return(result)
  } else {
    cat("❌ Upload failed. Status:", status_code(upload_response), "\n")
    cat("Error:", content(upload_response, "text"), "\n")
    return(NULL)
  }
}