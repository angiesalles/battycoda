#!/usr/bin/env Rscript
#
# Server Startup Script
# This file only starts the server
#

# Load required packages
library(plumber)
library(warbleR)
library(stringr)
library(mlr3)
library(mlr3learners)
library(kknn)
library(mlr3tuning)
library(viridis)

# Get command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Check for command line port argument
port <- 8000  # Default port
if (length(args) > 0 && startsWith(args[1], "--port=")) {
  port_arg <- sub("--port=", "", args[1])
  port <- as.numeric(port_arg)
}

# Set host to listen on all interfaces
host <- "0.0.0.0"  

# Print banner
cat("====================================\n")
cat("  Bat Call Classification Server\n")
cat("====================================\n")
cat("Starting server on", host, "port", port, "\n")

# Create and configure the API
api <- plumber::plumb("api_endpoints.R")

# Add CORS support
api$filter("cors", function(req, res) {
  res$setHeader("Access-Control-Allow-Origin", "*")
  plumber::forward()
})

# Define model types available
model_types <- c("knn", "lda")

# Print available endpoints
cat("Available endpoints:\n")
cat("  GET  /ping - Health check endpoint\n")
for (model in model_types) {
  cat(sprintf("  POST /predict/%s - Run prediction using %s model\n", model, toupper(model)))
}
for (model in model_types) {
  cat(sprintf("  POST /train/%s - Train a new %s model\n", model, toupper(model)))
}

# Start the server
cat(sprintf("Server ready. Test with: curl http://%s:%d/ping\n", host, port))
api$run(host = host, port = port)