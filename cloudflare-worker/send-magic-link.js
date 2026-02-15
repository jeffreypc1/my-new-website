/**
 * Cloudflare Worker — Magic Link Email Delivery
 * O'Brien Immigration Law Client Portal
 *
 * Sends magic link emails via Resend API (HTTP-based, CF Worker compatible).
 * Gmail SMTP is not usable from Workers (no TCP/SMTP support).
 *
 * Required secrets (set via `wrangler secret put`):
 *   RESEND_API_KEY    — from https://resend.com/api-keys
 *   PORTAL_SECRET     — shared secret the portal sends as a Bearer token
 *   ALLOWED_ORIGIN    — e.g. https://obrienimmigration.com
 *
 * Optional environment variable (set in wrangler.toml):
 *   FROM_EMAIL        — e.g. portal@obrienimmigration.com (must be verified in Resend)
 */

export default {
  async fetch(request, env) {
    // ── CORS preflight ──
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(env.ALLOWED_ORIGIN || "*"),
      });
    }

    // ── Only accept POST ──
    if (request.method !== "POST") {
      return jsonResponse(405, { error: "Method not allowed" }, env.ALLOWED_ORIGIN);
    }

    // ── Origin check ──
    const origin = request.headers.get("Origin") || "";
    const allowedOrigin = env.ALLOWED_ORIGIN || "";
    if (allowedOrigin && allowedOrigin !== "*" && origin !== allowedOrigin) {
      return jsonResponse(403, { error: "Forbidden: origin not allowed" }, allowedOrigin);
    }

    // ── Bearer token auth ──
    const authHeader = request.headers.get("Authorization") || "";
    const expectedToken = env.PORTAL_SECRET || "";
    if (!expectedToken || authHeader !== "Bearer " + expectedToken) {
      return jsonResponse(401, { error: "Unauthorized" }, allowedOrigin);
    }

    // ── Parse body ──
    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse(400, { error: "Invalid JSON" }, allowedOrigin);
    }

    const { to, subject, html } = body;
    if (!to || !subject || !html) {
      return jsonResponse(400, { error: "Missing required fields: to, subject, html" }, allowedOrigin);
    }

    // ── Send via Resend ──
    const resendKey = env.RESEND_API_KEY || "";
    if (!resendKey) {
      return jsonResponse(500, { error: "RESEND_API_KEY not configured" }, allowedOrigin);
    }

    const fromEmail = env.FROM_EMAIL || "O'Brien Immigration Portal <onboarding@resend.dev>";

    try {
      const resendResp = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + resendKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: fromEmail,
          to: [to],
          subject: subject,
          html: html,
        }),
      });

      if (resendResp.ok) {
        const data = await resendResp.json();
        return jsonResponse(200, { success: true, id: data.id }, allowedOrigin);
      } else {
        const err = await resendResp.text();
        console.error("Resend error:", err);
        return jsonResponse(502, { error: "Email delivery failed", detail: err }, allowedOrigin);
      }
    } catch (err) {
      console.error("Fetch error:", err);
      return jsonResponse(500, { error: "Internal error" }, allowedOrigin);
    }
  },
};

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
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
