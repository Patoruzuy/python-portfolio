/**
 * Python Developer Portfolio - Main JavaScript
 * Terminal Brutalist Edition
 * Handles navigation, animations, and interactive features
 */

// Scanline Toggle (CRT Effect)
document.addEventListener('DOMContentLoaded', function() {
    const scanlineToggle = document.getElementById('scanlineToggle');
    const body = document.body;
    
    // Check localStorage for saved preference
    const scanlinesEnabled = localStorage.getItem('scanlines') === 'true';
    if (scanlinesEnabled) {
        body.classList.add('scanlines');
    }
    
    if (scanlineToggle) {
        scanlineToggle.addEventListener('click', function() {
            body.classList.toggle('scanlines');
            localStorage.setItem('scanlines', body.classList.contains('scanlines'));
        });
    }
});

// Navigation Toggle for Mobile
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            
            // Toggle ASCII menu icon [≡] to [X]
            const span = this.querySelector('span');
            if (navMenu.classList.contains('active')) {
                span.textContent = '[X]';
            } else {
                span.textContent = '[≡]';
            }
        });
        
        // Close menu when clicking on a link
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                const span = navToggle.querySelector('span');
                span.textContent = '[≡]';
            });
        });
    }
});

// Navbar Scroll Effect
let lastScroll = 0;
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', function() {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll <= 0) {
        navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.5)';
        navbar.style.borderBottom = '2px solid #30363d';
    } else {
        navbar.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.7)';
        navbar.style.borderBottom = '2px solid #58d68d';
    }
    
    lastScroll = currentScroll;
});

// Smooth Scroll for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href !== '') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Intersection Observer for Terminal Loading Animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            // Terminal-style loading with staggered delay
            setTimeout(() => {
                entry.target.classList.add('terminal-loaded');
            }, index * 100); // Stagger the animations
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe elements for animation with terminal loading class
document.querySelectorAll('.project-card, .skill-card, .blog-post-card, .product-card, .terminal-window').forEach(el => {
    el.classList.add('terminal-loading');
    observer.observe(el);
});

// Skill Bar Animation
const skillBars = document.querySelectorAll('.skill-fill');
const skillObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const width = entry.target.style.width;
            entry.target.style.width = '0';
            setTimeout(() => {
                entry.target.style.width = width;
            }, 100);
            skillObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

skillBars.forEach(bar => {
    skillObserver.observe(bar);
});

// Terminal Boot Sequence Animation (Homepage)
if (document.querySelector('.ascii-python-logo')) {
    const bootElements = [
        '.ascii-python-logo',
        '.terminal-output',
        '.hero-cta',
        '.hero-stats'
    ];
    
    bootElements.forEach((selector, index) => {
        const element = document.querySelector(selector);
        if (element) {
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.transition = 'opacity 0.3s ease';
                element.style.opacity = '1';
            }, index * 200);
        }
    });
}

// Typewriter effect for terminal prompts
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.textContent = '';
    
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Add terminal cursor animation to active elements
function addTerminalCursor(element) {
    const cursor = document.createElement('span');
    cursor.className = 'terminal-cursor';
    element.appendChild(cursor);
}

// ASCII Spinner for loading states
const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
let spinnerInterval;

function showTerminalSpinner(element, message = 'Loading') {
    let frame = 0;
    const originalContent = element.innerHTML;
    
    spinnerInterval = setInterval(() => {
        element.innerHTML = `${spinnerFrames[frame]} ${message}...`;
        frame = (frame + 1) % spinnerFrames.length;
    }, 80);
    
    return () => {
        clearInterval(spinnerInterval);
        element.innerHTML = originalContent;
    };
}

// Form Validation Enhancement
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('invalid')) {
                validateInput(this);
            }
        });
    });
});

function validateInput(input) {
    const value = input.value.trim();
    const type = input.type;
    
    let isValid = true;
    let errorMessage = '';
    
    if (value === '') {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    if (isValid) {
        input.classList.remove('invalid');
        input.classList.add('valid');
        removeErrorMessage(input);
    } else {
        input.classList.remove('valid');
        input.classList.add('invalid');
        showErrorMessage(input, errorMessage);
    }
    
    return isValid;
}

function showErrorMessage(input, message) {
    removeErrorMessage(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.color = '#f56565';
    errorDiv.style.fontSize = '0.85rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function removeErrorMessage(input) {
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

// Add input validation styles
const style = document.createElement('style');
style.textContent = `
    input.valid, textarea.valid, select.valid {
        border-color: #48bb78 !important;
    }
    
    input.invalid, textarea.invalid, select.invalid {
        border-color: #f56565 !important;
    }
`;
document.head.appendChild(style);

// Lazy Loading Images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Copy Code to Clipboard
document.querySelectorAll('pre code').forEach(block => {
    const button = document.createElement('button');
    button.className = 'copy-code-btn';
    button.textContent = 'Copy';
    button.style.cssText = `
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: #3776ab;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    const pre = block.parentElement;
    pre.style.position = 'relative';
    pre.appendChild(button);
    
    pre.addEventListener('mouseenter', () => {
        button.style.opacity = '1';
    });
    
    pre.addEventListener('mouseleave', () => {
        button.style.opacity = '0';
    });
    
    button.addEventListener('click', async function() {
        const code = block.textContent;
        
        try {
            await navigator.clipboard.writeText(code);
            this.textContent = 'Copied!';
            this.style.backgroundColor = '#48bb78';
            
            setTimeout(() => {
                this.textContent = 'Copy';
                this.style.backgroundColor = '#3776ab';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy code:', err);
            this.textContent = 'Failed';
            setTimeout(() => {
                this.textContent = 'Copy';
            }, 2000);
        }
    });
});

// Back to Top Button
const backToTopButton = document.createElement('button');
backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
backToTopButton.className = 'back-to-top';
backToTopButton.style.cssText = `
    position: fixed;
    bottom: 2rem;
    left: 2rem;
    width: 50px;
    height: 50px;
    background-color: #3776ab;
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
    z-index: 998;
`;

document.body.appendChild(backToTopButton);

window.addEventListener('scroll', function() {
    if (window.pageYOffset > 300) {
        backToTopButton.style.display = 'flex';
    } else {
        backToTopButton.style.display = 'none';
    }
});

backToTopButton.addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

backToTopButton.addEventListener('mouseenter', function() {
    this.style.transform = 'scale(1.1)';
});

backToTopButton.addEventListener('mouseleave', function() {
    this.style.transform = 'scale(1)';
});

// Search Functionality (if search input exists)
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = document.querySelectorAll('[data-searchable]');
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
}

// Dark Mode Toggle (Optional Feature)
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return;
    
    const darkMode = localStorage.getItem('darkMode');
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }
    
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.setItem('darkMode', null);
        }
    });
}

// Initialize dark mode if toggle exists
initDarkMode();

// Performance: Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Performance: Throttle Function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Apply throttle to scroll events
const throttledScroll = throttle(function() {
    // Scroll-based animations or effects
}, 100);

window.addEventListener('scroll', throttledScroll);

// Console Message
console.log('%c👋 Hello Developer!', 'font-size: 20px; color: #3776ab; font-weight: bold;');
console.log('%cInterested in the code? Check out the repository!', 'font-size: 14px; color: #646464;');
console.log('%cBuilt with Python, Flask, and modern web technologies', 'font-size: 12px; color: #718096;');

// Analytics (placeholder - integrate with your analytics service)
function trackEvent(category, action, label) {
    // Example: Google Analytics
    // gtag('event', action, {
    //     'event_category': category,
    //     'event_label': label
    // });
    
    console.log('Event tracked:', category, action, label);
}

// Track button clicks
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function() {
        const text = this.textContent.trim();
        trackEvent('Button', 'Click', text);
    });
});

// Track external links
document.querySelectorAll('a[target="_blank"]').forEach(link => {
    link.addEventListener('click', function() {
        const url = this.href;
        trackEvent('External Link', 'Click', url);
    });
});

// Service Worker Registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment to enable service worker
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered:', registration))
        //     .catch(error => console.log('SW registration failed:', error));
    });
}

// Export functions for use in other scripts
window.portfolioUtils = {
    debounce,
    throttle,
    validateInput,
    trackEvent
};
