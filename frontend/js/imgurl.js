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
function imgUrl(url, fallback = '') {
    if (!url || url === 'not_provided' || url === 'not_uploaded') {
        return fallback;
    }
    // Already an absolute URL (Supabase public URLs) — use as-is
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    // Relative path — prepend origin (for any legacy local-storage URLs)
    return window.location.origin + (url.startsWith('/') ? '' : '/') + url;
}

// Legacy compat: IMG_BASE_URL is now empty because imgUrl() handles resolution
const IMG_BASE_URL = '';
