// Contact form submission handler
document.getElementById('contactForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const form = this;
    const formData = new FormData(form);
    const formSuccess = document.getElementById('formSuccess');
    const formError = document.getElementById('formError');
    
    // Hide previous messages
    formSuccess.style.display = 'none';
    formError.style.display = 'none';
    
    // Disable submit button during submission
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    // Send form data to API
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            name: formData.get('name'),
            email: formData.get('email'),
            subject: formData.get('subject'),
            projectType: formData.get('projectType'),
            message: formData.get('message')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            formSuccess.style.display = 'block';
            form.reset();
            
            // Scroll to success message
            formSuccess.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Hide success message after 5 seconds
            setTimeout(() => {
                formSuccess.style.display = 'none';
            }, 5000);
        } else {
            formError.style.display = 'block';
            formError.textContent = data.message || 'An error occurred. Please try again.';
            
            // Scroll to error message
            formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        formError.style.display = 'block';
        formError.textContent = 'Network error. Please check your connection and try again.';
        
        // Scroll to error message
        formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    })
    .finally(() => {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    });
});
