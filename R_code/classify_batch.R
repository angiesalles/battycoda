#!/usr/bin/env Rscript
#
# Script to classify batch segments using the trained model
#

# Load libraries
library(warbleR)
library(stringr)
library(mlr3)
library(mlr3learners)
library(kknn)

# Load common utilities and model runner
source("/app/R_code/model_functions/utils_module.R")
source("/app/R_code/model_functions/model_runner.R")

# Path to the model and batch folder
model_path <- "/app/data/models/carollia_lda_model_new.RData"
batch_folder <- "/app/batch_0_168"

# Function to classify batch segments
classify_batch <- function(batch_folder, model_path, output_file = NULL) {
  cat(sprintf("Classifying segments in %s using model %s\n", batch_folder, model_path))
  
  # Run the model on the batch folder
  results <- run_model(batch_folder, model_path, "lda")
  
  if (results$status != "success") {
    stop(sprintf("Classification failed: %s", results$status))
  }
  
  cat(sprintf("Successfully processed %d files\n", results$processed_files))
  
  # Prepare a detailed summary of results
  summary_lines <- c()
  summary_lines <- c(summary_lines, sprintf("Classification results for batch %s", basename(batch_folder)))
  summary_lines <- c(summary_lines, "")
  summary_lines <- c(summary_lines, "Overall summary:")
  
  # Add summary information
  for (class_name in names(results$summary)) {
    count <- results$summary[[class_name]]$count
    percent <- results$summary[[class_name]]$percent
    summary_lines <- c(summary_lines, sprintf("  %s: %d files (%.1f%%)", class_name, count, percent))
  }
  
  summary_lines <- c(summary_lines, "")
  summary_lines <- c(summary_lines, "Individual file results:")
  summary_lines <- c(summary_lines, "")
  
  # Add detailed file results
  for (file_name in names(results$file_results)) {
    result <- results$file_results[[file_name]]
    pred_class <- result$predicted_class
    confidence <- result$confidence
    
    # Add individual file result
    summary_lines <- c(summary_lines, sprintf("File: %s", file_name))
    summary_lines <- c(summary_lines, sprintf("  Prediction: %s (%.1f%% confidence)", pred_class, confidence))
    
    # Add probability details
    summary_lines <- c(summary_lines, "  Class probabilities:")
    for (class_name in names(result$class_probabilities)) {
      prob <- result$class_probabilities[[class_name]]
      summary_lines <- c(summary_lines, sprintf("    %s: %.2f%%", class_name, prob))
    }
    summary_lines <- c(summary_lines, "")
  }
  
  # Write to file or console
  if (!is.null(output_file)) {
    writeLines(summary_lines, output_file)
    cat(sprintf("Results written to: %s\n", output_file))
  } else {
    cat(paste(summary_lines, collapse = "\n"))
  }
  
  # Return the results
  return(results)
}

# Main execution
output_file <- "/app/data/batch_0_168_classification_results.txt"
results <- classify_batch(batch_folder, model_path, output_file)

# Create a simple CSV with just the file names and predictions
csv_file <- "/app/data/batch_0_168_predictions.csv"
csv_data <- data.frame(
  file_name = character(),
  predicted_class = character(),
  confidence = numeric(),
  stringsAsFactors = FALSE
)

for (file_name in names(results$file_results)) {
  result <- results$file_results[[file_name]]
  row <- data.frame(
    file_name = file_name,
    predicted_class = result$predicted_class,
    confidence = result$confidence,
    stringsAsFactors = FALSE
  )
  csv_data <- rbind(csv_data, row)
}

# Write the CSV file
write.csv(csv_data, file = csv_file, row.names = FALSE)
cat(sprintf("CSV predictions written to: %s\n", csv_file))

# Print summary statistics
cat("\nCall type distribution:\n")
for (class_name in names(results$summary)) {
  count <- results$summary[[class_name]]$count
  percent <- results$summary[[class_name]]$percent
  cat(sprintf("%s: %d files (%.1f%%)\n", class_name, count, percent))
}