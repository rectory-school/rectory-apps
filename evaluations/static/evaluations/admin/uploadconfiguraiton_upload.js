document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.querySelector("#uploadconfig-upload-form");
    const inputButton = document.querySelector("#uploadconfig-upload-form-file");
    const uploadButton = document.querySelector("#uploadconfig-upload-button");

    inputButton.addEventListener("change", (evt) => {
        uploadForm.submit();
    });

    uploadButton.addEventListener("click", (evt) => {
        evt.preventDefault();
        inputButton.click();
    });
}, false);