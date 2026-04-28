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
    if (!url || url === 'not_provided' || url === 'not_uploaded' || url === 'null' || url === 'undefined') {
        return fallback;
    }
    
    // Clean the URL - remove whitespace and surrounding quotes
    let cleanUrl = url.trim().replace(/^["'](.+)["']$/, '$1');
    
    // Already an absolute URL (Supabase public URLs) — use as-is
    if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {
        return cleanUrl;
    }
    
    // Relative path — prepend origin
    const origin = window.location.origin;
    const finalUrl = origin + (cleanUrl.startsWith('/') ? '' : '/') + cleanUrl;
    return finalUrl;
}

// Attach to window for global access across modules
window.imgUrl = imgUrl;
window.IMG_BASE_URL = '';

console.log("🎨 CivilConnection Image Resolver Loaded.");
