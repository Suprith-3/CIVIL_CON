/**
 * imgurl.js - Centralized Image URL Resolver
 * 
 * This utility ensures that image URLs from Supabase or local storage
 * resolve correctly across both localhost and production (Render).
 */

function imgUrl(url, fallback = 'https://placehold.co/400x300?text=No+Image+Provided') {
    const debug = true; // Set to true to see logs in console
    
    // 1. Basic Validation
    if (!url || typeof url !== 'string' || url.length < 3) {
        if (debug) console.log("🖼️ Image Resolved: (Using Fallback - Invalid Input)", url);
        return fallback;
    }
    
    const currentOrigin = window.location.origin;
    const isLocalhost = currentOrigin.includes('localhost') || currentOrigin.includes('127.0.0.1');

    // 2. Clean the URL - remove whitespace and surrounding quotes/brackets
    let cleanUrl = url.trim().replace(/^["'\[]+|["'\]]+$/g, '');
    
    // If it was a JSON string like '["http..."]', it's now just 'http...'
    
    // 3. Check for common "invalid" strings in database
    const invalidStrings = ['not_provided', 'not_uploaded', 'null', 'undefined', '[]', '', 'none'];
    if (invalidStrings.includes(cleanUrl.toLowerCase())) {
        if (debug) console.log("🖼️ Image Resolved: (Using Fallback - Invalid String)", cleanUrl);
        return fallback;
    }
    
    // 4. Detect and fix localhost URLs in production
    if (!isLocalhost && (cleanUrl.includes('localhost:') || cleanUrl.includes('127.0.0.1:'))) {
        if (debug) console.warn("⚠️ Detected Localhost URL on Production:", cleanUrl);
        
        // Try to recover the path if it's a supabase-style URL
        if (cleanUrl.includes('/storage/v1/object/public/')) {
            // It's a local supabase URL, cannot be recovered without production project ref
            return fallback;
        }
        
        // Strip the localhost domain to turn it into a relative path
        cleanUrl = cleanUrl.replace(/^https?:\/\/[^\/]+/, '');
    }

    // 5. Handle JSON array strings (Supabase often returns these for multiple images)
    if (cleanUrl.startsWith('[') && cleanUrl.endsWith(']')) {
        try {
            const arr = JSON.parse(cleanUrl);
            if (Array.isArray(arr) && arr.length > 0) {
                cleanUrl = arr[0]; // Take first image
            } else {
                return fallback;
            }
        } catch (e) {
            return fallback;
        }
    }

    // 6. Secondary check for partial invalidity
    if (cleanUrl.includes('placeholder') || (cleanUrl.includes('uploads/') && !cleanUrl.includes('.'))) {
        if (debug) console.log("🖼️ Image Resolved: (Using Fallback - Partial Invalid)", cleanUrl);
        return fallback;
    }
    
    // 7. Absolute URLs (Supabase public URLs) — use as-is
    if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {
        if (debug) console.log("🖼️ Image Resolved (Absolute):", cleanUrl);
        return cleanUrl;
    }

    // 8. Relative paths — prepend origin
    // Ensure we don't have double slashes
    const separator = cleanUrl.startsWith('/') ? '' : '/';
    const finalUrl = currentOrigin + separator + cleanUrl;
    
    if (debug) {
        if (!isLocalhost && (cleanUrl.startsWith('media/') || cleanUrl.startsWith('documents/'))) {
            console.warn("⚠️ Image Resolved (Relative - High Risk on Deploy):", finalUrl);
            console.info("💡 Tip: If this image is on Supabase, the database should store the FULL URL starting with https://");
        } else {
            console.log("🖼️ Image Resolved (Relative):", finalUrl);
        }
    }
    
    return finalUrl;
}

// Attach to window for global access across modules
window.imgUrl = imgUrl;
