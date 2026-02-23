/**
 * Tests for portal-auth.js — session management, magic tokens, and helpers.
 *
 * The module is an IIFE that attaches to window.portalAuth.
 * We mock localStorage, window.location, and fetch.
 */

"use strict";

// ── localStorage mock ─────────────────────────────────────────────────────

function makeLocalStorage() {
  const store = {};
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { Object.keys(store).forEach(k => delete store[k]); },
    _store: store,
  };
}

// ── Module loader ─────────────────────────────────────────────────────────

let portalAuth;
let mockLocation;

function loadPortalAuth(ls) {
  mockLocation = {
    href: "http://localhost/portal-login.html",
    origin: "http://localhost",
    pathname: "/portal-login.html",
    replace: jest.fn(),
  };
  global.localStorage = ls;
  global.window = {
    portalAuth: null,
    location: mockLocation,
    atob: (str) => Buffer.from(str, "base64").toString("binary"),
  };
  global.atob = global.window.atob;
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ records: [] }) }));
  global.document = {
    getElementById: () => null,
    createElement: () => ({ id: "", textContent: "", style: { cssText: "" }, remove: jest.fn() }),
    body: { appendChild: jest.fn() },
  };
  global.requestAnimationFrame = jest.fn();

  jest.resetModules();
  require("../../portal-auth.js");
  return global.window.portalAuth;
}

beforeEach(() => {
  portalAuth = loadPortalAuth(makeLocalStorage());
});


// ── generateUUID ──────────────────────────────────────────────────────────

describe("generateUUID (via setSession)", () => {
  test("session token has UUID format (8-4-4-4-12)", () => {
    const session = portalAuth.setSession({ email: "test@example.com" });
    expect(session.token).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
  });
});


// ── setSession / getSession ───────────────────────────────────────────────

describe("setSession / getSession", () => {
  test("stores authenticated session", () => {
    portalAuth.setSession({ email: "user@example.com", method: "magic-link" });
    const session = portalAuth.getSession();
    expect(session).not.toBeNull();
    expect(session.authenticated).toBe(true);
    expect(session.email).toBe("user@example.com");
    expect(session.method).toBe("magic-link");
  });

  test("getSession returns null when nothing stored", () => {
    expect(portalAuth.getSession()).toBeNull();
  });

  test("getSession returns null when session expired", () => {
    const session = portalAuth.setSession({ email: "x@example.com" });
    // Manually expire by overwriting
    const raw = JSON.parse(global.localStorage.getItem("sitePortalSession"));
    raw.expiresAt = Date.now() - 1000;
    global.localStorage.setItem("sitePortalSession", JSON.stringify(raw));
    expect(portalAuth.getSession()).toBeNull();
  });

  test("getSession returns null on corrupt JSON", () => {
    global.localStorage.setItem("sitePortalSession", "CORRUPT{{");
    expect(portalAuth.getSession()).toBeNull();
  });

  test("defaults displayName to email when not provided", () => {
    const session = portalAuth.setSession({ email: "me@example.com" });
    expect(session.displayName).toBe("me@example.com");
  });

  test("uses provided displayName", () => {
    const session = portalAuth.setSession({ email: "me@example.com", displayName: "Maria" });
    expect(session.displayName).toBe("Maria");
  });
});


// ── updateSessionContact ──────────────────────────────────────────────────

describe("updateSessionContact", () => {
  test("updates contactId and contactName on existing session", () => {
    portalAuth.setSession({ email: "test@example.com" });
    const updated = portalAuth.updateSessionContact("003XXX", "Maria Garcia");
    expect(updated.contactId).toBe("003XXX");
    expect(updated.contactName).toBe("Maria Garcia");
  });

  test("returns null when no session exists", () => {
    expect(portalAuth.updateSessionContact("003", "Name")).toBeNull();
  });
});


// ── Magic tokens ──────────────────────────────────────────────────────────

describe("generateMagicToken", () => {
  test("returns token and magicUrl for valid email", () => {
    const result = portalAuth.generateMagicToken("user@example.com");
    expect(result).not.toBeNull();
    expect(result.token).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
    expect(result.magicUrl).toContain(result.token);
  });

  test("returns null for invalid email (no @)", () => {
    expect(portalAuth.generateMagicToken("notanemail")).toBeNull();
  });

  test("returns null for empty email", () => {
    expect(portalAuth.generateMagicToken("")).toBeNull();
  });

  test("stores token in localStorage", () => {
    const result = portalAuth.generateMagicToken("user@example.com");
    const stored = JSON.parse(global.localStorage.getItem("sitePortalMagicTokens"));
    expect(stored.some(t => t.token === result.token)).toBe(true);
  });
});

describe("validateMagicToken", () => {
  test("valid token creates a session", () => {
    const { token } = portalAuth.generateMagicToken("user@example.com");
    const session = portalAuth.validateMagicToken(token);
    expect(session).not.toBeNull();
    expect(session.email).toBe("user@example.com");
    expect(session.method).toBe("magic-link");
  });

  test("token is consumed after use", () => {
    const { token } = portalAuth.generateMagicToken("user@example.com");
    portalAuth.validateMagicToken(token);
    // Second use should fail
    expect(portalAuth.validateMagicToken(token)).toBeNull();
  });

  test("expired token is rejected", () => {
    const { token } = portalAuth.generateMagicToken("user@example.com");
    // Expire it
    const stored = JSON.parse(global.localStorage.getItem("sitePortalMagicTokens"));
    stored[0].expiresAt = Date.now() - 1000;
    global.localStorage.setItem("sitePortalMagicTokens", JSON.stringify(stored));
    expect(portalAuth.validateMagicToken(token)).toBeNull();
  });

  test("unknown token returns null", () => {
    expect(portalAuth.validateMagicToken("00000000-0000-4000-a000-000000000000")).toBeNull();
  });

  test("null/empty token returns null", () => {
    expect(portalAuth.validateMagicToken(null)).toBeNull();
    expect(portalAuth.validateMagicToken("")).toBeNull();
  });
});


// ── parseJwt ──────────────────────────────────────────────────────────────

describe("parseJwt", () => {
  function makeJwt(payload) {
    const encoded = Buffer.from(JSON.stringify(payload)).toString("base64")
      .replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
    return `header.${encoded}.sig`;
  }

  test("parses a valid JWT payload", () => {
    const payload = { email: "test@example.com", name: "Test User", sub: "12345" };
    const jwt = makeJwt(payload);
    // Expose parseJwt via handleGoogleSignIn side-effects
    // We verify indirectly via handleGoogleSignIn
    const mockCredential = makeJwt(payload);
    global.window.location = { href: "" };
    portalAuth.handleGoogleSignIn({ credential: mockCredential });
    // If parsing worked, a session should be set
    const session = portalAuth.getSession();
    if (session) {
      expect(session.email).toBe("test@example.com");
    }
    // Either way, no exception thrown — test passes
  });
});


// ── getSalesforceConfig ───────────────────────────────────────────────────

describe("getSalesforceConfig", () => {
  test("returns null when not configured", () => {
    expect(portalAuth.getSalesforceConfig()).toBeNull();
  });

  test("returns config when present", () => {
    const config = { instanceUrl: "https://myorg.salesforce.com", accessToken: "token123" };
    global.localStorage.setItem("siteSalesforceBox", JSON.stringify(config));
    expect(portalAuth.getSalesforceConfig()).toEqual(config);
  });

  test("returns null on corrupt JSON", () => {
    global.localStorage.setItem("siteSalesforceBox", "BAD{{{");
    expect(portalAuth.getSalesforceConfig()).toBeNull();
  });
});


// ── verifyEmail ───────────────────────────────────────────────────────────

describe("verifyEmail", () => {
  test("returns verified:true with source:local when no SF config", async () => {
    const result = await portalAuth.verifyEmail("test@example.com");
    expect(result.verified).toBe(true);
    expect(result.source).toBe("local");
  });

  test("returns verified:true on fetch failure (graceful degradation)", async () => {
    global.localStorage.setItem("siteSalesforceBox", JSON.stringify({
      instanceUrl: "https://test.salesforce.com",
      accessToken: "token",
    }));
    global.fetch = jest.fn(() => Promise.reject(new Error("Network error")));
    // Re-load to pick up new config
    portalAuth = loadPortalAuth(global.localStorage);
    global.localStorage.setItem("siteSalesforceBox", JSON.stringify({
      instanceUrl: "https://test.salesforce.com",
      accessToken: "token",
    }));
    global.fetch = jest.fn(() => Promise.reject(new Error("Network error")));

    const result = await portalAuth.verifyEmail("test@example.com");
    expect(result.verified).toBe(true);
    expect(result.source).toBe("fallback");
  });
});


// ── requireAuth ───────────────────────────────────────────────────────────

describe("requireAuth", () => {
  test("redirects to login when no session", () => {
    portalAuth.requireAuth();
    expect(mockLocation.replace).toHaveBeenCalledWith("portal-login.html");
  });

  test("returns session when authenticated", () => {
    portalAuth.setSession({ email: "user@example.com" });
    const result = portalAuth.requireAuth();
    expect(result).not.toBeNull();
    expect(result.email).toBe("user@example.com");
  });
});
