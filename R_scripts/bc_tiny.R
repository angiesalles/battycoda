#!/usr/bin/env Rscript
# Ultra-compact BattyCoda API - 1-liners for R
library(httr); library(jsonlite)

# Quick functions - just pass api_key and url
bc_sp <- function(key, url="https://your-domain.com") { data <- content(GET(paste0(url, "/simple-api/species/?api_key=", key))); for(s in data$species) cat(s$id, "|", s$name, "\n") }
bc_up <- function(file, species_id, key, url="https://your-domain.com") { r <- POST(paste0(url, "/simple-api/upload/"), body=list(name=tools::file_path_sans_ext(basename(file)), species_id=species_id, api_key=key, wav_file=upload_file(file)), encode="multipart"); data <- content(r); if(data$success) cat("✅ ID:", data$recording$id, "\n") else cat("❌", data$error, "\n") }

# Examples:
# bc_sp("your_api_key_here")  # List species  
# bc_up("file.wav", 1, "your_api_key_here")  # Upload file