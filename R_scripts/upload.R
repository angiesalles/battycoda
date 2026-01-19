#!/usr/bin/env Rscript
# Ultra-compact BattyCoda uploader - Usage: upload("file.wav", "username", "password", species_id=1)
library(httr)
upload <- function(wav_path, user, pass, species_id, name=tools::file_path_sans_ext(basename(wav_path)), url="https://your-domain.com") {
  csrf <- sub('.*value="([^"]+)".*', '\\1', content(GET(paste0(url, "/auth/login/")), "text"))
  session <- cookies(POST(paste0(url, "/auth/login/"), body=list(username=user, password=pass, csrfmiddlewaretoken=csrf), encode="form"))
  result <- POST(paste0(url, "/api/recordings/"), body=list(name=name, species_id=species_id, wav_file=upload_file(wav_path)), encode="multipart", set_cookies(.cookies=session))
  if(status_code(result)==201) cat("✅ Uploaded:", content(result)$id, "\n") else cat("❌ Failed:", status_code(result), "\n")
  return(content(result))
}
# Example: upload("recording.wav", "myuser", "mypass", species_id=1)