document.addEventListener("DOMContentLoaded", () => {
  /* ── Global navigation (must run first) ── */
  renderGlobalNav();

  /* ── Success Ribbon (cross-fading social proof) ── */
  renderSuccessRibbon();

  /* ── Scroll-to-reveal ── */
  const reveals = document.querySelectorAll(".reveal");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  reveals.forEach((el) => observer.observe(el));

  /* ── Navbar shrink on scroll ── */
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    let ticking = false;
    window.addEventListener("scroll", () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          navbar.classList.toggle("scrolled", window.scrollY > 40);
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  /* ── Site settings (CSS variable system) ── */
  loadSiteSettings();

  /* ── Bento grid from localStorage ── */
  renderBentoGrid();

  /* ── Seed default staff & render posts ── */
  seedDefaultStaff();
  renderPostsSection();

  /* ── Dynamic navigation & routing ── */
  renderDynamicNav();
  renderDynamicFooter();
  handleRoute();

  window.addEventListener("popstate", handleRoute);

  /* ── Consultation modal ── */
  initConsultButtons();

  /* ── Dark mode ── */
  initDarkMode();

  /* ── Magnetic buttons ── */
  initMagneticButtons();

  /* ── Smooth scroll for internal anchor links ── */
  initSmoothScroll();

  /* ── Ambient motion layer ── */
  initAmbientGlow();
  /* ── Aurora glow on nav & buttons ── */
  initAuroraGlow();

  /* ── Page transition fade ── */
  initPageTransitions();

  /* ── Adaptive images (day/night) — runs after dark mode init ── */
  applyAdaptiveImages();

  /* ── Scroll depth tracking (Services section) ── */
  initScrollDepthTracking();

  /* ── Page toggle redirect (hidden pages → home) ── */
  enforcePageToggles();

  /* ── Toggle-aware footer on sub-pages ── */
  renderToggleAwareFooter();

  /* ── Admin shortcut: Cmd+Shift+A / Ctrl+Shift+A ── */
  let adminTriggered = false;

  document.addEventListener("keydown", (e) => {
    if (e.shiftKey && (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "a") {
      e.preventDefault();
      if (adminTriggered) return;
      adminTriggered = true;

      const overlay = document.createElement("div");
      overlay.className = "admin-overlay";
      overlay.innerHTML = '<div class="admin-overlay-content">' +
        '<div class="admin-overlay-spinner"></div>' +
        '<p>Loading Admin\u2026</p>' +
        '</div>';
      document.body.appendChild(overlay);

      requestAnimationFrame(() => overlay.classList.add("visible"));

      setTimeout(() => {
        window.location.href = "admin.html";
      }, 1000);
    }
  });
});

/* ══════════════════════════════════════════════
   Page Data (localStorage)
   ══════════════════════════════════════════════ */

function getPages() {
  return JSON.parse(localStorage.getItem("sitePages") || "[]");
}

function savePagesData(pages) {
  localStorage.setItem("sitePages", JSON.stringify(pages));
}

/* ══════════════════════════════════════════════
   Staff Data (localStorage)
   ══════════════════════════════════════════════ */

function getStaff() {
  try { return JSON.parse(localStorage.getItem("siteStaff") || "[]"); }
  catch (e) { return []; }
}

/* ══════════════════════════════════════════════
   Posts Data (localStorage)
   ══════════════════════════════════════════════ */

function getPosts() {
  try { return JSON.parse(localStorage.getItem("sitePosts") || "[]"); }
  catch (e) { return []; }
}

/* ══════════════════════════════════════════════
   Testimonials Data (localStorage)
   ══════════════════════════════════════════════ */

function getTestimonials() {
  try { return JSON.parse(localStorage.getItem("siteTestimonials") || "[]"); }
  catch (e) { return []; }
}

function saveTestimonials(data) {
  localStorage.setItem("siteTestimonials", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Business Hours Data (localStorage)
   ══════════════════════════════════════════════ */

function getBusinessHours() {
  try { return JSON.parse(localStorage.getItem("siteBusinessHours") || "null"); }
  catch (e) { return null; }
}

function saveBusinessHours(data) {
  localStorage.setItem("siteBusinessHours", JSON.stringify(data));
}

function getDefaultBusinessHours() {
  var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  var schedule = {};
  days.forEach(function(day) {
    if (day === "Saturday" || day === "Sunday") {
      schedule[day] = { open: "", close: "", closed: true };
    } else {
      schedule[day] = { open: "09:00", close: "17:00", closed: false };
    }
  });
  return { schedule: schedule, closures: [] };
}

/* ══════════════════════════════════════════════
   Locations Data (localStorage)
   ══════════════════════════════════════════════ */

function getLocations() {
  try { return JSON.parse(localStorage.getItem("siteLocations") || "[]"); }
  catch (e) { return []; }
}

function saveLocations(data) {
  localStorage.setItem("siteLocations", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Office Locations Picklist (localStorage)
   ══════════════════════════════════════════════ */

function getOfficeLocations() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteOfficeLocations") || "null");
    if (stored && stored.length) return stored;
  } catch (e) {}
  return ["San Francisco", "Stockton"];
}

function saveOfficeLocations(data) {
  localStorage.setItem("siteOfficeLocations", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Page Visibility Toggles (localStorage)
   ══════════════════════════════════════════════ */

function getPageToggles() {
  try {
    var stored = JSON.parse(localStorage.getItem("sitePageToggles") || "null");
    if (stored) return stored;
  } catch (e) {}
  return { education: true, locations: true, staff: true, testimonials: true };
}

function savePageToggles(data) {
  localStorage.setItem("sitePageToggles", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Centralized Nav & Footer Settings (localStorage)
   ══════════════════════════════════════════════ */

function getNavFooterSettings() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteNavFooterSettings") || "null");
    if (stored) return stored;
  } catch (e) {}

  // Migration: construct defaults from existing settings
  var toggles = getPageToggles();
  var clockSettings = getClockSettings();

  return {
    nav: {
      home:             { visible: false, label: "Home",                href: "index.html" },
      services:         { visible: true,  label: "Services",            href: "index.html#services-grid" },
      staff:            { visible: toggles.staff !== false,             label: "Staff",               href: "staff.html" },
      testimonials:     { visible: toggles.testimonials !== false,      label: "Testimonials",        href: "testimonials.html" },
      education:        { visible: toggles.education !== false,         label: "Education",           href: "education.html" },
      locations:        { visible: toggles.locations !== false,         label: "Locations",           href: "locations.html" },
      careers:          { visible: false, label: "Careers",             href: "staff.html" },
      bookConsultation: { visible: true,  label: "Book a Consultation", href: "#", isCta: true }
    },
    globe: { visible: true, position: "hero-top-right" },
    maxNavItems: toggles.maxNavItems || 5,
    footer: {
      home:         { visible: true,  label: "Home",         href: "index.html" },
      services:     { visible: false, label: "Services",     href: "index.html#services-grid" },
      staff:        { visible: true,  label: "Our Team",     href: "staff.html" },
      testimonials: { visible: true,  label: "Testimonials", href: "testimonials.html" },
      education:    { visible: true,  label: "Education",    href: "education.html" },
      locations:    { visible: true,  label: "Locations",    href: "locations.html" },
      careers:      { visible: true,  label: "Careers",      href: "staff.html" }
    },
    copyright: "\u00a9 2026 O\u2019Brien Immigration Law. All rights reserved.",
    disclaimer: ""
  };
}

function saveNavFooterSettings(data) {
  localStorage.setItem("siteNavFooterSettings", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Contact Config (localStorage)
   ══════════════════════════════════════════════ */

function getContactConfig() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteContactConfig") || "null");
    if (stored) return stored;
  } catch (e) {}
  return { formspreeUrl: "https://formspree.io/f/mpqjddon" };
}

function saveContactConfig(data) {
  localStorage.setItem("siteContactConfig", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Clock Settings (localStorage)
   ══════════════════════════════════════════════ */

function getClockSettings() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteClockSettings") || "null");
    if (stored) return stored;
  } catch (e) {}
  return { visible: true, position: "center", label: "San Francisco" };
}

function saveClockSettings(data) {
  localStorage.setItem("siteClockSettings", JSON.stringify(data));
}

/* ══════════════════════════════════════════════
   Success Ribbon (localStorage)
   ══════════════════════════════════════════════ */

function getSuccessRibbon() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteSuccessRibbon") || "null");
    if (stored) return stored;
  } catch (e) {}
  return {
    enabled: true,
    phrases: [
      "Over 5,000 families reunited through our legal advocacy",
      "Recognized by the East Bay Sanctuary Covenant for pro bono excellence",
      "Serving the Bay Area and Central Valley since 2010",
      "Multilingual team fluent in Spanish, Portuguese, Nepali, and Hindi"
    ]
  };
}

function saveSuccessRibbon(data) {
  localStorage.setItem("siteSuccessRibbon", JSON.stringify(data));
}

function renderSuccessRibbon() {
  var ribbon = getSuccessRibbon();
  if (!ribbon.enabled || !ribbon.phrases || ribbon.phrases.length === 0) return;

  var hero = document.querySelector(".hero");
  if (!hero) return;

  var el = document.createElement("div");
  el.className = "success-ribbon";
  el.innerHTML = '<span class="success-ribbon-text" id="successRibbonText"></span>';

  // Insert after hero
  hero.parentNode.insertBefore(el, hero.nextSibling);

  var textEl = document.getElementById("successRibbonText");
  var phrases = ribbon.phrases;
  var idx = 0;

  function showPhrase() {
    textEl.textContent = phrases[idx];
    textEl.classList.add("visible");

    // Stay visible for 5 seconds, then fade out over 2 seconds
    setTimeout(function() {
      textEl.classList.remove("visible");
      // After fade-out completes, advance to next phrase
      setTimeout(function() {
        idx = (idx + 1) % phrases.length;
        showPhrase();
      }, 2000);
    }, 5000);
  }

  showPhrase();
}

/* ══════════════════════════════════════════════
   Path Finder Data (localStorage)
   ══════════════════════════════════════════════ */

function getPathFinderData() {
  try {
    var saved = JSON.parse(localStorage.getItem("sitePathFinder") || "null");
    if (saved && saved.paths && saved.paths.length > 0) return saved;
  } catch (e) {}
  return getDefaultPathFinderData();
}

function savePathFinderData(data) {
  localStorage.setItem("sitePathFinder", JSON.stringify(data));
}

function getDefaultPathFinderData() {
  return {
    paths: [
      {
        id: "citizen", label: "A U.S. Citizen",
        goals: [
          { id: "citizen-spouse", label: "Sponsor a spouse", process: "File Form I-130 (Petition for Alien Relative) with USCIS. As an immediate relative, your spouse has no visa queue wait. After approval, your spouse adjusts status (if in the U.S.) or goes through consular processing abroad.", timeline: "12\u201318 months", cta: "Request Deep Dive" },
          { id: "citizen-parent", label: "Sponsor a parent", process: "File Form I-130 for your parent. Parents of U.S. citizens are immediate relatives\u2014no visa backlog. If your parent is in the U.S., they may file Form I-485 concurrently to adjust status.", timeline: "12\u201318 months", cta: "Request Deep Dive" },
          { id: "citizen-fiance", label: "Apply for a fianc\u00e9(e) visa", process: "File Form I-129F (Petition for Alien Fianc\u00e9(e)) with USCIS. After approval, your fianc\u00e9(e) applies for a K-1 visa at a U.S. consulate. They must enter the U.S. and marry within 90 days, then apply to adjust status.", timeline: "8\u201314 months", cta: "Request Deep Dive" },
          { id: "citizen-sibling", label: "Sponsor a sibling", process: "File Form I-130 for your brother or sister. Siblings of U.S. citizens fall under the Family Fourth Preference (F4) category. Due to high demand, wait times can be significant depending on country of origin.", timeline: "7\u201324 years (varies by country)", cta: "Request Deep Dive" }
        ]
      },
      {
        id: "lpr", label: "A Lawful Permanent Resident",
        goals: [
          { id: "lpr-spouse", label: "Sponsor a spouse", process: "File Form I-130 for your spouse. Spouses of LPRs fall under the Family Second Preference (F2A) category. Wait times are shorter than other family preference categories but longer than immediate relative petitions.", timeline: "2\u20133 years", cta: "Request Deep Dive" },
          { id: "lpr-child", label: "Sponsor an unmarried child", process: "File Form I-130. Unmarried children under 21 qualify for F2A (shorter wait), while unmarried children over 21 fall into F2B (longer wait).", timeline: "2\u20137 years", cta: "Request Deep Dive" },
          { id: "lpr-naturalize", label: "Apply for U.S. citizenship", process: "If you\u2019ve been a permanent resident for 5 years (or 3 years if married to a U.S. citizen), you may file Form N-400 for naturalization. You\u2019ll need to pass an English and civics test and attend an interview.", timeline: "8\u201314 months after filing", cta: "Request Deep Dive" }
        ]
      },
      {
        id: "undocumented", label: "Undocumented / No Status",
        goals: [
          { id: "undoc-asylum", label: "Apply for asylum", process: "If you fear persecution in your home country based on race, religion, nationality, political opinion, or membership in a social group, you may file Form I-589 within one year of your last arrival. Asylum grants work authorization and a path to permanent residency.", timeline: "6 months \u2013 4+ years (depending on court backlog)", cta: "Request Deep Dive" },
          { id: "undoc-sij", label: "Special Immigrant Juvenile Status", process: "If you are under 21, unmarried, and have been abused, neglected, or abandoned by a parent, a state court may declare you a dependent. You can then file Form I-360 with USCIS to seek Special Immigrant Juvenile Status.", timeline: "1\u20133 years", cta: "Request Deep Dive" },
          { id: "undoc-u", label: "U-Visa (crime victim)", process: "If you were a victim of a qualifying crime in the U.S. and helped law enforcement, you may petition for a U nonimmigrant visa using Form I-918. U-Visas lead to work authorization and, after 3 years, eligibility for a green card.", timeline: "4\u20136+ years (significant backlog)", cta: "Request Deep Dive" },
          { id: "undoc-tps", label: "Temporary Protected Status", process: "If your home country is designated for TPS due to armed conflict, environmental disaster, or other extraordinary conditions, you may apply for temporary protection from deportation and work authorization.", timeline: "Depends on country designation", cta: "Request Deep Dive" }
        ]
      },
      {
        id: "visa", label: "A Visa Holder",
        goals: [
          { id: "visa-greencard", label: "Adjust to permanent residence", process: "Depending on your visa type, you may be eligible to adjust status to permanent residence through employment (EB categories) or family sponsorship. An employer typically files a PERM labor certification, then Form I-140, followed by Form I-485.", timeline: "1\u20135+ years (varies by category and country)", cta: "Request Deep Dive" },
          { id: "visa-extend", label: "Extend or change my visa", process: "File Form I-539 (for nonimmigrant status changes) or have your employer file Form I-129 (for work visa extensions). Apply before your current status expires.", timeline: "2\u20136 months", cta: "Request Deep Dive" },
          { id: "visa-h1b", label: "Transition to H-1B", process: "Your employer files Form I-129 with a Labor Condition Application. H-1B visas are subject to an annual cap (with exceptions for certain employers). If selected in the lottery, you can begin working October 1.", timeline: "3\u20138 months (if selected in lottery)", cta: "Request Deep Dive" }
        ]
      }
    ]
  };
}

/* ══════════════════════════════════════════════
   Bento Grid (localStorage driven)
   ══════════════════════════════════════════════ */

var BENTO_ICON_MAP = {
  scale: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M4 7l8-4 8 4"/><path d="M1 14l3-7 3 7a4.24 4.24 0 0 1-6 0z"/><path d="M17 14l3-7 3 7a4.24 4.24 0 0 1-6 0z"/></svg>',
  shield: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  users: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  document: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
};

function getBentoTiles() {
  var saved = localStorage.getItem("bentoTiles");
  if (saved) {
    var parsed = JSON.parse(saved);
    // Support both array format and old object format
    if (Array.isArray(parsed)) return parsed;
    // Convert old {tile1, tile2, tile3} format to array
    var arr = [];
    for (var key in parsed) {
      var t = parsed[key];
      t.id = t.id || key;
      arr.push(t);
    }
    return arr;
  }
  // Defaults
  return [
    { id: "tile1", title: "Family Petitions", description: "Reuniting families through spousal visas, parent and child petitions, and adjustment of status. We guide you through every step of the process.", icon: "users", layout: "large" },
    { id: "tile2", title: "Removal Defense", description: "Experienced representation in immigration court. We fight to protect your right to remain in the United States through asylum, cancellation of removal, and other forms of relief.", icon: "shield", layout: "large" },
    { id: "tile3", title: "Citizenship", description: "From naturalization applications to citizenship interviews, we help you reach the final milestone on your immigration journey.", icon: "document", layout: "medium" },
    { id: "tile4", title: "Work Visas", description: "H-1B, L-1, O-1 and other employment-based visas for professionals and their families.", icon: "scale", layout: "medium" },
    { id: "tile5", title: "Asylum", description: "Protection for those fleeing persecution. We build strong cases grounded in compassion and legal expertise.", icon: "shield", layout: "small" }
  ];
}

function renderBentoGrid() {
  var container = document.querySelector(".bento-grid");
  if (!container) return;

  var tiles = getBentoTiles();
  var layoutClasses = {
    wide: "card-wide", tall: "card-tall", short: "card-short",
    small: "card-small", medium: "card-medium", large: "card-large"
  };

  container.innerHTML = tiles.map(function(tile, idx) {
    var cls = layoutClasses[tile.layout] || "card-medium";
    var isImage = tile.displayMode === "image" && tile.bgImage;

    if (isImage) {
      return '<div class="card ' + cls + ' card-bg-image card-clickable reveal" data-tile-idx="' + idx + '" style="background-image:url(\'' + escapeHtmlUtil(tile.bgImage) + '\')">' +
        '<div class="card-bg-overlay"></div>' +
        '<div class="card-bg-content">' +
          '<h3>' + escapeHtmlUtil(tile.title) + '</h3>' +
          '<p>' + escapeHtmlUtil(tile.description) + '</p>' +
        '</div>' +
      '</div>';
    }

    var iconHtml = BENTO_ICON_MAP[tile.icon] || BENTO_ICON_MAP.scale;
    return '<div class="card ' + cls + ' card-clickable reveal" data-tile-idx="' + idx + '">' +
      '<div class="card-icon">' + iconHtml + '</div>' +
      '<h3>' + escapeHtmlUtil(tile.title) + '</h3>' +
      '<p>' + escapeHtmlUtil(tile.description) + '</p>' +
    '</div>';
  }).join('');

  // Bind click → modal for all tiles
  container.querySelectorAll(".card-clickable").forEach(function(card) {
    card.addEventListener("click", function() {
      var idx = parseInt(card.dataset.tileIdx, 10);
      var tile = tiles[idx];
      if (tile) openBentoModal(tile);
    });
  });

  // Re-observe for reveal animation
  container.querySelectorAll(".reveal").forEach(function(el) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    obs.observe(el);
  });
}

/* ── Bento Modal System ── */

var _bentoModalOpenTime = 0;
var _bentoModalTitle = "";

function openBentoModal(tile) {
  // Remove any existing modal
  var existing = document.getElementById("bentoModalOverlay");
  if (existing) existing.remove();

  _bentoModalOpenTime = Date.now();
  _bentoModalTitle = tile.title || "";

  var hasImage = tile.modalImage && tile.modalImage.trim();
  var layoutClass = hasImage ? "bento-modal--split" : "bento-modal--text-only";

  var overlay = document.createElement("div");
  overlay.id = "bentoModalOverlay";
  overlay.className = "bento-modal-overlay";
  overlay.innerHTML =
    '<div class="bento-modal-aurora"></div>' +
    '<div class="bento-modal ' + layoutClass + '">' +
      (hasImage ? '<div class="bento-modal-image"><img src="' + escapeHtmlUtil(tile.modalImage) + '" alt="' + escapeHtmlUtil(tile.title) + '"></div>' : '') +
      '<div class="bento-modal-body">' +
        '<h2 class="bento-modal-title">' + escapeHtmlUtil(tile.title) + '</h2>' +
        '<div class="bento-modal-desc">' + escapeHtmlUtil(tile.fullDescription || tile.description) + '</div>' +
        '<button class="bento-modal-cta" id="bentoModalCta">Book a Consultation</button>' +
      '</div>' +
      '<button class="bento-modal-close" aria-label="Close">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
      '</button>' +
    '</div>';

  document.body.appendChild(overlay);

  // Trigger entrance animation
  requestAnimationFrame(function() {
    overlay.classList.add("bento-modal-active");
  });

  // Close handlers
  overlay.querySelector(".bento-modal-close").addEventListener("click", closeBentoModal);
  overlay.addEventListener("click", function(e) {
    if (e.target === overlay) closeBentoModal();
  });
  document.addEventListener("keydown", bentoModalEscHandler);

  // CTA opens consultation modal
  document.getElementById("bentoModalCta").addEventListener("click", function() {
    closeBentoModal();
    openConsultModal();
  });
}

function closeBentoModal() {
  var overlay = document.getElementById("bentoModalOverlay");
  if (!overlay) return;

  // Track time-on-modal
  if (_bentoModalOpenTime && _bentoModalTitle && window.siteAnalytics) {
    var duration = Date.now() - _bentoModalOpenTime;
    siteAnalytics.trackModalTime(_bentoModalTitle, duration);
  }
  _bentoModalOpenTime = 0;
  _bentoModalTitle = "";

  overlay.classList.remove("bento-modal-active");
  overlay.classList.add("bento-modal-leaving");
  document.removeEventListener("keydown", bentoModalEscHandler);
  setTimeout(function() { overlay.remove(); }, 400);
}

function bentoModalEscHandler(e) {
  if (e.key === "Escape") closeBentoModal();
}

function escapeHtmlUtil(str) {
  var div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ══════════════════════════════════════════════
   Global Navigation (shared across all pages)
   ══════════════════════════════════════════════ */

function renderGlobalNav() {
  var nav = document.getElementById("globalNav");
  if (!nav) return;

  var settings = getNavFooterSettings();
  var navKeys = ["home", "services", "staff", "testimonials", "education", "locations", "careers"];

  // Build nav items from settings, filtering by visible
  var navItems = [];
  navKeys.forEach(function(key) {
    var item = settings.nav[key];
    if (item && item.visible) {
      navItems.push({ label: item.label, href: item.href });
    }
  });

  var maxVisible = settings.maxNavItems || 5;
  var visibleItems = navItems.slice(0, maxVisible);
  var overflowItems = navItems.slice(maxVisible);

  var linksHtml = visibleItems.map(function(item) {
    return '<li><a href="' + item.href + '">' + escapeHtmlUtil(item.label) + '</a></li>';
  }).join('');

  // Smart Collapse: group overflow into "More" dropdown
  if (overflowItems.length > 0) {
    var moreLinks = overflowItems.map(function(item) {
      return '<a href="' + item.href + '">' + escapeHtmlUtil(item.label) + '</a>';
    }).join('');
    linksHtml += '<li class="nav-more" id="navMore">' +
      '<button class="nav-more-trigger" aria-expanded="false">More ' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>' +
      '</button>' +
      '<div class="nav-more-dropdown">' + moreLinks + '</div>' +
    '</li>';
  }

  // CTA button
  var ctaItem = settings.nav.bookConsultation;
  if (ctaItem && ctaItem.visible) {
    linksHtml += '<li><a href="#" class="nav-cta">' + escapeHtmlUtil(ctaItem.label) + '</a></li>';
  }

  // Build mobile menu links (all visible items, no More dropdown)
  var allMobileItems = navItems;
  var mobileLinksHtml = allMobileItems.map(function(item) {
    return '<a href="' + item.href + '" class="mobile-menu-link">' + escapeHtmlUtil(item.label) + '</a>';
  }).join('');
  if (ctaItem && ctaItem.visible) {
    mobileLinksHtml += '<a href="#" class="mobile-menu-cta">' + escapeHtmlUtil(ctaItem.label) + '</a>';
  }

  nav.innerHTML =
    '<div class="nav-content">' +
      '<a href="index.html" class="nav-logo">O\u2019Brien Immigration</a>' +
      '<ul class="nav-links" id="navLinks">' + linksHtml + '</ul>' +
      '<button class="nav-hamburger" id="navHamburger" aria-label="Open menu">' +
        '<span></span><span></span><span></span>' +
      '</button>' +
    '</div>' +
    '<div class="mobile-menu-overlay" id="mobileMenuOverlay">' +
      '<div class="mobile-menu-panel">' +
        '<button class="mobile-menu-close" id="mobileMenuClose" aria-label="Close menu">&times;</button>' +
        '<div class="mobile-menu-links">' + mobileLinksHtml + '</div>' +
      '</div>' +
    '</div>';

  // Bind "More" dropdown toggle
  var moreEl = document.getElementById("navMore");
  if (moreEl) {
    var moreTrigger = moreEl.querySelector(".nav-more-trigger");
    moreTrigger.addEventListener("click", function(e) {
      e.stopPropagation();
      var isOpen = moreEl.classList.contains("open");
      moreEl.classList.toggle("open");
      moreTrigger.setAttribute("aria-expanded", !isOpen);
    });
    document.addEventListener("click", function() {
      moreEl.classList.remove("open");
      moreTrigger.setAttribute("aria-expanded", "false");
    });
  }

  // Mobile hamburger menu
  var hamburger = document.getElementById("navHamburger");
  var mobileOverlay = document.getElementById("mobileMenuOverlay");
  var mobileClose = document.getElementById("mobileMenuClose");

  if (hamburger && mobileOverlay) {
    hamburger.addEventListener("click", function() {
      mobileOverlay.classList.add("open");
      document.body.style.overflow = "hidden";
    });

    function closeMobileMenu() {
      mobileOverlay.classList.remove("open");
      document.body.style.overflow = "";
    }

    mobileClose.addEventListener("click", closeMobileMenu);
    mobileOverlay.addEventListener("click", function(e) {
      if (e.target === mobileOverlay) closeMobileMenu();
    });

    // Close on link click
    mobileOverlay.querySelectorAll(".mobile-menu-link").forEach(function(link) {
      link.addEventListener("click", closeMobileMenu);
    });

    // Mobile CTA opens consultation modal
    var mobileCta = mobileOverlay.querySelector(".mobile-menu-cta");
    if (mobileCta) {
      mobileCta.addEventListener("click", function(e) {
        e.preventDefault();
        closeMobileMenu();
        if (window.siteAnalytics) siteAnalytics.trackBookClick();
        openConsultModal();
      });
    }

    // Escape key
    document.addEventListener("keydown", function(e) {
      if (e.key === "Escape" && mobileOverlay.classList.contains("open")) {
        closeMobileMenu();
      }
    });
  }

  // Globe language button — always hero-top-right if visible
  if (settings.globe && settings.globe.visible) {
    var hero = document.querySelector(".hero");
    if (hero) {
      var heroLangBtn = document.createElement("button");
      heroLangBtn.className = "hero-lang-btn hero-lang-right";
      heroLangBtn.id = "heroLangBtn";
      heroLangBtn.setAttribute("aria-label", "Change language");
      heroLangBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>';
      heroLangBtn.addEventListener("click", function(e) {
        e.preventDefault();
        openLanguageModal();
      });
      hero.appendChild(heroLangBtn);
    }
  }

  // Inject hero clock if hero exists on this page
  initHeroClock();

  // Translation engine
  initTranslationEngine();

  // Admin shortcut button (subtle gear, bottom-left)
  var adminBtn = document.createElement("button");
  adminBtn.className = "admin-shortcut-btn";
  adminBtn.setAttribute("aria-label", "Open Admin Panel");
  adminBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>';
  adminBtn.addEventListener("click", function() {
    window.location.href = "admin.html";
  });
  document.body.appendChild(adminBtn);

  // Mobile FAB
  var fab = document.createElement("button");
  fab.className = "mobile-fab";
  fab.setAttribute("aria-label", "Book a Consultation");
  fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Book';
  fab.addEventListener("click", function() {
    if (window.siteAnalytics) siteAnalytics.trackBookClick();
    openConsultModal();
  });
  document.body.appendChild(fab);
}

/* ══════════════════════════════════════════════
   Dynamic Navigation
   ══════════════════════════════════════════════ */

function renderDynamicNav() {
  var navUl = document.getElementById("navLinks");
  if (!navUl) return;

  navUl.querySelectorAll(".dynamic-nav-link").forEach(function(el) { el.remove(); });

  // Only show published pages with showInNav
  var pages = getPages().filter(function(p) { return p.showInNav && p.published !== false; });

  // Filter out CMS pages that duplicate built-in nav items
  var settings = getNavFooterSettings();
  var builtInLabels = {};
  var navKeys = ["home", "services", "staff", "testimonials", "education", "locations", "careers"];
  navKeys.forEach(function(key) {
    var item = settings.nav[key];
    if (item) builtInLabels[item.label.toLowerCase()] = true;
  });

  pages = pages.filter(function(p) {
    return !builtInLabels[p.title.toLowerCase()];
  });

  var cta = navUl.querySelector(".nav-cta");
  var ctaLi = cta ? cta.closest("li") : null;

  var currentPath = window.location.pathname;
  var isIndexPage = currentPath.endsWith("/") || currentPath.endsWith("/index.html") || currentPath.endsWith("index.html");

  pages.forEach(function(page) {
    var li = document.createElement("li");
    li.className = "dynamic-nav-link";
    var a = document.createElement("a");
    a.href = "index.html?page=" + encodeURIComponent(page.slug);
    a.textContent = page.title;
    // Only use SPA navigation on index.html where the virtual router exists
    if (isIndexPage) {
      a.addEventListener("click", function(e) {
        e.preventDefault();
        navigateTo(page.slug);
      });
    }
    li.appendChild(a);
    if (ctaLi) {
      navUl.insertBefore(li, ctaLi);
    } else {
      navUl.appendChild(li);
    }
  });
}

function renderDynamicFooter() {
  var container = document.getElementById("footerLinks");
  if (!container) return;

  container.innerHTML = "";
  // Only show published pages with showInFooter
  var pages = getPages().filter(function(p) { return p.showInFooter && p.published !== false; });

  var currentPath = window.location.pathname;
  var isIndexPage = currentPath.endsWith("/") || currentPath.endsWith("/index.html") || currentPath.endsWith("index.html");

  pages.forEach(function(page) {
    var a = document.createElement("a");
    a.href = "index.html?page=" + encodeURIComponent(page.slug);
    a.textContent = page.title;
    // Only use SPA navigation on index.html where the virtual router exists
    if (isIndexPage) {
      a.addEventListener("click", function(e) {
        e.preventDefault();
        navigateTo(page.slug);
      });
    }
    container.appendChild(a);
  });

  // Populate static footer links from navFooter settings
  var settings = getNavFooterSettings();
  var staticContainer = document.getElementById("footerStaticLinks");
  if (staticContainer) {
    var footerKeys = ["home", "services", "staff", "testimonials", "education", "locations", "careers"];
    staticContainer.innerHTML = footerKeys.filter(function(key) {
      return settings.footer[key] && settings.footer[key].visible;
    }).map(function(key) {
      var item = settings.footer[key];
      return '<a href="' + item.href + '">' + escapeHtmlUtil(item.label) + '</a>';
    }).join('');
  }

  // Update copyright
  var copyrightEl = document.getElementById("footerCopyright");
  if (copyrightEl && settings.copyright) {
    copyrightEl.textContent = settings.copyright;
  }

  // Append disclaimer if set
  if (settings.disclaimer) {
    var existingDisclaimer = document.getElementById("footerDisclaimer");
    if (!existingDisclaimer) {
      var disclaimerP = document.createElement("p");
      disclaimerP.id = "footerDisclaimer";
      disclaimerP.style.cssText = "font-size:0.75rem;color:var(--mid-gray);margin-top:8px";
      disclaimerP.textContent = settings.disclaimer;
      var copyrightEl2 = document.getElementById("footerCopyright");
      if (copyrightEl2 && copyrightEl2.parentElement) {
        copyrightEl2.parentElement.appendChild(disclaimerP);
      }
    }
  }
}

/* ══════════════════════════════════════════════
   Virtual Router
   ══════════════════════════════════════════════ */

function navigateTo(slug) {
  var url = slug ? "index.html?page=" + encodeURIComponent(slug) : "index.html";
  history.pushState({ page: slug }, "", url);
  handleRoute();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function handleRoute() {
  var homeView = document.getElementById("homeView");
  var pageView = document.getElementById("pageView");
  var postView = document.getElementById("postView");
  if (!homeView || !pageView) return;

  var params = new URLSearchParams(window.location.search);
  var pageSlug = params.get("page");
  var postSlug = params.get("post");

  // Hide all views first
  homeView.style.display = "none";
  pageView.style.display = "none";
  if (postView) postView.style.display = "none";

  if (pageSlug) {
    var pages = getPages();
    var page = pages.find(function(p) { return p.slug === pageSlug; });
    if (page) {
      pageView.style.display = "block";
      document.getElementById("pageTitle").textContent = page.title;
      document.getElementById("pageBody").textContent = page.content;
      document.title = (page.seoTitle || page.title) + " \u2014 O\u2019Brien Immigration Law";

      var metaDesc = document.querySelector('meta[name="description"]');
      if (page.metaDescription) {
        if (!metaDesc) {
          metaDesc = document.createElement("meta");
          metaDesc.name = "description";
          document.head.appendChild(metaDesc);
        }
        metaDesc.content = page.metaDescription;
      } else if (metaDesc) {
        metaDesc.remove();
      }
      return;
    }
  }

  if (postSlug && postView) {
    var posts = getPosts();
    var post = posts.find(function(p) { return p.slug === postSlug; });
    if (post) {
      postView.style.display = "block";
      document.getElementById("postViewTitle").textContent = post.title;
      document.getElementById("postViewDate").textContent = post.date || "";
      document.getElementById("postViewCategory").textContent = post.category || "News";
      document.getElementById("postViewBody").innerHTML = post.content || "";
      document.title = post.title + " \u2014 O\u2019Brien Immigration Law";
      return;
    }
  }

  // Default: show home
  homeView.style.display = "";
  document.title = "O\u2019Brien Immigration Law";
}

/* ══════════════════════════════════════════════
   Staff Seed (populate localStorage if empty)
   ══════════════════════════════════════════════ */

function seedDefaultStaff() {
  if (getStaff().length > 0) return;

  var defaults = [
    { id: "s1", name: "Jeffrey O'Brien", title: "Founding Partner", office: "San Francisco", email: "info@obrienimmigration.com", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Founded the firm in 2010 with a mission to provide high-quality, affordable, and respectful legal representation to immigrants and their families. Recognized for pro bono work by the East Bay Sanctuary Covenant.", createdAt: "Feb 14, 2026" },
    { id: "s2", name: "Daska Babcock", title: "Senior Attorney", office: "Stockton", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Joined the firm in 2016 and launched the Central Valley office in 2017. Practices asylum cases and Special Immigrant Juvenile Status petitions. Fourteen years of civil litigation experience and recipient of the Father Cuchulain Moriarty Award.", createdAt: "Feb 14, 2026" },
    { id: "s3", name: "Elena Applebaum", title: "Senior Attorney", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Focuses on asylum and humanitarian petitions. Prior work with Jesuit Refugee Service in Malta and California immigration clinics. Fluent in multiple languages, including Spanish and Portuguese.", createdAt: "Feb 14, 2026" },
    { id: "s4", name: "Rosanna Katz", title: "Senior Attorney", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Joined the firm in 2016. Practices asylum cases and family-based petitions. Prior litigation experience and pro bono work through East Bay Sanctuary Covenant.", createdAt: "Feb 14, 2026" },
    { id: "s5", name: "Maria Amaya", title: "Senior Paralegal", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Colombian attorney managing case coordination, legal preparation, and team leadership. Handles deadlines, filings, evidence preparation, legal research, and motion drafting.", createdAt: "Feb 14, 2026" },
    { id: "s6", name: "Roshani Sitaula", title: "Senior Paralegal / Operations Director", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Joined in 2013 with over a decade of immigration law experience. Fluent in English, Nepali, and Hindi. Holds two Master\u2019s degrees in Environmental Management and Geology.", createdAt: "Feb 14, 2026" },
    { id: "s7", name: "Esteban Lasso", title: "Paralegal", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Supports case preparation, document review, and client communications. Background in law, international business, and project management. Multilingual.", createdAt: "Feb 14, 2026" },
    { id: "s8", name: "Guisselle Castellon", title: "Intake Specialist", office: "San Francisco", email: "", phone: "", imageUrl: "", showOnWebsite: true, hiring: false, bio: "Conducts client intake and screening in Spanish; assists with interpretation. Psychology background; helps identify asylum and family-based relief eligibility.", createdAt: "Feb 14, 2026" }
  ];
  localStorage.setItem("siteStaff", JSON.stringify(defaults));
}

/* ══════════════════════════════════════════════
   Posts / Newsroom (rendered from localStorage)
   ══════════════════════════════════════════════ */

function renderPostsSection() {
  var container = document.getElementById("postsGrid");
  if (!container) return;

  var posts = getPosts().filter(function(p) { return p.published !== false; });
  if (posts.length === 0) {
    container.innerHTML = "";
    var section = document.getElementById("postsSection");
    if (section) section.style.display = "none";
    return;
  }

  var section = document.getElementById("postsSection");
  if (section) section.style.display = "";

  // Sort by date descending
  posts.sort(function(a, b) { return (b.date || "").localeCompare(a.date || ""); });

  container.innerHTML = posts.map(function(post) {
    return '<a href="index.html?post=' + encodeURIComponent(post.slug) + '" class="post-card reveal" data-slug="' + escapeHtmlUtil(post.slug) + '">' +
      '<span class="post-category">' + escapeHtmlUtil(post.category || "News") + '</span>' +
      '<h3 class="post-title">' + escapeHtmlUtil(post.title) + '</h3>' +
      '<time class="post-date">' + escapeHtmlUtil(post.date || "") + '</time>' +
    '</a>';
  }).join('');

  // Bind navigation
  container.querySelectorAll(".post-card").forEach(function(card) {
    card.addEventListener("click", function(e) {
      e.preventDefault();
      var slug = card.dataset.slug;
      history.pushState({ post: slug }, "", "index.html?post=" + encodeURIComponent(slug));
      handleRoute();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  container.querySelectorAll(".reveal").forEach(function(el) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    obs.observe(el);
  });
}

/* ══════════════════════════════════════════════
   CSS Variable Settings
   ══════════════════════════════════════════════ */

var BTN_STYLES = {
  pill: { "--btn-radius": "980px", "--btn-bg": "var(--accent-color)", "--btn-color": "var(--white)", "--btn-border": "none", "--btn-backdrop": "none" },
  modern: { "--btn-radius": "8px", "--btn-bg": "var(--accent-color)", "--btn-color": "var(--white)", "--btn-border": "none", "--btn-backdrop": "none" },
  glass: { "--btn-radius": "980px", "--btn-bg": "rgba(255,255,255,0.15)", "--btn-color": "var(--dark)", "--btn-border": "1px solid rgba(0,0,0,0.12)", "--btn-backdrop": "saturate(180%) blur(12px)" }
};

function applySiteSettings(settings) {
  var root = document.documentElement;
  for (var key in settings) {
    if (settings[key]) {
      // Don't override the CSS default hero image with "none"
      if (key === "--hero-bg-image" && settings[key] === "none") continue;
      // Night image is handled by the adaptive image engine, not as a CSS var
      if (key === "--hero-bg-image-night") continue;
      root.style.setProperty(key, settings[key]);
    }
  }
  // Apply button style engine
  var style = settings["--btn-style"] || "pill";
  var vars = BTN_STYLES[style] || BTN_STYLES.pill;
  for (var k in vars) {
    root.style.setProperty(k, vars[k]);
  }
}

function loadSiteSettings() {
  var saved = localStorage.getItem("siteSettings");
  if (saved) {
    applySiteSettings(JSON.parse(saved));
  }
}

function saveSiteSettings(settings) {
  localStorage.setItem("siteSettings", JSON.stringify(settings));
  applySiteSettings(settings);
}

/* ══════════════════════════════════════════════
   Consultation Modal
   ══════════════════════════════════════════════ */

function isConsultEnabled() {
  try {
    var settings = JSON.parse(localStorage.getItem("siteSettings") || "{}");
    return settings["--consult-popup"] !== "disabled";
  } catch (e) { return true; }
}

function buildConsultModal() {
  if (document.getElementById("consultOverlay")) return;

  var contactConfig = getContactConfig();
  var formUrl = contactConfig.formspreeUrl || "https://formspree.io/f/mpqjddon";

  // Build Path Finder picklist options for the form
  var pfData = getPathFinderData();
  var statusOptions = pfData.paths.map(function(p) {
    return '<option value="' + escapeHtmlUtil(p.id) + '">' + escapeHtmlUtil(p.label) + '</option>';
  }).join('');

  // Build office location options
  var officeLocations = getOfficeLocations();
  var officeOptions = officeLocations.map(function(loc) {
    return '<option value="' + escapeHtmlUtil(loc) + '">' + escapeHtmlUtil(loc) + '</option>';
  }).join('');

  var overlay = document.createElement("div");
  overlay.id = "consultOverlay";
  overlay.className = "consult-overlay";
  overlay.innerHTML =
    '<div class="consult-modal">' +
      '<button class="consult-close" aria-label="Close">&times;</button>' +
      '<form id="consultForm" action="' + escapeHtmlUtil(formUrl) + '" method="POST">' +
        '<h2>Book a Consultation</h2>' +
        '<p class="consult-sub">Tell us about your situation and we\u2019ll get back to you within 24 hours.</p>' +
        '<input type="hidden" name="_next" value="' + window.location.origin + '/thank-you.html">' +
        '<input type="hidden" name="_subject" id="consultSubject" value="New Consultation Request">' +
        '<div class="consult-form-row">' +
          '<div class="consult-form-group">' +
            '<label for="consultName">Name</label>' +
            '<input type="text" id="consultName" name="name" required placeholder="Your full name">' +
          '</div>' +
          '<div class="consult-form-group">' +
            '<label for="consultPhone">Phone</label>' +
            '<input type="tel" id="consultPhone" name="phone" placeholder="(555) 123-4567">' +
          '</div>' +
        '</div>' +
        '<div class="consult-form-group">' +
          '<label for="consultEmail">Email</label>' +
          '<input type="email" id="consultEmail" name="email" required placeholder="you@example.com">' +
        '</div>' +
        '<div class="consult-form-row">' +
          '<div class="consult-form-group">' +
            '<label for="consultStatus">I am\u2026</label>' +
            '<select id="consultStatus" name="status">' +
              '<option value="">Choose your status</option>' +
              statusOptions +
            '</select>' +
          '</div>' +
          '<div class="consult-form-group">' +
            '<label for="consultGoal">And I want to\u2026</label>' +
            '<select id="consultGoal" name="goal" disabled>' +
              '<option value="">Choose your goal</option>' +
            '</select>' +
          '</div>' +
        '</div>' +
        '<div class="consult-form-group">' +
          '<label for="consultOffice">Preferred Office</label>' +
          '<select id="consultOffice" name="preferred_office">' +
            '<option value="">No preference</option>' +
            officeOptions +
          '</select>' +
        '</div>' +
        '<div class="consult-form-group">' +
          '<label for="consultMessage">Message</label>' +
          '<textarea id="consultMessage" name="message" placeholder="Briefly describe your situation\u2026"></textarea>' +
        '</div>' +
        '<button type="submit" class="consult-submit">Send Request</button>' +
      '</form>' +
    '</div>';
  document.body.appendChild(overlay);

  // Dependent goal picklist
  var statusSelect = document.getElementById("consultStatus");
  var goalSelect = document.getElementById("consultGoal");
  statusSelect.addEventListener("change", function() {
    var path = pfData.paths.find(function(p) { return p.id === statusSelect.value; });
    if (path && path.goals) {
      goalSelect.disabled = false;
      goalSelect.innerHTML = '<option value="">Choose your goal</option>' +
        path.goals.map(function(g) {
          return '<option value="' + escapeHtmlUtil(g.id) + '">' + escapeHtmlUtil(g.label) + '</option>';
        }).join('');
      if (window.siteAnalytics) {
        var sOpt = statusSelect.options[statusSelect.selectedIndex];
        siteAnalytics.trackPathFinderChoice("status", statusSelect.value, sOpt ? sOpt.text : "");
      }
    } else {
      goalSelect.disabled = true;
      goalSelect.innerHTML = '<option value="">Choose your goal</option>';
    }
    updateConsultSubject();
  });
  goalSelect.addEventListener("change", function() {
    updateConsultSubject();
    if (window.siteAnalytics && goalSelect.value) {
      var gOpt = goalSelect.options[goalSelect.selectedIndex];
      siteAnalytics.trackPathFinderChoice("goal", goalSelect.value, gOpt ? gOpt.text : "");
    }
  });

  function updateConsultSubject() {
    var statusText = statusSelect.options[statusSelect.selectedIndex] ? statusSelect.options[statusSelect.selectedIndex].text : "";
    var goalText = goalSelect.options[goalSelect.selectedIndex] ? goalSelect.options[goalSelect.selectedIndex].text : "";
    var subject = "Consultation: " + statusText;
    if (goalText && goalText !== "Choose your goal") subject += " \u2014 " + goalText;
    document.getElementById("consultSubject").value = subject || "New Consultation Request";
  }

  // Close on overlay background click
  overlay.addEventListener("click", function(e) {
    if (e.target === overlay) closeConsultModal();
  });

  // Close button
  overlay.querySelector(".consult-close").addEventListener("click", closeConsultModal);

  // Escape key
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && overlay.classList.contains("visible")) {
      closeConsultModal();
    }
  });

  // Client-side validation highlight + analytics tracking
  overlay.querySelector("#consultForm").addEventListener("submit", function(e) {
    var name = document.getElementById("consultName");
    var email = document.getElementById("consultEmail");
    if (!name.value.trim() || !email.value.trim()) {
      e.preventDefault();
      if (!name.value.trim()) name.style.borderColor = "#d63031";
      if (!email.value.trim()) email.style.borderColor = "#d63031";
      setTimeout(function() {
        name.style.borderColor = "";
        email.style.borderColor = "";
      }, 1500);
    } else {
      // Track successful submission
      if (window.siteAnalytics) {
        var sOpt = statusSelect.options[statusSelect.selectedIndex];
        var gOpt = goalSelect.options[goalSelect.selectedIndex];
        siteAnalytics.trackFormSubmission(
          sOpt ? sOpt.text : "",
          gOpt ? gOpt.text : ""
        );
      }
    }
  });
}

function openConsultModal(prefill) {
  if (!isConsultEnabled()) return;
  buildConsultModal();

  // Reset form state
  var form = document.getElementById("consultForm");
  var success = document.getElementById("consultSuccess");
  if (form) {
    form.style.display = "";
    form.querySelectorAll("input:not([type=hidden]), select, textarea").forEach(function(el) {
      if (el.tagName === "SELECT") {
        el.selectedIndex = 0;
        if (el.id === "consultGoal") el.disabled = true;
      } else {
        el.value = "";
      }
    });
  }
  if (success) success.classList.remove("visible");

  // Pre-fill from Education Hub bridge
  if (prefill) {
    var statusSelect = document.getElementById("consultStatus");
    var goalSelect = document.getElementById("consultGoal");
    if (prefill.statusId && statusSelect) {
      statusSelect.value = prefill.statusId;
      statusSelect.dispatchEvent(new Event("change"));
      // Set goal after the change event populates options
      if (prefill.goalId && goalSelect) {
        setTimeout(function() {
          goalSelect.value = prefill.goalId;
          goalSelect.dispatchEvent(new Event("change"));
        }, 50);
      }
    }
  }

  var overlay = document.getElementById("consultOverlay");
  requestAnimationFrame(function() { overlay.classList.add("visible"); });
}

function closeConsultModal() {
  var overlay = document.getElementById("consultOverlay");
  if (overlay) overlay.classList.remove("visible");
}

function initConsultButtons() {
  if (!isConsultEnabled()) return;

  document.querySelectorAll(".nav-cta, .hero-btn").forEach(function(btn) {
    if (btn.textContent.trim() === "Book a Consultation") {
      btn.addEventListener("click", function(e) {
        e.preventDefault();
        if (window.siteAnalytics) siteAnalytics.trackBookClick();
        openConsultModal();
      });
    }
  });
}

/* ══════════════════════════════════════════════
   Dark Mode Toggle
   ══════════════════════════════════════════════ */

function initDarkMode() {
  // Restore saved preference
  var saved = localStorage.getItem("theme");
  if (saved === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  }

  // Build toggle button
  var toggle = document.createElement("button");
  toggle.className = "theme-toggle";
  toggle.setAttribute("aria-label", "Toggle dark mode");
  toggle.innerHTML =
    '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>' +
    '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  document.body.appendChild(toggle);

  toggle.addEventListener("click", function() {
    var isDark = document.documentElement.getAttribute("data-theme") === "dark";
    if (isDark) {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("theme", "dark");
    }
    // Trigger adaptive image swap on theme change
    applyAdaptiveImages();
  });
}

/* ══════════════════════════════════════════════
   Adaptive Image Engine (Day/Night cross-fade)
   ══════════════════════════════════════════════ */

function isNightMode() {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function applyAdaptiveImages() {
  var isDark = isNightMode();
  var settings = {};
  try { settings = JSON.parse(localStorage.getItem("siteSettings") || "{}"); } catch (e) {}

  // ── Hero cross-fade ──
  var hero = document.querySelector(".hero");
  if (hero) {
    var dayUrl = settings["--hero-bg-image"] || "";
    var nightUrl = settings["--hero-bg-image-night"] || "";

    // Extract raw URL from css url() wrapper
    dayUrl = dayUrl.replace(/^url\(["']?/, "").replace(/["']?\)$/, "");
    nightUrl = nightUrl.replace(/^url\(["']?/, "").replace(/["']?\)$/, "");
    if (dayUrl === "none") dayUrl = "";
    if (nightUrl === "none") nightUrl = "";

    var targetUrl = "";
    var useSmartFilter = false;

    if (isDark) {
      if (nightUrl) {
        targetUrl = nightUrl;
      } else if (dayUrl) {
        targetUrl = dayUrl;
        useSmartFilter = true;
      }
    } else {
      targetUrl = dayUrl;
    }

    crossFadeHero(hero, targetUrl, useSmartFilter);
  }

  // ── Location hero cross-fade ──
  var locHero = document.getElementById("locationHero");
  if (locHero && locHero.dataset.dayPhoto) {
    var locDay = locHero.dataset.dayPhoto;
    var locNight = locHero.dataset.nightPhoto || "";
    var locTarget = "";
    var locFilter = false;

    if (isDark) {
      if (locNight) {
        locTarget = locNight;
      } else if (locDay) {
        locTarget = locDay;
        locFilter = true;
      }
    } else {
      locTarget = locDay;
    }

    crossFadeLocationHero(locHero, locTarget, locFilter);
  }
}

function crossFadeHero(hero, imageUrl, useSmartFilter) {
  // Use a ::after layer for cross-fade to avoid blinking
  var fadeLayer = hero.querySelector(".hero-crossfade");
  if (!fadeLayer) {
    fadeLayer = document.createElement("div");
    fadeLayer.className = "hero-crossfade";
    hero.insertBefore(fadeLayer, hero.firstChild);
  }

  if (imageUrl) {
    fadeLayer.style.backgroundImage = "url('" + imageUrl + "')";
  } else {
    fadeLayer.style.backgroundImage = "";
  }

  if (useSmartFilter) {
    fadeLayer.style.filter = "brightness(0.5) contrast(1.1)";
  } else {
    fadeLayer.style.filter = "";
  }

  // Trigger cross-fade: fade in the new layer, then swap to base
  fadeLayer.classList.add("active");

  setTimeout(function() {
    // After fade completes, update the base hero and remove the layer
    if (imageUrl) {
      hero.style.backgroundImage = "url('" + imageUrl + "')";
    }
    if (useSmartFilter) {
      hero.classList.add("hero-night-filter");
    } else {
      hero.classList.remove("hero-night-filter");
    }
    fadeLayer.classList.remove("active");
    fadeLayer.style.backgroundImage = "";
    fadeLayer.style.filter = "";
  }, 3000);
}

function crossFadeLocationHero(locHero, imageUrl, useSmartFilter) {
  var fadeLayer = locHero.querySelector(".location-hero-crossfade");
  if (!fadeLayer) {
    fadeLayer = document.createElement("div");
    fadeLayer.className = "location-hero-crossfade";
    locHero.insertBefore(fadeLayer, locHero.firstChild);
  }

  if (imageUrl) {
    fadeLayer.style.backgroundImage = "url('" + imageUrl + "')";
  } else {
    fadeLayer.style.backgroundImage = "";
  }

  if (useSmartFilter) {
    fadeLayer.style.filter = "brightness(0.5) contrast(1.1)";
  } else {
    fadeLayer.style.filter = "";
  }

  fadeLayer.classList.add("active");

  setTimeout(function() {
    if (imageUrl) {
      locHero.style.backgroundImage = "url('" + imageUrl + "')";
    }
    if (useSmartFilter) {
      locHero.classList.add("location-hero-night-filter");
    } else {
      locHero.classList.remove("location-hero-night-filter");
    }
    fadeLayer.classList.remove("active");
    fadeLayer.style.backgroundImage = "";
    fadeLayer.style.filter = "";
  }, 3000);
}

/* ══════════════════════════════════════════════
   Living Clock & Status Engine
   ══════════════════════════════════════════════ */

function getOfficeStatus() {
  var hours = getBusinessHours() || getDefaultBusinessHours();
  var now = new Date();
  var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  var dayName = days[now.getDay()];
  var schedule = hours.schedule[dayName];

  // Check special closures
  var month = String(now.getMonth() + 1).padStart(2, "0");
  var date = String(now.getDate()).padStart(2, "0");
  var todayStr = now.getFullYear() + "-" + month + "-" + date;

  var closures = hours.closures || [];
  for (var i = 0; i < closures.length; i++) {
    if (closures[i].date === todayStr) {
      return { status: "holiday", label: closures[i].label || "Holiday", color: "red" };
    }
  }

  if (!schedule || schedule.closed || !schedule.open || !schedule.close) {
    return { status: "closed", label: "Closed", color: "amber" };
  }

  var nowMinutes = now.getHours() * 60 + now.getMinutes();
  var openParts = schedule.open.split(":");
  var closeParts = schedule.close.split(":");
  var openMinutes = parseInt(openParts[0]) * 60 + parseInt(openParts[1]);
  var closeMinutes = parseInt(closeParts[0]) * 60 + parseInt(closeParts[1]);

  if (nowMinutes >= openMinutes && nowMinutes < closeMinutes) {
    return { status: "open", label: "Open", color: "green" };
  }
  return { status: "closed", label: "Closed", color: "amber" };
}

function formatClockTime(date) {
  var h = date.getHours();
  var m = String(date.getMinutes()).padStart(2, "0");
  var ampm = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return h + ":" + m + " " + ampm;
}

var _lastSunAwareTheme = null;

function initHeroClock() {
  var settings = getClockSettings();

  // If clock is hidden via admin, don't render it
  if (settings.visible === false) return;

  var heroInner = document.querySelector(".hero-inner");
  var hero = document.querySelector(".hero");
  if (!heroInner || !hero) return;

  // Create the clock whisper element
  var clockLine = document.createElement("div");
  clockLine.className = "hero-clock-line reveal";

  // Apply positioning from settings
  var pos = settings.position || "center";
  if (pos !== "center") {
    clockLine.classList.add("clock-positioned", "clock-" + pos);
    // Positioned clock goes in the hero (absolute), not hero-inner
    hero.appendChild(clockLine);
  } else {
    heroInner.insertBefore(clockLine, heroInner.firstChild);
  }

  clockLine.innerHTML = '<span class="status-dot" id="statusDot"></span><span id="clockText" class="hero-clock-text"></span>';

  var clockEl = document.getElementById("clockText");
  var dotEl = document.getElementById("statusDot");
  var cityLabel = settings.label || "San Francisco";

  function update() {
    var now = new Date();
    var timeStr = formatClockTime(now);
    var info = getOfficeStatus();

    clockEl.textContent = cityLabel + ", CA \u2014 " + timeStr + " \u00b7 Office is " + info.label;
    dotEl.className = "status-dot status-" + info.color;

    // Sun-aware auto-transition at 6 PM / 6 AM
    var hour = now.getHours();
    var shouldBeNight = hour >= 18 || hour < 6;
    var currentTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";

    if (_lastSunAwareTheme !== null && _lastSunAwareTheme !== shouldBeNight) {
      if (shouldBeNight && currentTheme !== "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        applyAdaptiveImages();
      } else if (!shouldBeNight && currentTheme === "dark") {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("theme", "light");
        applyAdaptiveImages();
      }
    }
    _lastSunAwareTheme = shouldBeNight;
  }

  update();
  setInterval(update, 30000);
}

/* ══════════════════════════════════════════════
   Magnetic Button Effect
   ══════════════════════════════════════════════ */

function initMagneticButtons() {
  var selectors = ".nav-cta, .hero-btn, .consult-submit";
  document.querySelectorAll(selectors).forEach(function(btn) {
    btn.addEventListener("mousemove", function(e) {
      var rect = btn.getBoundingClientRect();
      var x = e.clientX - rect.left - rect.width / 2;
      var y = e.clientY - rect.top - rect.height / 2;
      btn.style.transform = "translate(" + (x * 0.15) + "px, " + (y * 0.15) + "px)";
    });

    btn.addEventListener("mouseleave", function() {
      btn.style.transform = "";
    });
  });
}

/* ══════════════════════════════════════════════
   Ambient Glow (cursor-following light)
   ══════════════════════════════════════════════ */

function initAmbientGlow() {
  var glow = document.createElement("div");
  glow.className = "ambient-glow";
  document.body.appendChild(glow);

  var targetX = 0, targetY = 0;
  var currentX = 0, currentY = 0;
  var rafId = null;

  document.addEventListener("mousemove", function(e) {
    targetX = e.clientX;
    targetY = e.clientY;
    if (!rafId) tick();
  });

  function tick() {
    // Ease toward target (0.08 = smooth lag)
    currentX += (targetX - currentX) * 0.08;
    currentY += (targetY - currentY) * 0.08;

    glow.style.left = currentX + "px";
    glow.style.top = currentY + "px";

    // Keep animating while there's meaningful distance
    if (Math.abs(targetX - currentX) > 0.5 || Math.abs(targetY - currentY) > 0.5) {
      rafId = requestAnimationFrame(tick);
    } else {
      rafId = null;
    }
  }
}

/* ══════════════════════════════════════════════
   Bento Perspective Tilt
   ══════════════════════════════════════════════ */

/* ══════════════════════════════════════════════
   Aurora Glow (cursor tracking on nav & buttons)
   ══════════════════════════════════════════════ */

function initAuroraGlow() {
  var selectors = ".nav-links a, .nav-cta, .hero-btn, .consult-submit, .mobile-fab";

  document.addEventListener("mousemove", function(e) {
    document.querySelectorAll(selectors).forEach(function(el) {
      var rect = el.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      el.style.setProperty("--glow-x", x + "px");
      el.style.setProperty("--glow-y", y + "px");
    });
  });
}

/* ══════════════════════════════════════════════
   Page Transition Fade
   ══════════════════════════════════════════════ */

function initPageTransitions() {
  // Fade in on page load
  document.body.classList.add("page-loaded");

  document.addEventListener("click", function(e) {
    var link = e.target.closest("a[href]");
    if (!link) return;

    var href = link.getAttribute("href");
    if (!href) return;

    // Skip anchors, javascript:, external links, and CTA buttons
    if (href.charAt(0) === "#" || href.indexOf("javascript:") === 0) return;
    if (href.indexOf("mailto:") === 0 || href.indexOf("tel:") === 0) return;
    if (link.target === "_blank") return;
    if (link.classList.contains("nav-cta") || link.classList.contains("hero-btn")) return;

    // Only intercept local .html links
    if (href.indexOf(".html") === -1) return;

    // Don't intercept same-page anchor links (e.g., index.html#services-grid)
    if (href.indexOf("#") !== -1) {
      var parts = href.split("#");
      var currentPage = window.location.pathname.split("/").pop() || "index.html";
      if (parts[0] === currentPage || parts[0] === "") return;
    }

    e.preventDefault();
    document.body.classList.add("page-leaving");

    setTimeout(function() {
      window.location.href = href;
    }, 400);
  });
}

/* ══════════════════════════════════════════════
   Smooth Scroll for Internal Links
   ══════════════════════════════════════════════ */

/* ══════════════════════════════════════════════
   Smart Translation System
   ══════════════════════════════════════════════ */

var TRANSLATE_LANGUAGES = [
  { code: "es", label: "Espa\u00f1ol", flag: "\ud83c\uddea\ud83c\uddf8" },
  { code: "zh-CN", label: "\u4e2d\u6587", flag: "\ud83c\udde8\ud83c\uddf3" },
  { code: "vi", label: "Ti\u1ebfng Vi\u1ec7t", flag: "\ud83c\uddfb\ud83c\uddf3" },
  { code: "ko", label: "\ud55c\uad6d\uc5b4", flag: "\ud83c\uddf0\ud83c\uddf7" },
  { code: "tl", label: "Tagalog", flag: "\ud83c\uddf5\ud83c\udded" },
  { code: "ar", label: "\u0627\u0644\u0639\u0631\u0628\u064a\u0629", flag: "\ud83c\uddf8\ud83c\udde6" },
  { code: "fr", label: "Fran\u00e7ais", flag: "\ud83c\uddeb\ud83c\uddf7" },
  { code: "pt", label: "Portugu\u00eas", flag: "\ud83c\udde7\ud83c\uddf7" },
  { code: "ru", label: "\u0420\u0443\u0441\u0441\u043a\u0438\u0439", flag: "\ud83c\uddf7\ud83c\uddfa" },
  { code: "hi", label: "\u0939\u093f\u0928\u094d\u0926\u0940", flag: "\ud83c\uddee\ud83c\uddf3" }
];

function getTranslationSettings() {
  try {
    var stored = JSON.parse(localStorage.getItem("siteTranslation") || "null");
    if (stored) return stored;
  } catch (e) {}
  return { disclaimer: "This translation is automated for your convenience. For legal precision, please refer to the English original." };
}

function getSelectedLanguage() {
  return localStorage.getItem("siteLanguage") || "";
}

function setSelectedLanguage(langCode) {
  localStorage.setItem("siteLanguage", langCode);
}

function initTranslationEngine() {
  // Inject hidden Google Translate element
  var gtDiv = document.createElement("div");
  gtDiv.id = "google_translate_element";
  gtDiv.style.cssText = "position:absolute;top:-9999px;left:-9999px;opacity:0;pointer-events:none";
  document.body.appendChild(gtDiv);

  // Load Google Translate script
  window.googleTranslateElementInit = function() {
    new google.translate.TranslateElement({
      pageLanguage: "en",
      autoDisplay: false,
      layout: google.translate.TranslateElement.InlineLayout.SIMPLE
    }, "google_translate_element");

    // After Google Translate initializes, apply saved or auto-detected language
    setTimeout(function() {
      var saved = getSelectedLanguage();
      if (saved && saved !== "en") {
        triggerGoogleTranslate(saved);
        showTranslationDisclaimer();
      } else if (!saved) {
        autoDetectLanguage();
      }
    }, 1000);
  };

  var script = document.createElement("script");
  script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
  script.async = true;
  document.head.appendChild(script);
}

function autoDetectLanguage() {
  var browserLang = (navigator.language || navigator.userLanguage || "en").toLowerCase();
  // Check if browser language matches any of our supported languages
  for (var i = 0; i < TRANSLATE_LANGUAGES.length; i++) {
    var lang = TRANSLATE_LANGUAGES[i];
    if (browserLang === lang.code.toLowerCase() || browserLang.split("-")[0] === lang.code.split("-")[0].toLowerCase()) {
      setSelectedLanguage(lang.code);
      triggerGoogleTranslate(lang.code);
      showTranslationDisclaimer();
      return;
    }
  }
}

function triggerGoogleTranslate(langCode) {
  // Google Translate uses a cookie to set language
  var domain = window.location.hostname;
  document.cookie = "googtrans=/en/" + langCode + ";path=/;domain=" + domain;
  document.cookie = "googtrans=/en/" + langCode + ";path=/";

  // Try the combo box immediately, then retry if not yet loaded
  function tryCombo() {
    var select = document.querySelector(".goog-te-combo");
    if (select) {
      select.value = langCode;
      select.dispatchEvent(new Event("change"));
      return true;
    }
    return false;
  }

  if (!tryCombo()) {
    // Retry a few times as Google Translate widget may still be loading
    var attempts = 0;
    var retryInterval = setInterval(function() {
      attempts++;
      if (tryCombo() || attempts >= 10) {
        clearInterval(retryInterval);
      }
    }, 500);
  }
}

function showTranslationDisclaimer() {
  if (document.getElementById("translationDisclaimer")) return;

  var settings = getTranslationSettings();
  var disclaimer = settings.disclaimer || "";
  if (!disclaimer) return;

  var bar = document.createElement("div");
  bar.id = "translationDisclaimer";
  bar.className = "translation-disclaimer";
  bar.innerHTML = '<span>' + escapeHtmlUtil(disclaimer) + '</span>' +
    '<button class="translation-disclaimer-close" aria-label="Dismiss">&times;</button>';
  document.body.appendChild(bar);

  requestAnimationFrame(function() {
    bar.classList.add("visible");
  });

  bar.querySelector(".translation-disclaimer-close").addEventListener("click", function() {
    bar.classList.remove("visible");
    setTimeout(function() { bar.remove(); }, 300);
  });
}

function removeTranslationDisclaimer() {
  var bar = document.getElementById("translationDisclaimer");
  if (bar) {
    bar.classList.remove("visible");
    setTimeout(function() { bar.remove(); }, 300);
  }
}

function openLanguageModal() {
  var existing = document.getElementById("langModalOverlay");
  if (existing) existing.remove();

  var currentLang = getSelectedLanguage();

  var langItems = '<a class="lang-option' + (!currentLang || currentLang === "en" ? " lang-active" : "") + '" data-lang="en">' +
    '<span class="lang-flag">\ud83c\uddfa\ud83c\uddf8</span><span class="lang-label">English</span></a>';

  langItems += TRANSLATE_LANGUAGES.map(function(lang) {
    var activeClass = currentLang === lang.code ? " lang-active" : "";
    return '<a class="lang-option' + activeClass + '" data-lang="' + lang.code + '">' +
      '<span class="lang-flag">' + lang.flag + '</span><span class="lang-label">' + lang.label + '</span></a>';
  }).join('');

  var overlay = document.createElement("div");
  overlay.id = "langModalOverlay";
  overlay.className = "lang-modal-overlay";
  overlay.innerHTML =
    '<div class="lang-modal">' +
      '<div class="lang-modal-header">' +
        '<h3>Choose Language</h3>' +
        '<button class="lang-modal-close" aria-label="Close">' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
        '</button>' +
      '</div>' +
      '<div class="lang-modal-grid">' + langItems + '</div>' +
    '</div>';

  document.body.appendChild(overlay);

  requestAnimationFrame(function() {
    overlay.classList.add("lang-modal-active");
  });

  // Close handlers
  overlay.querySelector(".lang-modal-close").addEventListener("click", closeLanguageModal);
  overlay.addEventListener("click", function(e) {
    if (e.target === overlay) closeLanguageModal();
  });

  // Language selection
  overlay.querySelectorAll(".lang-option").forEach(function(opt) {
    opt.addEventListener("click", function() {
      var lang = opt.dataset.lang;
      setSelectedLanguage(lang);
      if (window.siteAnalytics) siteAnalytics.trackLanguageChange(lang);

      if (lang === "en") {
        // Reset to English — remove Google Translate cookie and reload
        document.cookie = "googtrans=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie = "googtrans=;path=/;domain=" + window.location.hostname + ";expires=Thu, 01 Jan 1970 00:00:00 GMT";
        removeTranslationDisclaimer();
        closeLanguageModal();
        window.location.reload();
      } else {
        triggerGoogleTranslate(lang);
        showTranslationDisclaimer();
        closeLanguageModal();
        // Reload for Google Translate to take effect with cookie
        window.location.reload();
      }
    });
  });
}

function closeLanguageModal() {
  var overlay = document.getElementById("langModalOverlay");
  if (!overlay) return;
  overlay.classList.remove("lang-modal-active");
  overlay.classList.add("lang-modal-leaving");
  setTimeout(function() { overlay.remove(); }, 300);
}

/* ══════════════════════════════════════════════
   Scroll Depth Tracking (Services / Bento section)
   ══════════════════════════════════════════════ */

function initScrollDepthTracking() {
  var section = document.querySelector(".bento-grid") || document.getElementById("services-grid");
  if (!section || !window.siteAnalytics) return;

  var thresholds = [0.25, 0.5, 0.75, 1.0];
  var tracked = {};

  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      thresholds.forEach(function(t) {
        if (!tracked[t] && entry.intersectionRatio >= t) {
          tracked[t] = true;
          siteAnalytics.trackScrollDepth("services", Math.round(t * 100) + "%");
        }
      });
    });
  }, { threshold: thresholds });

  obs.observe(section);
}

/* ══════════════════════════════════════════════
   Page Toggle Enforcement (redirect hidden pages)
   ══════════════════════════════════════════════ */

function enforcePageToggles() {
  var toggles = getPageToggles();
  var page = window.location.pathname.split("/").pop() || "";

  var pageMap = {
    "education.html": "education",
    "locations.html": "locations",
    "staff.html": "staff",
    "testimonials.html": "testimonials"
  };

  var toggleKey = pageMap[page];
  if (toggleKey && toggles[toggleKey] === false) {
    window.location.replace("index.html");
  }
}

/* ══════════════════════════════════════════════
   Dynamic Footer Links (toggle-aware on sub-pages)
   ══════════════════════════════════════════════ */

function renderToggleAwareFooter() {
  var containers = document.querySelectorAll(".footer-links");
  if (!containers.length) return;

  // Only apply on sub-pages that have static footer links (not index.html's dynamic footer)
  var container = containers[0];
  if (container.id === "footerLinks") return; // index.html uses dynamic footer

  var settings = getNavFooterSettings();
  var footerKeys = ["home", "services", "staff", "testimonials", "education", "locations", "careers"];

  container.innerHTML = footerKeys.filter(function(key) {
    return settings.footer[key] && settings.footer[key].visible;
  }).map(function(key) {
    var item = settings.footer[key];
    return '<a href="' + item.href + '">' + escapeHtmlUtil(item.label) + '</a>';
  }).join('');

  // Update copyright text on sub-pages
  var copyrightP = container.parentElement ? container.parentElement.querySelector("p") : null;
  if (copyrightP && settings.copyright) {
    copyrightP.textContent = settings.copyright;
  }

  // Append disclaimer if set
  if (settings.disclaimer && container.parentElement) {
    var existingDisclaimer = container.parentElement.querySelector("#footerDisclaimer");
    if (!existingDisclaimer) {
      var disclaimerP = document.createElement("p");
      disclaimerP.id = "footerDisclaimer";
      disclaimerP.style.cssText = "font-size:0.75rem;color:var(--mid-gray);margin-top:8px";
      disclaimerP.textContent = settings.disclaimer;
      container.parentElement.appendChild(disclaimerP);
    }
  }
}

function initSmoothScroll() {
  document.addEventListener("click", function(e) {
    var link = e.target.closest("a[href]");
    if (!link) return;

    var href = link.getAttribute("href");
    if (!href) return;

    // Pure anchor: #services
    var hash;
    if (href.charAt(0) === "#") {
      hash = href;
    } else {
      // Same-page link with anchor: index.html#services
      var parts = href.split("#");
      if (parts.length < 2 || !parts[1]) return;
      var linkPath = parts[0];
      var currentPath = window.location.pathname.split("/").pop() || "index.html";
      if (linkPath && linkPath !== currentPath) return;
      hash = "#" + parts[1];
    }

    if (hash === "#") return;
    var target = document.querySelector(hash);
    if (!target) return;

    e.preventDefault();
    var navHeight = 60;
    var top = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
    window.scrollTo({ top: top, behavior: "smooth" });
  });
}
