#!/usr/bin/env Rscript
#
# Train a new LDA model for Rousettus using existing training data
#

# Set working directory to the R_code folder
setwd("/app/R_code")

# Load required modules
source("model_functions/utils_module.R")
source("model_functions/model_trainer.R")

# Define parameters
data_folder <- "/app/R_code/model_functions/training_Rousettus"
output_model_path <- "/app/data/models/rousettus_lda_model.RData"
test_split <- 0.2

# Print configuration
cat("=== Training new Rousettus LDA model ===\n")
cat("Data folder: ", data_folder, "\n")
cat("Output model path: ", output_model_path, "\n")
cat("Test split: ", test_split, "\n\n")

# Train LDA model
cat("Starting LDA model training...\n")
result <- tryCatch({
  train_model(data_folder, output_model_path, test_split, "lda")
}, error = function(e) {
  cat("ERROR in LDA training:", e$message, "\n")
  return(list(
    status = "error",
    message = paste("Error in LDA training:", e$message)
  ))
})

# Print results
cat("\n=== Training Results ===\n")
cat("Status: ", result$status, "\n")
if (result$status == "success") {
  cat("Model path: ", result$model_path, "\n")
  cat("Model type: ", result$model_type, "\n")
  cat("Accuracy: ", sprintf("%.2f%%", result$accuracy), "\n")
  cat("Classes: ", paste(unlist(result$classes), collapse=", "), "\n")
  cat("Files used - Total: ", result$file_counts$total, 
      ", Training: ", result$file_counts$training, 
      ", Testing: ", result$file_counts$testing, "\n")
} else {
  cat("Error message: ", result$message, "\n")
}