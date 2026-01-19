#!/usr/bin/env Rscript
#
# Script to evaluate the Carollia LDA model on training data
#

# No need to change directories - we'll use absolute paths

# Load libraries and modules
library(warbleR)
library(stringr)
library(mlr3)
library(mlr3learners)
library(kknn)

# Load common utilities using absolute paths
source("/app/R_code/model_functions/utils_module.R")
source("/app/R_code/model_functions/model_runner.R")

#' Evaluate the Carollia model performance on its training dataset
#'
#' @param model_path Path to the saved model file (.RData)
#' @param data_folder Path to folder containing the Carollia WAV files
#' @param output_file Path to save the evaluation report (default: NULL for console)
#' @return List containing evaluation metrics
evaluate_carollia_model <- function(model_path, data_folder, output_file = NULL) {
  # Verify folder exists
  if (!dir.exists(data_folder)) {
    stop(paste("Data folder not found:", data_folder))
  }
  
  # Verify model exists
  if (!file.exists(model_path)) {
    stop(paste("Model file not found:", model_path))
  }
  
  cat(sprintf("Evaluating LDA model on %s\n", data_folder))
  
  # Save original working directory
  original_dir <- getwd()
  on.exit(setwd(original_dir))  # Ensure we return to original directory
  
  # Change to data folder
  setwd(data_folder)
  
  # Get list of WAV files
  sound.files <- list.files(pattern = "\\.wav$")
  if (length(sound.files) == 0) {
    stop("No WAV files found in the specified folder")
  }
  
  cat(sprintf("Found %d WAV files for evaluation\n", length(sound.files)))
  
  # Extract true labels from filenames (assuming format: NUMBER_LABEL.wav)
  true_labels <- sapply(strsplit(sound.files, "_"), function(x) {
    if (length(x) >= 2) {
      # Join all parts after the first underscore
      label_parts <- x[2:length(x)]
      label <- paste(label_parts, collapse="_")
      # Remove .wav extension
      gsub("\\.wav$", "", label)
    } else {
      "Unknown"
    }
  })
  
  # Count instances of each class
  class_counts <- table(true_labels)
  cat("Class distribution in evaluation dataset:\n")
  for (class_name in names(class_counts)) {
    cat(sprintf("  %s: %d files\n", class_name, class_counts[class_name]))
  }
  
  # Use all files for evaluation
  eval_files <- sound.files
  eval_labels <- true_labels
  eval_folder <- data_folder
  
  cat(sprintf("Using all %d files for evaluation\n", length(eval_files)))
  
  # Run the model on the evaluation set
  cat("Running LDA model on evaluation set...\n")
  model_results <- run_model(eval_folder, model_path, "lda")
  
  cat(sprintf("Model ran successfully on %d files\n", model_results$processed_files))
  
  # Extract predictions
  predictions <- list()
  pred_classes <- c()
  
  for (i in 1:length(eval_files)) {
    file_name <- eval_files[i]
    if (file_name %in% names(model_results$file_results)) {
      result <- model_results$file_results[[file_name]]
      pred_classes[i] <- result$predicted_class
      
      # Store detailed prediction
      predictions[[file_name]] <- list(
        file_name = file_name,
        true_label = eval_labels[i],
        predicted_label = result$predicted_class,
        confidence = result$confidence,
        probabilities = result$class_probabilities
      )
    } else {
      cat(sprintf("Warning: No prediction found for file %s\n", file_name))
      # Use a placeholder for missing predictions
      pred_classes[i] <- NA
    }
  }
  
  # Remove any NA predictions
  valid_indices <- !is.na(pred_classes)
  if (sum(!valid_indices) > 0) {
    cat(sprintf("Warning: %d files had no predictions and will be excluded\n", 
               sum(!valid_indices)))
  }
  
  pred_classes <- pred_classes[valid_indices]
  true_classes <- eval_labels[valid_indices]
  
  # Calculate overall accuracy
  correct <- sum(pred_classes == true_classes)
  total <- length(pred_classes)
  accuracy <- correct / total
  
  cat(sprintf("Overall accuracy: %.2f%% (%d/%d correct)\n", 
             accuracy * 100, correct, total))
  
  # Create confusion matrix
  conf_matrix <- table(Actual = true_classes, Predicted = pred_classes)
  
  # Calculate per-class metrics
  class_metrics <- list()
  all_classes <- union(unique(true_classes), unique(pred_classes))
  
  # Initialize aggregates
  total_precision <- 0
  total_recall <- 0
  total_f1 <- 0
  classes_with_metrics <- 0
  
  cat("\nPer-class metrics:\n")
  
  for (class_name in all_classes) {
    # Skip if class doesn't appear in both actual and predicted
    if (!(class_name %in% rownames(conf_matrix)) || 
        !(class_name %in% colnames(conf_matrix))) {
      cat(sprintf("Warning: Class %s lacks data for metrics calculation\n", 
                 class_name))
      next
    }
    
    # True positives
    tp <- conf_matrix[class_name, class_name]
    
    # False positives (predicted as this class but actually different)
    fp <- sum(conf_matrix[, class_name]) - tp
    
    # False negatives (actually this class but predicted as different)
    fn <- sum(conf_matrix[class_name, ]) - tp
    
    # True negatives (neither actual nor predicted as this class)
    tn <- sum(conf_matrix) - tp - fp - fn
    
    # Calculate metrics
    precision <- ifelse(tp + fp > 0, tp / (tp + fp), 0)
    recall <- ifelse(tp + fn > 0, tp / (tp + fn), 0)
    f1_score <- ifelse(precision + recall > 0, 
                     2 * precision * recall / (precision + recall), 
                     0)
    
    # Add to class metrics
    class_metrics[[class_name]] <- list(
      precision = precision,
      recall = recall,
      f1_score = f1_score,
      support = sum(conf_matrix[class_name, ]),
      true_positives = tp,
      false_positives = fp,
      false_negatives = fn
    )
    
    # Add to totals for averaging
    total_precision <- total_precision + precision
    total_recall <- total_recall + recall
    total_f1 <- total_f1 + f1_score
    classes_with_metrics <- classes_with_metrics + 1
    
    cat(sprintf("  %s - Precision: %.1f%%, Recall: %.1f%%, F1: %.1f%%, Support: %d\n",
               class_name, precision * 100, recall * 100, f1_score * 100,
               sum(conf_matrix[class_name, ])))
  }
  
  # Calculate macro-averages
  avg_precision <- total_precision / classes_with_metrics
  avg_recall <- total_recall / classes_with_metrics
  avg_f1 <- total_f1 / classes_with_metrics
  
  cat(sprintf("\nMacro-average metrics - Precision: %.1f%%, Recall: %.1f%%, F1: %.1f%%\n",
             avg_precision * 100, avg_recall * 100, avg_f1 * 100))
  
  # Generate report
  if (!is.null(output_file)) {
    # Create report text
    report <- c()
    
    # Header
    report <- c(report, "# CAROLLIA LDA MODEL EVALUATION REPORT")
    report <- c(report, sprintf("Date: %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S")))
    report <- c(report, sprintf("Model: %s", basename(model_path)))
    report <- c(report, sprintf("Data: %s", data_folder))
    report <- c(report, sprintf("Files evaluated: %d", total))
    report <- c(report, "")
    
    # Overall metrics
    report <- c(report, "## OVERALL METRICS")
    report <- c(report, sprintf("Accuracy: %.2f%%", accuracy * 100))
    report <- c(report, sprintf("Macro Avg Precision: %.2f%%", avg_precision * 100))
    report <- c(report, sprintf("Macro Avg Recall: %.2f%%", avg_recall * 100))
    report <- c(report, sprintf("Macro Avg F1 Score: %.2f%%", avg_f1 * 100))
    report <- c(report, "")
    
    # Per-class metrics
    report <- c(report, "## CLASS METRICS")
    report <- c(report, sprintf("%-30s %10s %10s %10s %10s", 
                               "Class", "Precision", "Recall", "F1 Score", "Support"))
    report <- c(report, paste(rep("-", 75), collapse = ""))
    
    for (class_name in names(class_metrics)) {
      metrics <- class_metrics[[class_name]]
      report <- c(report, sprintf("%-30s %9.1f%% %9.1f%% %9.1f%% %10d", 
                                class_name, 
                                metrics$precision * 100,
                                metrics$recall * 100,
                                metrics$f1_score * 100,
                                metrics$support))
    }
    report <- c(report, "")
    
    # Confusion matrix
    report <- c(report, "## CONFUSION MATRIX")
    
    # Format confusion matrix as text
    cm <- conf_matrix
    
    # Header row for predicted classes
    header <- sprintf("%-30s", "Actual \\ Predicted")
    for (col in colnames(cm)) {
      header <- paste0(header, sprintf(" %10s", col))
    }
    report <- c(report, header)
    report <- c(report, paste(rep("-", nchar(header)), collapse = ""))
    
    # Data rows
    for (row in rownames(cm)) {
      line <- sprintf("%-30s", row)
      for (col in colnames(cm)) {
        line <- paste0(line, sprintf(" %10d", cm[row, col]))
      }
      report <- c(report, line)
    }
    
    # Write report to file
    report_text <- paste(report, collapse = "\n")
    writeLines(report_text, output_file)
    cat(sprintf("\nReport saved to: %s\n", output_file))
  }
  
  # Function to find top confusion errors
  find_top_confusions <- function(cm, n = 3) {
    confusion_errors <- c()
    
    # Iterate through each cell of the confusion matrix
    for (actual in rownames(cm)) {
      for (predicted in colnames(cm)) {
        # Skip the diagonal (correct predictions)
        if (actual == predicted) next
        
        # Count of this type of error
        error_count <- cm[actual, predicted]
        
        if (error_count > 0) {
          confusion_errors <- c(confusion_errors, 
                                list(list(actual = actual, 
                                         predicted = predicted, 
                                         count = error_count)))
        }
      }
    }
    
    # Sort by error count in descending order
    sorted_errors <- confusion_errors[order(sapply(confusion_errors, function(x) x$count), 
                                           decreasing = TRUE)]
    
    # Return top n errors or all if less than n
    return(sorted_errors[1:min(n, length(sorted_errors))])
  }
  
  top_confusions <- find_top_confusions(conf_matrix, 3)
  
  cat("\nTop confusion errors:\n")
  for (i in 1:length(top_confusions)) {
    error <- top_confusions[[i]]
    cat(sprintf("%d. %s misclassified as %s: %d instances\n", 
                i, error$actual, error$predicted, error$count))
  }
  
  # Return evaluation results
  return(list(
    status = "success",
    model_path = model_path,
    data_folder = data_folder,
    files_evaluated = total,
    overall_accuracy = accuracy,
    macro_avg_precision = avg_precision,
    macro_avg_recall = avg_recall,
    macro_avg_f1 = avg_f1,
    confusion_matrix = conf_matrix,
    class_metrics = class_metrics,
    predictions = predictions,
    top_confusions = top_confusions
  ))
}

# Main execution
cat("Starting Carollia model evaluation...\n")

# Path to the Carollia model and training data
model_path <- "/app/data/models/carollia_lda_model_new.RData"  # Using the new model
data_folder <- "/app/R_code/model_functions/training_Carollia"
report_path <- "/app/data/carollia_model_evaluation_report.txt"

# Evaluate the model on the full dataset
results <- evaluate_carollia_model(model_path, data_folder, output_file = report_path)

cat("\nEvaluation complete!\n")