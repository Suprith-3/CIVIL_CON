/**
 * CIVIL CONNECTION - Shared Image URL Resolver
 * 
 * Supabase Storage always returns full absolute URLs like:
 *   https://xxxx.supabase.co/storage/v1/object/public/media/...
 *
 * OLD broken code: `${IMG_BASE_URL}${url}` where IMG_BASE_URL = window.location.origin
 * This created: https://civil-con.onrender.comhttps://supabase.co/...  ❌
 *
 * FIX: imgUrl(url) — safely resolves any image URL regardless of format.
 */

/**
 * Safely resolves an image URL from Supabase or local storage.
 * @param {string|null|undefined} url - The raw URL from the database
 * @param {string} [fallback=''] - Fallback URL if the url is empty/null
 * @returns {string} A usable absolute URL
 */
/**
 * Safely resolves an image URL from Supabase or local storage.
 */
function imgUrl(url, fallback = 'https://placehold.co/400x300?text=No+Image+Provided') {
    if (!url || typeof url !== 'string') return fallback;
    
    const currentOrigin = window.location.origin;
    const isLocalhost = currentOrigin.includes('localhost') || currentOrigin.includes('127.0.0.1');

    // Clean the URL - remove whitespace and surrounding quotes
    let cleanUrl = url.trim().replace(/^["'](.+)["']$/, '$1');
    
    // Check for common "invalid" strings in database
    const invalidStrings = ['not_provided', 'not_uploaded', 'null', 'undefined', '[]', '', 'none'];
    if (invalidStrings.includes(cleanUrl.toLowerCase())) return fallback;
    
    // Detect and fix localhost URLs in production
    if (!isLocalhost && (cleanUrl.includes('localhost:') || cleanUrl.includes('127.0.0.1:'))) {
        // If it's a local Supabase URL, try to extract the path and point to current origin or placeholder
        if (cleanUrl.includes('/storage/v1/object/public/')) {
             // This was a local supabase URL, it won't work in production.
             // We can't easily guess the production supabase URL here without the project ref,
             // so we fall back to placeholder to avoid broken icons.
             return fallback;
        }
        // If it was just a local file path with http://localhost
        cleanUrl = cleanUrl.replace(/^https?:\/\/[^\/]+/, '');
    }

    // If it looks like a JSON array string
    if (cleanUrl.startsWith('[') && cleanUrl.endsWith(']')) {
        try {
            const arr = JSON.parse(cleanUrl);
            if (Array.isArray(arr) && arr.length > 0) {
                cleanUrl = arr[0];
            } else {
                return fallback;
            }
        } catch (e) {
            return fallback;
        }
    }

    // Secondary check for partial invalidity
    if (cleanUrl.includes('placeholder') || (cleanUrl.includes('uploads/') && !cleanUrl.includes('.'))) {
        return fallback;
    }
    
    // Already an absolute URL — use as-is
    if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {
        return cleanUrl;
    }

    // Relative path — prepend origin
    // Ensure we don't have double slashes
    const separator = cleanUrl.startsWith('/') ? '' : '/';
    return currentOrigin + separator + cleanUrl;
}

// Attach to window for global access across modules
window.imgUrl = imgUrl;
window.IMG_BASE_URL = '';

console.log("🎨 CivilConnection Image Resolver Loaded.");
