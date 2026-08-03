Dropzone.autoDiscover = false
// Dropzone
var dropzonePreviewNode = document.querySelector("#dropzone-preview-list");
if (dropzonePreviewNode) {
    dropzonePreviewNode.id = "";
    var previewTemplate = dropzonePreviewNode.parentNode.innerHTML;
    dropzonePreviewNode.parentNode.removeChild(dropzonePreviewNode);
    var dropzone = new Dropzone(".dropzone", {
        url: 'https://httpbin.org/post',
        method: "post",
        previewTemplate: previewTemplate,
        previewsContainer: "#dropzone-preview",
    });
}

// Dropzone
var dropzonePreviewTwoNode = document.querySelector("#dropzone-preview-list-2");
if (dropzonePreviewTwoNode) {
    dropzonePreviewTwoNode.id = "";
    var previewTemplateTwo = dropzonePreviewTwoNode.parentNode.innerHTML;
    dropzonePreviewTwoNode.parentNode.removeChild(dropzonePreviewTwoNode);
    var dropzone2 = new Dropzone(".dropzone-two", {
        url: 'https://httpbin.org/post',
        method: "post",
        previewTemplate: previewTemplateTwo,
        previewsContainer: "#dropzone-preview-2",
    });
}