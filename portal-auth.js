/* ══════════════════════════════════════════════
   Portal Authentication Engine — v3.8
   Session management, Google Sign-In, Magic Link,
   Salesforce Box integration
   ══════════════════════════════════════════════ */

(function() {
  "use strict";

  var SESSION_KEY = "sitePortalSession";
  var MAGIC_KEY = "sitePortalMagicTokens";
  var SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours
  var MAGIC_DURATION = 15 * 60 * 1000; // 15 minutes

  /* ── Session helpers ── */

  function getPortalSession() {
    try {
      var raw = localStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      var session = JSON.parse(raw);
      if (!session || !session.authenticated) return null;
      if (Date.now() > session.expiresAt) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
      return session;
    } catch (e) {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
  }

  function setPortalSession(data) {
    var session = {
      authenticated: true,
      method: data.method || "unknown",
      email: data.email || "",
      displayName: data.displayName || data.email || "",
      token: data.token || generateUUID(),
      expiresAt: Date.now() + SESSION_DURATION
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    return session;
  }

  function clearPortalSession() {
    localStorage.removeItem(SESSION_KEY);
    window.location.href = "portal-login.html";
  }

  function requireAuth() {
    var session = getPortalSession();
    if (!session) {
      window.location.replace("portal-login.html");
      return null;
    }
    return session;
  }

  /* ── Magic Link ── */

  function generateMagicToken(email) {
    if (!email || !email.includes("@")) return null;

    var token = generateUUID();
    var tokens = getMagicTokens();
    tokens.push({
      token: token,
      email: email,
      expiresAt: Date.now() + MAGIC_DURATION
    });
    localStorage.setItem(MAGIC_KEY, JSON.stringify(tokens));

    var magicUrl = window.location.origin + window.location.pathname.replace(/[^/]*$/, "") + "portal-login.html?token=" + token;
    console.log("[Portal] Magic link for " + email + ":\n" + magicUrl);

    return token;
  }

  function validateMagicToken(token) {
    if (!token) return null;
    var tokens = getMagicTokens();
    var now = Date.now();
    var match = null;

    for (var i = 0; i < tokens.length; i++) {
      if (tokens[i].token === token && now < tokens[i].expiresAt) {
        match = tokens[i];
        tokens.splice(i, 1); // consume token
        break;
      }
    }

    // Clean expired tokens
    tokens = tokens.filter(function(t) { return now < t.expiresAt; });
    localStorage.setItem(MAGIC_KEY, JSON.stringify(tokens));

    if (match) {
      return setPortalSession({
        method: "magic-link",
        email: match.email,
        displayName: match.email
      });
    }
    return null;
  }

  function getMagicTokens() {
    try {
      return JSON.parse(localStorage.getItem(MAGIC_KEY)) || [];
    } catch (e) {
      return [];
    }
  }

  /* ── Google Sign-In ── */

  function handleGoogleSignIn(response) {
    try {
      var payload = parseJwt(response.credential);
      if (!payload || !payload.email) {
        showPortalToast("Sign-in failed. Please try again.", true);
        return;
      }
      setPortalSession({
        method: "google",
        email: payload.email,
        displayName: payload.name || payload.email
      });
      window.location.href = "portal-dashboard.html";
    } catch (e) {
      console.error("[Portal] Google sign-in error:", e);
      showPortalToast("Sign-in failed. Please try again.", true);
    }
  }

  function initGoogleSignIn() {
    var container = document.getElementById("portalGoogleBtn");
    if (!container) return;

    // Placeholder client ID — admin can configure a real one later
    var clientId = "PLACEHOLDER_CLIENT_ID.apps.googleusercontent.com";

    var script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = function() {
      if (typeof google === "undefined" || !google.accounts) return;
      google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleSignIn
      });
      google.accounts.id.renderButton(container, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "signin_with",
        shape: "pill"
      });
    };
    document.head.appendChild(script);
  }

  /* ── Utilities ── */

  function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function parseJwt(token) {
    try {
      var base64Url = token.split(".")[1];
      var base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      var json = decodeURIComponent(atob(base64).split("").map(function(c) {
        return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(""));
      return JSON.parse(json);
    } catch (e) {
      return null;
    }
  }

  function showPortalToast(msg, isError) {
    var existing = document.getElementById("portalToast");
    if (existing) existing.remove();

    var toast = document.createElement("div");
    toast.id = "portalToast";
    toast.textContent = msg;
    toast.style.cssText = "position:fixed;bottom:32px;left:50%;transform:translateX(-50%) translateY(20px);padding:14px 28px;border-radius:980px;font-size:0.875rem;font-weight:500;z-index:9999;opacity:0;transition:opacity 0.3s,transform 0.3s;pointer-events:none;"
      + (isError
        ? "background:rgba(214,48,49,0.92);color:#fff;backdrop-filter:blur(12px);"
        : "background:rgba(59,130,246,0.92);color:#fff;backdrop-filter:blur(12px);");
    document.body.appendChild(toast);

    requestAnimationFrame(function() {
      toast.style.opacity = "1";
      toast.style.transform = "translateX(-50%) translateY(0)";
    });
    setTimeout(function() {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(-50%) translateY(20px)";
      setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
  }

  /* ── Salesforce / Box Integration ── */

  var SF_CONFIG_KEY = "siteSalesforceBox";

  function getSalesforceConfig() {
    try {
      return JSON.parse(localStorage.getItem(SF_CONFIG_KEY)) || null;
    } catch (e) {
      return null;
    }
  }

  function fetchContactData(email) {
    var config = getSalesforceConfig();
    if (!config || !config.instanceUrl || !email) {
      return Promise.resolve(null);
    }

    var soql = "SELECT FirstName, Box_Upload_Link__c, Box_View_Only_Link__c FROM Contact WHERE Email='" + email.replace(/'/g, "\\'") + "' LIMIT 1";
    var url = config.instanceUrl.replace(/\/+$/, "") + "/services/data/v59.0/query/?q=" + encodeURIComponent(soql);

    return fetch(url, {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + (config.accessToken || ""),
        "Content-Type": "application/json"
      }
    }).then(function(resp) {
      if (!resp.ok) return null;
      return resp.json();
    }).then(function(data) {
      if (data && data.records && data.records.length > 0) {
        var rec = data.records[0];
        return {
          firstName: rec.FirstName || null,
          uploadLink: rec.Box_Upload_Link__c || null,
          viewLink: rec.Box_View_Only_Link__c || null
        };
      }
      return null;
    }).catch(function() {
      return null;
    });
  }

  /* ── Public API ── */

  window.portalAuth = {
    getSession: getPortalSession,
    setSession: setPortalSession,
    clearSession: clearPortalSession,
    requireAuth: requireAuth,
    generateMagicToken: generateMagicToken,
    validateMagicToken: validateMagicToken,
    handleGoogleSignIn: handleGoogleSignIn,
    initGoogleSignIn: initGoogleSignIn,
    showToast: showPortalToast,
    getSalesforceConfig: getSalesforceConfig,
    fetchContactData: fetchContactData
  };

})();
