/**
 * Cookie Consent Manager
 * GDPR-compliant cookie consent for analytics
 */

(function() {
    'use strict';
    
    const CONSENT_COOKIE_NAME = 'cookie_consent';
    const CONSENT_EXPIRY_DAYS = 365;
    
    // Check if consent has been given
    function hasConsent() {
        return getCookie(CONSENT_COOKIE_NAME) === 'accepted';
    }
    
    // Check if consent has been declined
    function hasDeclined() {
        return getCookie(CONSENT_COOKIE_NAME) === 'declined';
    }
    
    // Get cookie value
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Set cookie
    function setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }
    
    // Delete cookie
    function deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
    
    // Show cookie banner
    function showBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'flex';
        }
    }
    
    // Hide cookie banner
    function hideBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }
    
    // Accept cookies
    function acceptCookies() {
        const categories = ['necessary', 'analytics'];
        setCookie(CONSENT_COOKIE_NAME, 'accepted', CONSENT_EXPIRY_DAYS);
        logConsent('accepted', categories);
        hideBanner();
        // Reload page to enable analytics
        window.location.reload();
    }
    
    // Decline cookies
    function declineCookies() {
        const categories = ['necessary'];
        setCookie(CONSENT_COOKIE_NAME, 'declined', CONSENT_EXPIRY_DAYS);
        logConsent('declined', categories);
        hideBanner();
        // Disable analytics and remove cookies
        disableAnalytics();
    }
    
    // Log consent decision to server for GDPR audit trail
    function logConsent(consentType, categories) {
        fetch('/api/cookie-consent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                consent_type: consentType,
                categories: categories,
                session_id: getCookie('analytics_session')
            })
        }).catch(err => {
            console.debug('Consent logging failed:', err);
        });
    }
    
    // Enable analytics tracking
    function enableAnalytics() {
        console.log('Analytics enabled');
    }
    
    // Disable analytics and remove cookies
    function disableAnalytics() {
        // Delete analytics session cookie
        deleteCookie('analytics_session');
        console.log('Analytics disabled');
    }
    
    // Show cookie settings modal
    function showCookieSettings() {
        const modal = document.getElementById('cookie-settings-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    // Hide cookie settings modal
    function hideCookieSettings() {
        const modal = document.getElementById('cookie-settings-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // Save cookie preferences from settings modal
    function savePreferences() {
        const analyticsCheckbox = document.getElementById('analytics-cookies-toggle');
        const marketingCheckbox = document.getElementById('marketing-cookies-toggle');
        
        const categories = ['necessary'];  // Always included
        
        if (analyticsCheckbox && analyticsCheckbox.checked) {
            categories.push('analytics');
        }
        
        if (marketingCheckbox && marketingCheckbox.checked) {
            categories.push('marketing');
        }
        
        if (categories.length > 1) {
            setCookie(CONSENT_COOKIE_NAME, 'accepted', CONSENT_EXPIRY_DAYS);
            logConsent('partial', categories);
            window.location.reload();
        } else {
            setCookie(CONSENT_COOKIE_NAME, 'declined', CONSENT_EXPIRY_DAYS);
            logConsent('declined', categories);
            disableAnalytics();
        }
        
        hideCookieSettings();
    }
    
    // Initialize on page load
    function init() {
        // Check if user hasn't made a choice yet
        if (!hasConsent() && !hasDeclined()) {
            showBanner();
        }
        
        // Attach event listeners
        const acceptBtn = document.getElementById('accept-cookies');
        const declineBtn = document.getElementById('decline-cookies');
        const settingsBtn = document.getElementById('cookie-settings');
        const saveSettingsBtn = document.getElementById('save-cookie-settings');
        const closeModalBtn = document.getElementById('close-settings-modal');
        
        if (acceptBtn) {
            acceptBtn.addEventListener('click', acceptCookies);
        }
        
        if (declineBtn) {
            declineBtn.addEventListener('click', declineCookies);
        }
        
        if (settingsBtn) {
            settingsBtn.addEventListener('click', showCookieSettings);
        }
        
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', savePreferences);
        }
        
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', hideCookieSettings);
        }
        
        // Update settings modal checkbox if it exists
        const analyticsCheckbox = document.getElementById('analytics-cookies-toggle');
        if (analyticsCheckbox) {
            analyticsCheckbox.checked = hasConsent();
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose functions globally for settings page
    window.cookieConsent = {
        accept: acceptCookies,
        decline: declineCookies,
        hasConsent: hasConsent,
        hasDeclined: hasDeclined,
        showSettings: showCookieSettings
    };
})();
