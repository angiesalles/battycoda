#!/usr/bin/env Rscript
# BattyCoda Species Lister - Usage: species("username", "password")
library(httr)
library(jsonlite)

species <- function(user, pass, url="https://your-domain.com") {
  # Create a handle that will persist cookies
  h <- handle("")
  
  # Get login page and CSRF token
  cat("Getting login page...\n")
  login_page <- GET(paste0(url, "/auth/login/"), handle=h)
  if (status_code(login_page) != 200) {
    stop("Failed to access login page. Check your URL.")
  }
  
  # Extract CSRF token
  page_content <- content(login_page, "text")
  csrf_match <- regmatches(page_content, regexpr('name="csrfmiddlewaretoken"\\s+value="([^"]+)"', page_content))
  if (length(csrf_match) == 0) stop("Could not find CSRF token")
  csrf_token <- gsub('.*value="([^"]+)".*', '\\1', csrf_match)
  
  # Login
  cat("Logging in...\n")
  login_response <- POST(paste0(url, "/auth/login/"), 
                        body=list(username=user, password=pass, csrfmiddlewaretoken=csrf_token), 
                        encode="form", handle=h)
  
  if (status_code(login_response) != 200) stop("Login failed")
  
  # Get species using same handle (cookies automatically preserved)
  cat("Fetching species...\n")
  species_response <- GET(paste0(url, "/api/species/"), handle=h)
  
  cat("API Status Code:", status_code(species_response), "\n")
  cat("Response Content-Type:", headers(species_response)$`content-type`, "\n")
  
  if (status_code(species_response) == 401) stop("Authentication failed - check username/password")
  if (status_code(species_response) != 200) stop(paste("API call failed:", status_code(species_response)))
  
  # Check if we got JSON or HTML
  content_type <- headers(species_response)$`content-type`
  if (grepl("json", content_type)) {
    # Parse as JSON
    response_content <- content(species_response, "parsed")
    if ("results" %in% names(response_content)) {
      data <- response_content$results
      cat("\nAvailable Species:\n")
      cat("ID | Name\n")
      cat("---|-----\n")
      if (length(data) == 0) {
        cat("No species found. You may need to create species first.\n")
      } else {
        for(s in data) cat(sprintf("%2d | %s\n", s$id, s$name))
      }
    } else {
      cat("Unexpected JSON structure:\n")
      str(response_content)
    }
  } else {
    # Got HTML instead of JSON - likely redirected to login
    cat("Got HTML instead of JSON - authentication may have failed\n")
    cat("This often means the API endpoint doesn't exist or auth failed\n")
    html_content <- content(species_response, "text")
    if (grepl("login", html_content, ignore.case=TRUE)) {
      cat("Response contains login form - authentication failed\n")
    }
  }
}