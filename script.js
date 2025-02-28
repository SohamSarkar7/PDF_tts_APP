// script.js

// Lighting effect on file upload
const fileUploader = document.querySelector('.st-file-uploader input[type="file"]');
if (fileUploader) {
    fileUploader.addEventListener('change', () => {
        if (fileUploader.files.length > 0) {
            document.body.classList.add('lighting');
        } else {
            document.body.classList.remove('lighting');
        }
    });
}

// Lighting effect on button click
const summarizeButton = document.querySelector('.st-button button');
if (summarizeButton) {
    summarizeButton.addEventListener('click', () => {
        summarizeButton.classList.add('lighting');
        setTimeout(() => summarizeButton.classList.remove('lighting'), 1000);
    });
}