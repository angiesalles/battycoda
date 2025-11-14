#!/usr/bin/env Rscript
#
# API Endpoints Definition
# This file contains only the endpoint definitions
#

# Load model modules
source("model_functions/utils_module.R")
source("model_functions/model_runner.R")
source("model_functions/model_trainer.R")

#* @apiTitle Bat Call Classification API
#* @apiDescription API for training and using bat call classifiers

#* Health check endpoint
#* @get /ping
function() {
  debug_log("Ping request received")
  result <- list(
    status = "alive", 
    timestamp = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    r_version = R.version.string
  )
  debug_log("Ping response sent")
  return(result)
}

#* Run prediction on a folder of WAV files using KNN model
#* @post /predict/knn
#* @param wav_folder:character Path to folder containing WAV files
#* @param model_path:character Full path to the model file
#* @param export_features_path:character Optional path to export extracted features as CSV
function(wav_folder, model_path, export_features_path = NULL) {
  debug_log("KNN prediction request received")
  debug_log("Parameters: wav_folder=", wav_folder, "model_path=", model_path)
  if (!is.null(export_features_path)) {
    debug_log("Features will be exported to:", export_features_path)
  }
  
  # Call KNN prediction function
  tryCatch({
    result <- run_model(wav_folder, model_path, "knn", export_features_path)
    debug_log("KNN prediction successful")
    return(result)
  }, error = function(e) {
    debug_log("ERROR in KNN prediction:", e$message)
    return(list(
      status = "error",
      message = paste("Error in KNN prediction:", e$message)
    ))
  })
}

#* Run prediction on a folder of WAV files using LDA model
#* @post /predict/lda
#* @param wav_folder:character Path to folder containing WAV files
#* @param model_path:character Full path to the model file
#* @param export_features_path:character Optional path to export extracted features as CSV
function(wav_folder, model_path, export_features_path = NULL) {
  debug_log("LDA prediction request received")
  debug_log("Parameters: wav_folder=", wav_folder, "model_path=", model_path)
  if (!is.null(export_features_path)) {
    debug_log("Features will be exported to:", export_features_path)
  }
  
  # Call LDA prediction function
  tryCatch({
    result <- run_model(wav_folder, model_path, "lda", export_features_path)
    debug_log("LDA prediction successful")
    return(result)
  }, error = function(e) {
    debug_log("ERROR in LDA prediction:", e$message)
    return(list(
      status = "error",
      message = paste("Error in LDA prediction:", e$message)
    ))
  })
}

#* Train a new KNN model
#* @post /train/knn
#* @param data_folder:character Path to training data directory
#* @param output_model_path:character Full path where the model should be saved
#* @param test_split:numeric Fraction of data to use for testing (0.0-1.0)
#* @param k:numeric Optional k value for KNN (default: auto-tuned)
function(data_folder, output_model_path, test_split = 0.2, k = NULL) {
  debug_log("KNN training request received")
  debug_log("Parameters: data_folder=", data_folder,
            "output_model_path=", output_model_path,
            "test_split=", test_split,
            "k=", ifelse(is.null(k), "auto-tune", k))

  # Call KNN training function from module
  tryCatch({
    result <- train_model(data_folder, output_model_path, as.numeric(test_split), "knn", k)
    debug_log("KNN training successful")
    return(result)
  }, error = function(e) {
    debug_log("ERROR in KNN training:", e$message)
    return(list(
      status = "error",
      message = paste("Error in KNN training:", e$message)
    ))
  })
}

#* Train a new LDA model
#* @post /train/lda
#* @param data_folder:character Path to training data directory
#* @param output_model_path:character Full path where the model should be saved
#* @param test_split:numeric Fraction of data to use for testing (0.0-1.0)
function(data_folder, output_model_path, test_split = 0.2) {
  debug_log("LDA training request received")
  debug_log("Parameters: data_folder=", data_folder, 
            "output_model_path=", output_model_path, 
            "test_split=", test_split)
  
  # Call LDA training function
  tryCatch({
    result <- train_model(data_folder, output_model_path, as.numeric(test_split), "lda")
    debug_log("LDA training successful")
    return(result)
  }, error = function(e) {
    debug_log("ERROR in LDA training:", e$message)
    return(list(
      status = "error",
      message = paste("Error in LDA training:", e$message)
    ))
  })
}