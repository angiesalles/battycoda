#!/usr/bin/env Rscript
#
# Model Trainer Module - Unified interface for training classifier models
#

# Load required packages
library(warbleR)
library(stringr)
library(mlr3)
library(mlr3learners)
library(kknn)
library(mlr3tuning)
library(viridis)  # For visualization

# Load common utilities
source("model_functions/utils_module.R")

# Process training data and split into train/test sets
prepare_training_data <- function(data_folder, test_split = 0.2) {
  # Verify folder exists
  if (!dir.exists(data_folder)) {
    stop(paste("Data folder not found:", data_folder))
  }
  
  # Save original working directory
  original_dir <- getwd()
  on.exit(setwd(original_dir))  # Ensure we return to original directory
  
  # Change to data folder
  debug_log(sprintf("Processing training data in: %s", data_folder))
  setwd(data_folder)
  
  # Get list of WAV files
  sound.files <- list.files(pattern = "\\.wav$")
  if (length(sound.files) == 0) {
    stop("No WAV files found in the specified folder")
  }
  
  debug_log(sprintf("Found %d WAV files", length(sound.files)))
  
  # Extract labels from filenames (assuming format: NUMBER_LABEL.wav)
  # For example: 123_Echo.wav -> "Echo"
  labels <- sapply(strsplit(sound.files, "_"), function(x) {
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
  class_counts <- table(labels)
  debug_log("Class distribution in dataset:")
  for (class_name in names(class_counts)) {
    debug_log(sprintf("  %s: %d files", class_name, class_counts[class_name]))
  }
  
  
  # Load enhanced segment processor for better error diagnostics
  debug_log("Loading enhanced segment processor...")
  processor_path <- "/app/R_code/model_functions/process_segment.R"
  debug_log(sprintf("Looking for processor at: %s", processor_path))
  source(processor_path)
  
  # Extract acoustic features with enhanced error diagnostics
  debug_log("Extracting acoustic features...")
  
  # Process files individually using our enhanced processor
  all_features <- NULL
  num_files <- length(sound.files)
  
  # Progress tracking variables
  start_time <- Sys.time()
  success_count <- 0
  failure_count <- 0
  
  for (i in 1:num_files) {
    
    # Get the file name and path
    file_name <- sound.files[i]
    file_path <- file.path(getwd(), file_name)
    
    # Get the class label from the filename
    file_label <- labels[i]
    
    # Show progress for every file
    elapsed_time <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
    if (elapsed_time > 0 && i > 1) {
      files_per_sec <- (i - 1) / elapsed_time
      eta_secs <- (num_files - i + 1) / files_per_sec
      eta_mins <- round(eta_secs / 60, 1)
      debug_log(sprintf("Processing file %d/%d (%.1f%%) [%s] - %.1f files/sec - ETA: %.1f min - Success: %d, Failed: %d", 
                       i, num_files, (i/num_files)*100, file_name, files_per_sec, eta_mins, success_count, failure_count))
    } else {
      debug_log(sprintf("Processing file %d/%d (%.1f%%) [%s] - Success: %d, Failed: %d", 
                       i, num_files, (i/num_files)*100, file_name, success_count, failure_count))
    }
    
    # Process file using the enhanced process_segment function
    features <- process_segment(file_path)
    
    # Add to results if successful and replace the default selec value with actual label
    if (!is.null(features) && nrow(features) > 0) {
      # Replace the selec column with the actual label
      features$selec <- file_label
      
      # Add to the combined features dataset
      if (is.null(all_features)) {
        all_features <- features
      } else {
        all_features <- rbind(all_features, features)
      }
      success_count <- success_count + 1
    } else {
      failure_count <- failure_count + 1
    }
  }
  
  # Ensure we got features
  if (is.null(all_features) || nrow(all_features) == 0) {
    stop("Failed to extract features from any files")
  }
  
  total_time <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
  debug_log(sprintf("Feature extraction completed in %.1f seconds", total_time))
  debug_log(sprintf("Successfully extracted features from %d files (%.1f%% success rate)", 
                   success_count, (success_count/num_files)*100))
  debug_log(sprintf("Failed files: %d (%.1f%% failure rate)", 
                   failure_count, (failure_count/num_files)*100))
  ftable <- all_features
  
  # Prepare data for classification
  debug_log("Preparing data for classification...")
  ftable <- ftable[-1]  # Remove first column (redundant with sound.files)
  
  # Get unique call types and convert to factor
  levels <- unique(ftable$selec)
  debug_log(sprintf("Found %d unique call types: %s", length(levels), paste(levels, collapse=", ")))
  ftable$selec <- factor(ftable$selec, levels)
  
  # Perform stratified split for train/test
  debug_log(sprintf("Performing stratified %d/%d train/test split...", 
            round((1-test_split)*100), round(test_split*100)))
  set.seed(42)  # For reproducibility
  
  # Stratified sampling
  train_indices <- c()
  test_indices <- c()
  
  # For each class, split according to test_split ratio
  for (class_name in levels) {
    # Get indices for this class
    class_indices <- which(ftable$selec == class_name)
    # Shuffle these indices
    class_indices <- sample(class_indices)
    # Calculate split point
    split_point <- round((1-test_split) * length(class_indices))
    
    if (split_point < 1) {
      # Ensure at least one sample for training
      split_point <- 1
    }
    
    # Add to train and test sets
    train_indices <- c(train_indices, class_indices[1:split_point])
    if (split_point < length(class_indices)) {
      test_indices <- c(test_indices, class_indices[(split_point+1):length(class_indices)])
    }
  }
  
  # Shuffle the training indices
  train_indices <- sample(train_indices)
  
  # Split the data
  train_data <- ftable[train_indices, ]
  test_data <- ftable[test_indices, ]
  
  # Return the prepared data
  return(list(
    train_data = train_data,
    test_data = test_data,
    levels = levels,
    sound_files = sound.files,
    class_counts = class_counts
  ))
}

# Evaluate model performance and save metrics
evaluate_and_save_model <- function(model, test_data, output_model_path, training_info) {
  # Evaluate on test set
  debug_log("Evaluating model on test data...")
  
  # MLR3 model evaluation
  predictions <- model$predict_newdata(test_data)
  pred_classes <- predictions$response
  prob_matrix <- predictions$prob
  
  actual_classes <- test_data$selec
  
  # Check for NA values in predictions
  if (any(is.na(pred_classes))) {
    debug_log("WARNING: Found NA values in predictions. Replacing with most common class...")
    most_common_class <- names(sort(table(actual_classes), decreasing = TRUE))[1]
    pred_classes[is.na(pred_classes)] <- most_common_class
  }
  
  # Calculate accuracy
  accuracy <- mean(pred_classes == actual_classes)
  debug_log(sprintf("Overall accuracy on test set: %.2f%%", accuracy * 100))
  
  # Create confusion matrix
  debug_log("Generating confusion matrix...")
  conf_matrix <- table(Actual = actual_classes, Predicted = pred_classes)
  
  # Calculate per-class metrics
  debug_log("Calculating per-class metrics...")
  class_metrics <- list()
  levels <- levels(actual_classes)
  
  for (class_name in levels) {
    if (class_name %in% rownames(conf_matrix) && class_name %in% colnames(conf_matrix)) {
      # True positives
      tp <- conf_matrix[class_name, class_name]
      # False positives (sum of column - true positives)
      fp <- sum(conf_matrix[, class_name]) - tp
      # False negatives (sum of row - true positives)
      fn <- sum(conf_matrix[class_name, ]) - tp
      
      # Calculate metrics
      precision <- ifelse(tp + fp > 0, tp / (tp + fp), 0)
      recall <- ifelse(tp + fn > 0, tp / (tp + fn), 0)
      f1_score <- ifelse(precision + recall > 0, 
                       2 * precision * recall / (precision + recall), 
                       0)
      
      class_metrics[[class_name]] <- list(
        precision = precision,
        recall = recall,
        f1_score = f1_score,
        support = sum(conf_matrix[class_name, ])
      )
      
      debug_log(sprintf("  %s - Precision: %.1f%%, Recall: %.1f%%, F1: %.1f%%, Support: %d",
                class_name, precision * 100, recall * 100, f1_score * 100,
                sum(conf_matrix[class_name, ])))
    }
  }
  
  # Save the model
  debug_log(sprintf("Saving model to: %s", output_model_path))
  
  # Make sure directory exists
  output_dir <- dirname(output_model_path)
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }
  
  # Save model objects based on type
  if (training_info$model_type == "knn") {
    kknn_model <- model
    save(kknn_model, levels, file = output_model_path)
  } else if (training_info$model_type == "lda") {
    # Save the model and additional info
    lda_model_info <- list(
      model = model,
      levels = levels,
      feature_means = training_info$feature_means,
      feature_sds = training_info$feature_sds
    )
    save(lda_model_info, file = output_model_path)
  }
  
  # Create metrics file path
  metrics_path <- paste0(sub("\\.RData$", "", output_model_path), 
                         "_", training_info$model_type, "_metrics.RData")
  
  # Save detailed metrics
  model_metrics <- list(
    model_info = list(
      model_type = training_info$model_type,
      training_files = nrow(training_info$train_data),
      test_files = nrow(test_data),
      classes = levels,
      hyperparameters = training_info$hyperparameters
    ),
    performance = list(
      accuracy = accuracy,
      confusion_matrix = conf_matrix,
      class_metrics = class_metrics
    ),
    training_summary = list(
      data_folder = training_info$data_folder,
      file_count = length(training_info$sound_files),
      class_distribution = as.list(training_info$class_counts)
    )
  )
  
  save(model_metrics, file = metrics_path)
  debug_log(sprintf("Model metrics saved to: %s", metrics_path))
  
  # Return evaluation results
  return(list(
    accuracy = accuracy * 100,
    metrics_path = metrics_path,
    confusion_matrix = conf_matrix,
    class_metrics = class_metrics
  ))
}

# Train KNN model
train_knn_model <- function(data_folder, output_model_path, test_split = 0.2) {
  # Prepare training data
  data <- prepare_training_data(data_folder, test_split)
  train_data <- data$train_data
  test_data <- data$test_data
  levels <- data$levels
  
  # Handle missing values before creating the task
  debug_log("Checking for missing values in training data...")
  
  # Get feature columns (all except the response variable 'selec')
  feature_cols <- setdiff(colnames(train_data), "selec")
  
  # Check for missing values
  missing_counts <- sapply(train_data[feature_cols], function(x) sum(is.na(x)))
  if (sum(missing_counts) > 0) {
    debug_log(sprintf("Found %d missing values across %d columns. Imputing missing values...", 
                     sum(missing_counts), sum(missing_counts > 0)))
    
    # Impute missing values with column means for each feature
    for (col in feature_cols) {
      if (sum(is.na(train_data[[col]])) > 0) {
        # Calculate mean of non-missing values
        col_mean <- mean(train_data[[col]], na.rm = TRUE)
        
        # Replace missing values with mean
        train_data[[col]][is.na(train_data[[col]])] <- col_mean
        
        debug_log(sprintf("Imputed %d missing values in column '%s' with mean %.4f", 
                         sum(missing_counts[col]), col, col_mean))
      }
    }
  }
  
  # Also handle missing values in test data
  test_missing_counts <- sapply(test_data[feature_cols], function(x) sum(is.na(x)))
  if (sum(test_missing_counts) > 0) {
    debug_log(sprintf("Found %d missing values in test data. Imputing...", sum(test_missing_counts)))
    
    # Impute missing values in test data
    for (col in feature_cols) {
      if (sum(is.na(test_data[[col]])) > 0) {
        # Use the same mean as training data for consistency
        col_mean <- mean(train_data[[col]], na.rm = TRUE)
        test_data[[col]][is.na(test_data[[col]])] <- col_mean
      }
    }
  }
  
  # Final check for remaining missing values
  final_missing <- sum(sapply(train_data[feature_cols], function(x) sum(is.na(x))))
  if (final_missing > 0) {
    stop(sprintf("Still found %d missing values after imputation. Cannot proceed with KNN training.", final_missing))
  }
  
  debug_log("Missing value imputation completed successfully")
  
  # Create classification task with cleaned data
  debug_log("Creating classification task...")
  task <- as_task_classif(train_data, target = 'selec')
  
  # Create KNN learner with tunable parameters
  debug_log("Setting up KNN learner with hyperparameter tuning...")
  learner <- lrn("classif.kknn",
                k = to_tune(1, 50, logscale = TRUE),
                distance = to_tune(1, 50, logscale = TRUE), 
                kernel = "rectangular",
                predict_type = "prob"
  )
  
  # Create auto tuner
  at <- auto_tuner(
    tuner = tnr("grid_search", resolution = 5, batch_size = 5),
    learner = learner,
    resampling = rsmp("cv", folds = 3),
    measure = msr("classif.ce")
  )
  
  # Train the model
  debug_log("Training the KNN model (this may take a while)...")
  kknn_model <- at$train(task)
  
  # Get best hyperparameters
  best_k <- kknn_model$learner$param_set$values$k
  best_distance <- kknn_model$learner$param_set$values$distance
  debug_log(sprintf("Best hyperparameters: k = %.2f, distance = %.2f", best_k, best_distance))
  
  # Prepare training info
  training_info <- list(
    model_type = "knn",
    train_data = train_data,
    data_folder = data_folder,
    sound_files = data$sound_files,
    class_counts = data$class_counts,
    hyperparameters = list(
      k = best_k,
      distance = best_distance
    )
  )
  
  # Evaluate and save model
  eval_results <- evaluate_and_save_model(kknn_model, test_data, output_model_path, training_info)
  
  # Return combined results
  return(list(
    status = "success",
    model_path = output_model_path,
    model_type = "KNN",
    metrics_path = eval_results$metrics_path,
    accuracy = eval_results$accuracy,
    classes = as.list(levels),
    file_counts = list(
      total = length(data$sound_files),
      training = nrow(train_data),
      testing = nrow(test_data)
    ),
    best_hyperparameters = list(
      k = best_k,
      distance = best_distance
    )
  ))
}

# Train LDA model using mlr3
train_lda_model <- function(data_folder, output_model_path, test_split = 0.2) {
  # Prepare training data
  data <- prepare_training_data(data_folder, test_split)
  train_data <- data$train_data
  test_data <- data$test_data
  levels <- data$levels
  
  # Scale features and handle missing values
  debug_log("Scaling features for LDA...")
  
  # Get feature columns (all except the response variable 'selec')
  feature_cols <- setdiff(colnames(train_data), "selec")
  
  # Initialize vectors to store means and standard deviations
  feature_means <- numeric(length(feature_cols))
  feature_sds <- numeric(length(feature_cols))
  names(feature_means) <- feature_cols
  names(feature_sds) <- feature_cols
  
  # First, handle missing values in training data
  # LDA cannot handle NAs, so we need to impute them
  debug_log("Checking for missing values in training data...")
  missing_counts <- sapply(train_data[feature_cols], function(x) sum(is.na(x)))
  if (sum(missing_counts) > 0) {
    debug_log(sprintf("Found %d missing values across %d columns. Imputing missing values...", 
                     sum(missing_counts), sum(missing_counts > 0)))
    
    # Impute missing values with column means
    for (col in feature_cols) {
      if (sum(is.na(train_data[[col]])) > 0) {
        # Calculate mean of non-missing values
        col_mean <- mean(train_data[[col]], na.rm = TRUE)
        
        # Replace missing values with mean
        train_data[[col]][is.na(train_data[[col]])] <- col_mean
        
        debug_log(sprintf("Imputed %d missing values in column '%s' with mean %.4f", 
                         sum(missing_counts[col]), col, col_mean))
      }
    }
  }
  
  # Scale features and store scaling parameters
  scaled_train_data <- train_data
  for (i in seq_along(feature_cols)) {
    col <- feature_cols[i]
    
    # Compute mean and sd (after imputation, there should be no NAs)
    col_mean <- mean(train_data[[col]])
    col_sd <- sd(train_data[[col]])
    
    # Store scaling parameters
    feature_means[col] <- col_mean
    feature_sds[col] <- col_sd
    
    # If sd is 0, set it to 1 to avoid division by zero
    if (col_sd == 0 || is.na(col_sd)) {
      col_sd <- 1
      feature_sds[col] <- 1
    }
    
    # Scale the data
    scaled_train_data[[col]] <- (train_data[[col]] - col_mean) / col_sd
  }
  
  # Handle missing values and scale test data using the same parameters
  scaled_test_data <- test_data
  for (col in feature_cols) {
    if (col %in% colnames(test_data)) {
      # First impute any missing values in test data using training means
      if (sum(is.na(test_data[[col]])) > 0) {
        test_data[[col]][is.na(test_data[[col]])] <- feature_means[col]
      }
      
      # Then apply scaling
      scaled_test_data[[col]] <- (test_data[[col]] - feature_means[col]) / feature_sds[col]
    }
  }
  
  # Final check for any remaining missing values
  final_missing <- sum(sapply(scaled_train_data[feature_cols], function(x) sum(is.na(x))))
  if (final_missing > 0) {
    stop(sprintf("Still found %d missing values after imputation. Cannot proceed with LDA training.", final_missing))
  }
  
  debug_log("Feature scaling and imputation completed successfully")
  
  # Create classification task using scaled data
  debug_log("Creating LDA classification task...")
  task <- as_task_classif(scaled_train_data, target = 'selec')
  
  # Check for available LDA learners in mlr3
  avail_learners <- mlr_learners$keys()
  debug_log(sprintf("Available learners for LDA: %s", 
                  paste(grep("lda", avail_learners, value = TRUE), collapse = ", ")))
  
  # Try to use one of the LDA learners available in mlr3
  if ("classif.lda" %in% avail_learners) {
    learner_id <- "classif.lda"
  } else if ("classif.LDA" %in% avail_learners) {
    learner_id <- "classif.LDA"
  } else {
    # Look for any LDA learner available
    lda_learners <- grep("lda", avail_learners, value = TRUE, ignore.case = TRUE)
    if (length(lda_learners) > 0) {
      learner_id <- lda_learners[1]
    } else {
      # If no LDA learner is available, use our custom implementation
      debug_log("No LDA learner found in mlr3, implementing custom LDA...")
      stop("No LDA implementation available without MASS package. Please install MASS or use KNN instead.")
    }
  }
  
  # Create the LDA learner with mlr3
  debug_log(sprintf("Using learner: %s", learner_id))
  learner <- lrn(learner_id, predict_type = "prob")
  
  # Train the model
  debug_log("Training LDA model...")
  lda_model <- learner$train(task)
  
  # Prepare training info
  training_info <- list(
    model_type = "lda",
    train_data = train_data,
    data_folder = data_folder,
    sound_files = data$sound_files,
    class_counts = data$class_counts,
    hyperparameters = list(),
    feature_means = feature_means,
    feature_sds = feature_sds
  )
  
  # Evaluate and save model
  eval_results <- evaluate_and_save_model(lda_model, scaled_test_data, output_model_path, training_info)
  
  # Return combined results
  return(list(
    status = "success",
    model_path = output_model_path,
    model_type = "LDA",
    metrics_path = eval_results$metrics_path,
    accuracy = eval_results$accuracy,
    classes = as.list(levels),
    file_counts = list(
      total = length(data$sound_files),
      training = nrow(train_data),
      testing = nrow(test_data)
    )
  ))
}

# Unified model training interface
train_model <- function(data_folder, output_model_path, test_split = 0.2, model_type = "knn") {
  # Call appropriate model trainer
  if (model_type == "knn") {
    return(train_knn_model(data_folder, output_model_path, test_split))
  } else if (model_type == "lda") {
    return(train_lda_model(data_folder, output_model_path, test_split))
  } else {
    stop(paste("Unsupported model type:", model_type))
  }
}
