/* ══════════════════════════════════════════════
   Portal Authentication Engine — v3.10
   Session management, Magic Link with Salesforce
   email verification, Box integration
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
      contactId: data.contactId || null,
      contactName: data.contactName || null,
      token: data.token || generateUUID(),
      expiresAt: Date.now() + SESSION_DURATION
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    return session;
  }

  function updateSessionContact(contactId, contactName) {
    var session = getPortalSession();
    if (!session) return null;
    session.contactId = contactId;
    session.contactName = contactName;
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

  /* ── Salesforce Email Verification ── */

  function verifyEmail(email) {
    var config = getSalesforceConfig();
    if (!config || !config.instanceUrl || !email) {
      // No Salesforce config — skip verification, allow through
      return Promise.resolve({ verified: true, source: "local" });
    }

    var soql = "SELECT Id, Email FROM Contact WHERE Email='" + email.replace(/'/g, "\\'") + "' LIMIT 1";
    var url = config.instanceUrl.replace(/\/+$/, "") + "/services/data/v59.0/query/?q=" + encodeURIComponent(soql);

    return fetch(url, {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + (config.accessToken || ""),
        "Content-Type": "application/json"
      }
    }).then(function(resp) {
      if (!resp.ok) {
        // API error — allow through (don't block users due to API issues)
        return { verified: true, source: "fallback" };
      }
      return resp.json();
    }).then(function(data) {
      if (data && data.records !== undefined) {
        return data.records.length > 0
          ? { verified: true, source: "salesforce" }
          : { verified: false, source: "salesforce" };
      }
      // Non-SOQL response shape — allow through
      return { verified: true, source: "fallback" };
    }).catch(function() {
      // Network/CORS error — allow through gracefully
      return { verified: true, source: "fallback" };
    });
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

    // Email template for server-side delivery
    var emailTemplate = {
      to: email,
      subject: "Your Secure Portal Access — O'Brien Immigration Law",
      body: "Click here to access your O'Brien Immigration Secure Portal:\n\n" + magicUrl + "\n\nThis link expires in 15 minutes. If you did not request this, please ignore this email.",
      html: '<div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:480px;margin:0 auto;padding:32px">'
        + '<h2 style="color:#1a1a1a;font-size:1.25rem;margin-bottom:16px">O\'Brien Immigration Law</h2>'
        + '<p style="color:#444;font-size:0.9375rem;line-height:1.6">Click the button below to access your secure client portal:</p>'
        + '<p style="text-align:center;margin:28px 0"><a href="' + magicUrl + '" style="display:inline-block;padding:14px 32px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:980px;font-weight:600;font-size:0.9375rem">Access My Portal</a></p>'
        + '<p style="color:#888;font-size:0.75rem;line-height:1.5">This link expires in 15 minutes. If you did not request this, please ignore this email.</p>'
        + '</div>'
    };

    // Log for development — in production, this sends via server-side email service
    console.log("[Portal] Magic link for " + email + ":\n" + magicUrl);
    console.log("[Portal] Email template:", emailTemplate);

    return { token: token, magicUrl: magicUrl, emailTemplate: emailTemplate };
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

  /* ── Google Sign-In (disabled — Magic Link only for now) ── */

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
    // Google Sign-In is disabled for now — Magic Link is the primary auth method.
    // To re-enable, uncomment the SDK loading logic below and configure a Client ID.
    var container = document.getElementById("portalGoogleBtn");
    if (container) {
      container.innerHTML = '<span style="font-size:0.8125rem;color:var(--mid-gray)">Google Sign-In coming soon</span>';
    }
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

  function fetchAllContacts(email) {
    var config = getSalesforceConfig();
    if (!config || !config.instanceUrl || !email) {
      return Promise.resolve([]);
    }

    var soql = "SELECT Id, FirstName, LastName, Box_Upload_Link__c, Box_View_Only_Link__c FROM Contact WHERE Email='" + email.replace(/'/g, "\\'") + "'";
    var url = config.instanceUrl.replace(/\/+$/, "") + "/services/data/v59.0/query/?q=" + encodeURIComponent(soql);

    return fetch(url, {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + (config.accessToken || ""),
        "Content-Type": "application/json"
      }
    }).then(function(resp) {
      if (!resp.ok) return [];
      return resp.json();
    }).then(function(data) {
      if (data && data.records && data.records.length > 0) {
        return data.records.map(function(rec) {
          return {
            id: rec.Id,
            firstName: rec.FirstName || "",
            lastName: rec.LastName || "",
            uploadLink: rec.Box_Upload_Link__c || null,
            viewLink: rec.Box_View_Only_Link__c || null
          };
        });
      }
      return [];
    }).catch(function() {
      return [];
    });
  }

  function fetchContactById(contactId) {
    var config = getSalesforceConfig();
    if (!config || !config.instanceUrl || !contactId) {
      return Promise.resolve(null);
    }

    var soql = "SELECT Id, FirstName, LastName, Box_Upload_Link__c, Box_View_Only_Link__c FROM Contact WHERE Id='" + contactId.replace(/'/g, "\\'") + "' LIMIT 1";
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
          id: rec.Id,
          firstName: rec.FirstName || "",
          lastName: rec.LastName || "",
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
    updateSessionContact: updateSessionContact,
    clearSession: clearPortalSession,
    requireAuth: requireAuth,
    verifyEmail: verifyEmail,
    generateMagicToken: generateMagicToken,
    validateMagicToken: validateMagicToken,
    handleGoogleSignIn: handleGoogleSignIn,
    initGoogleSignIn: initGoogleSignIn,
    showToast: showPortalToast,
    getSalesforceConfig: getSalesforceConfig,
    fetchAllContacts: fetchAllContacts,
    fetchContactById: fetchContactById
  };

})();
