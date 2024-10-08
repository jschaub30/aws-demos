async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const statusMessage = document.getElementById('statusMessage');
    const fileLinks = document.getElementById('fileLinks');
    fileLinks.innerHTML = '';

    if (!file) {
        statusMessage.textContent = 'Please select a file to upload.';
        return;
    }

    const filename = file.name;
    const contentType = file.type || 'application/octet-stream';
    const apiUrl = "https://bx3sac0sc7.execute-api.us-east-1.amazonaws.com/Prod/job";

    try {
        // Call the Lambda function to get the presigned URL
        statusMessage.textContent = 'Getting presigned URL to upload file...';
        const lambdaResponse = await fetch(`${apiUrl}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                content_type: contentType
            })
        });

        if (!lambdaResponse.ok) {
            statusMessage.textContent = 'Failed to get presigned URL: ' + lambdaResponse.status + lambdaResponse.statusText;
            throw new Error('Failed to get presigned URL');
        }

        const lambdaData = await lambdaResponse.json();
        const presignedUrl = lambdaData.presigned_url;
        const jobId = lambdaData.job_id;

        // Upload the file to S3 using the presigned URL
        statusMessage.textContent = 'Uploading file...';
        const uploadResponse = await fetch(presignedUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': contentType
            },
            body: file
        });

        if (!uploadResponse.ok) {
            throw new Error('Failed to upload file to S3');
        }

        statusMessage.textContent = 'File uploaded successfully. Checking job status...';

        // Start polling the job status
        checkJobStatus(jobId, 0);
    } catch (error) {
        console.error('Error:', error);
        statusMessage.textContent = 'Error uploading file: ' + error.message;
    }
}

async function checkJobStatus(jobId, elapsedTime) {
    const statusMessage = document.getElementById('statusMessage');
    const fileLinks = document.getElementById('fileLinks');
    const pollInterval = 5000; // Poll every 5 seconds
    const maxPollingTime = 120000; // Maximum polling time of 2 minutes (120,000 ms)
    const apiUrl = "https://bx3sac0sc7.execute-api.us-east-1.amazonaws.com/Prod/job";

    // Stop polling if the elapsed time exceeds 5 minutes
    if (elapsedTime >= maxPollingTime) {
        statusMessage.textContent = 'Polling stopped after 2 minutes. Please try again later.';
        return;
    }

    try {
        const statusResponse = await fetch(`${apiUrl}?job_id=${jobId}`);  // Use the environment variable
        if (!statusResponse.ok) {
            throw new Error('Failed to check job status');
        }

        const statusData = await statusResponse.json();

        if (statusData.status === 'success') {
            statusMessage.textContent = 'Job completed successfully:';

            // Clear previous links
            fileLinks.innerHTML = '';

            // Iterate over the URLs and create links
            for (const [key, url] of Object.entries(statusData.urls)) {
                const link = document.createElement('a');
                link.href = url;
                if (key.toUpperCase() == 'INPUT'){
                    link.textContent = 'INPUT file';
                } else {
                    link.textContent = `${key.toUpperCase()} output`;
                }
                link.target = '_blank';
                fileLinks.appendChild(link);
                fileLinks.appendChild(document.createElement('br'));
            }
        } else if (statusData.status === 'started') {
            if (statusMessage.textContent !== 'Job started successfully. Please wait...') {
                statusMessage.textContent = 'Job started successfully. Please wait...';
            }
            setTimeout(() => checkJobStatus(jobId, elapsedTime + pollInterval), pollInterval);
        } else if (statusData.status === 'error') {
            statusMessage.textContent = statusData.message;
        } else {
            // If the job is still processing (other statuses)
            if (statusMessage.textContent !== 'Job is in progress...') {
                statusMessage.textContent = 'Job is in progress...';
            }
            setTimeout(() => checkJobStatus(jobId, elapsedTime + pollInterval), pollInterval);
        }
    } catch (error) {
        console.error('Error:', error);
        statusMessage.textContent = 'Error checking job status: ' + error.message;
    }
}

function toggleFileChoice() {
    const fileChoice = document.getElementById('fileChoice').value;
    const choiceLabel = document.getElementById('choiceLabel');
    const uploadSection = document.getElementById('uploadSection');
    const existingFilesSection = document.getElementById('existingFilesSection');

    if (fileChoice == "0") {
        uploadSection.style.display = 'block';
        existingFilesSection.style.display = 'none';
    } else {
        uploadSection.style.display = 'none';
        existingFilesSection.style.display = 'block';
    }
}

async function submitExistingFile() {
    const statusMessage = document.getElementById('statusMessage');
    const apiUrl = "https://bx3sac0sc7.execute-api.us-east-1.amazonaws.com/Prod/job";
    const selectedFileInput = document.querySelector('input[name="existingFile"]:checked');
    const fileLinks = document.getElementById('fileLinks');
    fileLinks.textContent = "";

    if (!selectedFileInput) {
        statusMessage.textContent = 'Please select a file to submit.';
        return;
    }

    statusMessage.textContent = 'Submitting existing file...';
    const selectedFileUrl = selectedFileInput.value;

    try {
        // Call the Lambda function to submit the existing file URL
        statusMessage.textContent = 'Submitting existing file URL...';
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_url: selectedFileUrl
            })
        });


        if (!response.ok) {
            console.log(response);
            console.dir(response);
            let responseBodyText = await response.text();
            let responseBody = JSON.parse(responseBodyText);
            let errorMessage = 'Failed to submit the file URL: ' +
                'Status=' + response.status +
                ', message=' + responseBody.message;

            console.log(errorMessage);
            statusMessage.textContent = errorMessage;
            throw new Error(errorMessage);
        }

        const data = await response.json();
        const jobId = data.job_id;
        statusMessage.textContent = 'File URL submitted successfully. Checking job status...';

        // Start polling the job status
        checkJobStatus(jobId, 0);
    } catch (error) {
        console.error('Error:', error);
        statusMessage.textContent = 'Error submitting file URL: ' + error.message;
    }
}
