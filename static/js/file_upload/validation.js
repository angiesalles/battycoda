// File validation
                } else {
                    statusText.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Processing files and creating tasks...';
                    progressBar.classList.remove('progress-bar-animated');
                }
            }
        });
        
        // Handle response
        xhr.addEventListener('load', function() {
            console.log(`XHR load event fired, status: ${xhr.status}`);
            
            // Always log the raw response for debugging
            console.log("Raw response text:", xhr.responseText.substring(0, 1000));
            
            if (xhr.status === 200) {
                try {
                    console.log("Attempting to parse JSON response");
                    const response = JSON.parse(xhr.responseText);
                    console.log("Parsed JSON response:", response);
                    
                    if (response.success) {
                        console.log("Success response detected");
                        statusText.innerHTML = `
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle mr-2"></i>
                                Upload complete! Successfully created batch with ${response.recordings_created || 'multiple'} recordings.
                            </div>
                        `;
                        progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
                        progressBar.classList.add('bg-success');
                        
                        // Ensure we have a redirect URL
                        if (!response.redirect_url) {
                            console.warn("Missing redirect_url in response");
                        }
                        
                        // Show success animation before redirect
                        console.log("Setting timeout for redirect");
                        setTimeout(() => {
                            // Redirect to the batch detail page or show success message
                            if (response.redirect_url) {
                                console.log("Executing redirect to:", response.redirect_url);
                                // Force a hard redirect to bypass any caching
                                window.location.assign(response.redirect_url);
                            } else {
                                console.error("No redirect URL available");
                            }
                        }, 1500);
                    } else {
                        console.warn("Response success=false:", response);
                        handleError(response.error || 'Upload failed');
                    }
                } catch (err) {
                    console.error("JSON parse error:", err);
                    console.log("Unable to parse response as JSON");
                    
                    // Handle non-JSON response (likely HTML from a successful form submission)
                    if (xhr.responseURL) {
                        console.log("Non-JSON response with responseURL available");
                        console.log("Redirecting to response URL:", xhr.responseURL);
                        window.location.assign(xhr.responseURL);
                    } else {
                        console.error("No responseURL available for non-JSON response");
                        handleError('Unknown response from server');
                    }
                }
            } else {
                console.error("HTTP error status:", xhr.status, xhr.statusText);
                handleError(`Upload failed (${xhr.status}: ${xhr.statusText})`);
            }
        });
        
        xhr.addEventListener('error', function() {
            handleError('Network error occurred');
        });
        
        xhr.addEventListener('abort', function() {
            handleError('Upload aborted');
        });
        
