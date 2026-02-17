/**
 * Cloudflare Worker — Site Settings Sync (KV-backed)
 * O'Brien Immigration Law
 *
 * Persists site configuration to KV so settings survive browser
 * data clears and work across devices/incognito windows.
 *
 * KV binding:  SITE_SETTINGS
 * Secrets:     ADMIN_TOKEN, ALLOWED_ORIGIN
 *
 * Routes:
 *   GET  /settings        — return all keys (public)
 *   GET  /settings/:key   — return single key (public)
 *   PUT  /settings        — bulk write { key: value, ... } (auth)
 *   PUT  /settings/:key   — write single key (auth)
 *   DELETE /settings/:key — remove a key (auth)
 */

const ALLOWED_KEYS = new Set([
  "siteSettings",
  "siteNavFooterSettings",
  "siteDesignSettings",
  "sitePageToggles",
  "siteBusinessHours",
  "siteContactConfig",
  "siteClockSettings",
  "siteTranslation",
  "siteSuccessRibbon",
  "siteOfficeLocations",
  "bentoTiles",
  "sitePages",
  "sitePosts",
  "siteStaff",
  "siteTestimonials",
  "siteLocations",
  "siteCareers",
  "sitePathFinder",
]);

export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || "*";

    // ── CORS preflight ──
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin),
      });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // ── Route: GET /settings — return all keys ──
    if (request.method === "GET" && path === "/settings") {
      const result = {};
      const list = await env.SITE_SETTINGS.list();
      for (const key of list.keys) {
        result[key.name] = await env.SITE_SETTINGS.get(key.name);
      }
      return jsonResponse(200, result, origin);
    }

    // ── Route: GET /settings/:key ──
    if (request.method === "GET" && path.startsWith("/settings/")) {
      const key = decodeURIComponent(path.slice("/settings/".length));
      if (!ALLOWED_KEYS.has(key)) {
        return jsonResponse(400, { error: "Key not in whitelist" }, origin);
      }
      const value = await env.SITE_SETTINGS.get(key);
      if (value === null) {
        return jsonResponse(404, { error: "Key not found" }, origin);
      }
      return jsonResponse(200, { key, value }, origin);
    }

    // ── Auth check for writes ──
    const authError = checkAuth(request, env);
    if (authError) return authError;

    // ── Route: PUT /settings — bulk write ──
    if (request.method === "PUT" && path === "/settings") {
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse(400, { error: "Invalid JSON" }, origin);
      }

      const written = [];
      const rejected = [];
      for (const [key, value] of Object.entries(body)) {
        if (!ALLOWED_KEYS.has(key)) {
          rejected.push(key);
          continue;
        }
        const val = typeof value === "string" ? value : JSON.stringify(value);
        await env.SITE_SETTINGS.put(key, val);
        written.push(key);
      }
      return jsonResponse(200, { written, rejected }, origin);
    }

    // ── Route: PUT /settings/:key — write single key ──
    if (request.method === "PUT" && path.startsWith("/settings/")) {
      const key = decodeURIComponent(path.slice("/settings/".length));
      if (!ALLOWED_KEYS.has(key)) {
        return jsonResponse(400, { error: "Key not in whitelist" }, origin);
      }
      const value = await request.text();
      await env.SITE_SETTINGS.put(key, value);
      return jsonResponse(200, { key, written: true }, origin);
    }

    // ── Route: DELETE /settings/:key ──
    if (request.method === "DELETE" && path.startsWith("/settings/")) {
      const key = decodeURIComponent(path.slice("/settings/".length));
      if (!ALLOWED_KEYS.has(key)) {
        return jsonResponse(400, { error: "Key not in whitelist" }, origin);
      }
      await env.SITE_SETTINGS.delete(key);
      return jsonResponse(200, { key, deleted: true }, origin);
    }

    return jsonResponse(404, { error: "Not found" }, origin);
  },
};

/* ── Helpers ── */

function checkAuth(request, env) {
  const origin = env.ALLOWED_ORIGIN || "*";
  const header = request.headers.get("Authorization") || "";
  const token = header.replace(/^Bearer\s+/i, "");
  if (!token || token !== env.ADMIN_TOKEN) {
    return jsonResponse(401, { error: "Unauthorized" }, origin);
  }
  return null;
}

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
  };
}

function jsonResponse(status, body, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(origin),
    },
  });
}
