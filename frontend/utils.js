/**
 * Shared utility functions for the Product Browser frontend.
 */

/**
 * Format a price value as INR currency string.
 */
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price);
}

/**
 * Format an ISO date string to a readable short date (e.g. "Jun 15, 2025").
 */
function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

/**
 * Toggle element visibility by adding/removing the 'hidden' class.
 */
function setVisible(element, visible) {
    if (visible) {
        element.classList.remove('hidden');
    } else {
        element.classList.add('hidden');
    }
}

/**
 * Build an API URL with query parameters, omitting null/undefined/empty values.
 */
function buildApiUrl(baseUrl, params) {
    const url = new URL(baseUrl);
    for (const [key, value] of Object.entries(params)) {
        if (value !== null && value !== undefined && value !== '') {
            url.searchParams.set(key, value);
        }
    }
    return url.toString();
}

/**
 * Apply modal animation classes for open/close transitions.
 * @param {HTMLElement} element - The modal content element.
 * @param {boolean} open - true to show (scale up), false to hide (scale down).
 */
function setModalAnimationState(element, open) {
    if (open) {
        element.classList.remove('scale-95', 'opacity-0');
        element.classList.add('scale-100', 'opacity-100');
    } else {
        element.classList.remove('scale-100', 'opacity-100');
        element.classList.add('scale-95', 'opacity-0');
    }
}
