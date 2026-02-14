/**
 * Analytics Event Tracking
 * Tracks user interactions for analytics
 */

(function() {
    'use strict';
    
    // Track button clicks
    function trackButtonClick(event) {
        const button = event.target.closest('button, a.btn, .cta-button');
        if (!button) return;
        
        const elementId = button.id || button.className;
        const text = button.textContent.trim();
        
        sendEvent({
            event_type: 'click',
            event_name: 'button_click',
            element_id: elementId,
            page_path: window.location.pathname,
            metadata: {
                text: text,
                url: button.href || null
            }
        });
    }
    
    // Track form submissions
    function trackFormSubmit(event) {
        const form = event.target;
        const formId = form.id || form.className;
        
        sendEvent({
            event_type: 'form_submit',
            event_name: 'form_submission',
            element_id: formId,
            page_path: window.location.pathname,
            metadata: {
                action: form.action || null,
                method: form.method || 'GET'
            }
        });
    }
    
    // Track newsletter signups
    function trackNewsletterSignup() {
        sendEvent({
            event_type: 'conversion',
            event_name: 'newsletter_signup',
            element_id: 'newsletter-form',
            page_path: window.location.pathname
        });
    }
    
    // Track contact form submissions
    function trackContactSubmit() {
        sendEvent({
            event_type: 'conversion',
            event_name: 'contact_form_submit',
            element_id: 'contact-form',
            page_path: window.location.pathname
        });
    }
    
    // Track external link clicks
    function trackExternalLink(event) {
        const link = event.target.closest('a');
        if (!link) return;
        
        const href = link.href;
        if (href && (href.startsWith('http://') || href.startsWith('https://')) && !href.includes(window.location.hostname)) {
            sendEvent({
                event_type: 'click',
                event_name: 'external_link_click',
                element_id: link.id || link.className,
                page_path: window.location.pathname,
                metadata: {
                    url: href,
                    text: link.textContent.trim()
                }
            });
        }
    }
    
    // Track scroll depth
    let maxScrollDepth = 0;
    let scrollDepthTracked = false;
    
    function trackScrollDepth() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = Math.round((scrollTop / docHeight) * 100);
        
        if (scrollPercent > maxScrollDepth) {
            maxScrollDepth = scrollPercent;
            
            // Track milestones: 25%, 50%, 75%, 100%
            if (!scrollDepthTracked && (scrollPercent >= 25 || scrollPercent >= 50 || scrollPercent >= 75 || scrollPercent >= 100)) {
                let milestone = 0;
                if (scrollPercent >= 100) milestone = 100;
                else if (scrollPercent >= 75) milestone = 75;
                else if (scrollPercent >= 50) milestone = 50;
                else if (scrollPercent >= 25) milestone = 25;
                
                sendEvent({
                    event_type: 'engagement',
                    event_name: 'scroll_depth',
                    element_id: 'page',
                    page_path: window.location.pathname,
                    metadata: {
                        depth: milestone
                    }
                });
            }
        }
    }
    
    // Send event to backend
    function sendEvent(eventData) {
        // Only send if analytics session cookie exists
        if (!document.cookie.includes('analytics_session')) {
            return;
        }
        
        fetch('/api/analytics/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        }).catch(err => {
            console.debug('Analytics tracking failed:', err);
        });
    }
    
    // Initialize tracking when DOM is ready
    function init() {
        // Track button clicks
        document.addEventListener('click', trackButtonClick);
        
        // Track external links
        document.addEventListener('click', trackExternalLink);
        
        // Track form submissions
        document.addEventListener('submit', trackFormSubmit);
        
        // Track newsletter signup (specific form)
        const newsletterForm = document.querySelector('[action*="newsletter"]');
        if (newsletterForm) {
            newsletterForm.addEventListener('submit', trackNewsletterSignup);
        }
        
        // Track contact form (specific form)
        const contactForm = document.querySelector('[action*="contact"]');
        if (contactForm) {
            contactForm.addEventListener('submit', trackContactSubmit);
        }
        
        // Track scroll depth
        let scrollTimeout;
        window.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(trackScrollDepth, 500);
        });
        
        // Track time on page (send event when user leaves)
        let startTime = Date.now();
        window.addEventListener('beforeunload', function() {
            const timeSpent = Math.round((Date.now() - startTime) / 1000);
            sendEvent({
                event_type: 'engagement',
                event_name: 'time_on_page',
                element_id: 'page',
                page_path: window.location.pathname,
                metadata: {
                    seconds: timeSpent
                }
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
