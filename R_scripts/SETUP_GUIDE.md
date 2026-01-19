# BattyCoda Simple API Setup Guide

## Overview

This simple API approach uses **API keys** instead of complex authentication, making it super easy for R users and students.

## Setup Steps

### 1. Django Setup (Run Migration)

First, apply the database migration to add API key support:

```bash
# Run migration to add API key field
docker compose exec -T web python manage.py migrate

# Restart the web container
docker compose restart web
```

### 2. Generate API Key (Web Interface)

Users need to generate their API key through the web interface:

1. Log into BattyCoda web interface
2. Go to Profile/Settings 
3. Generate API Key (you'll need to add this to the UI)
4. Copy the API key for use in R

### 3. R Usage

#### Option A: Full-featured (bc_simple.R)
```r
source("bc_simple.R")

# List species
bc_species(api_key="your_api_key_here", url="https://yourdomain.com")

# Upload a file
bc_upload("recording.wav", species_id=1, api_key="your_api_key_here")

# Bulk upload a folder
bc_bulk_upload("path/to/folder", species_id=1, api_key="your_api_key_here")
```

#### Option B: Ultra-compact (bc_tiny.R)
```r
source("bc_tiny.R")

# List species
bc_sp("your_api_key_here")

# Upload file  
bc_up("file.wav", 1, "your_api_key_here")
```

## API Endpoints Available

- `GET /simple-api/species/?api_key=KEY` - List species
- `GET /simple-api/projects/?api_key=KEY` - List projects  
- `GET /simple-api/recordings/?api_key=KEY` - List recordings
- `POST /simple-api/upload/` - Upload recording (with api_key in form data)
- `GET /simple-api/user/?api_key=KEY` - Get user info

## Benefits of This Approach

✅ **No complex authentication** - just an API key  
✅ **Works remotely** - no need to be on the server  
✅ **Super simple R code** - easy for students  
✅ **Easy to understand** - clear error messages  
✅ **Secure** - API keys can be revoked/regenerated  

## For Students

1. Get your API key from the web interface
2. Update the URL in the R script to your BattyCoda domain
3. Use the simple functions:
   ```r
   # Set your details
   MY_KEY <- "your_api_key_here"
   MY_URL <- "https://yourdomain.com"
   
   # List what's available
   bc_species(MY_KEY, MY_URL)
   
   # Upload a file
   bc_upload("my_recording.wav", species_id=1, MY_KEY, url=MY_URL)
   ```

## Next Steps

1. Add API key generation to the web UI (user profile page)
2. Test the endpoints work correctly
3. Update the domain URLs in the R scripts
4. Share the R scripts with students

This approach is much cleaner than web scraping and much simpler than complex OAuth!