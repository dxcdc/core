/*
Template Name: Ubold - Responsive Bootstrap 5 Admin Dashboard
Author: Techzaa
File: Quilljs init js
*/

// Snow theme
const snowEditor = document.getElementById('snow-editor')
if (snowEditor) {
    var quill = new Quill(snowEditor, {
        theme: 'snow',
        modules: {
            'toolbar': [[{'font': []}, {'size': []}], ['bold', 'italic', 'underline', 'strike'], [{'color': []}, {'background': []}], [{'script': 'super'}, {'script': 'sub'}], [{'header': [false, 1, 2, 3, 4, 5, 6]}, 'blockquote', 'code-block'], [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}], ['direction', {'align': []}], ['link', 'image', 'video'], ['clean']]
        },
    });
}

// Bubble theme
const bubbleEditor = document.getElementById('bubble-editor')
if (bubbleEditor) {
    var quill = new Quill(bubbleEditor, {
        theme: 'bubble'
    });
}

