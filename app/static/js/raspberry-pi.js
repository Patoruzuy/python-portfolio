// Toggle code examples for Raspberry Pi projects
function toggleCodeExample(projectId) {
    const codeExample = document.getElementById(`code-example-${projectId}`);
    if (codeExample.style.display === 'none') {
        codeExample.style.display = 'block';
    } else {
        codeExample.style.display = 'none';
    }
}
