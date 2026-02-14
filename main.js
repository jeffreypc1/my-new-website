document.addEventListener("DOMContentLoaded", () => {
  /* ── Global navigation (must run first) ── */
  renderGlobalNav();

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
  initBentoTilt();

  /* ── Aurora glow on nav & buttons ── */
  initAuroraGlow();

  /* ── Page transition fade ── */
  initPageTransitions();

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

  container.innerHTML = tiles.map(function(tile) {
    var cls = layoutClasses[tile.layout] || "card-medium";
    var isImage = tile.displayMode === "image" && tile.bgImage;

    if (isImage) {
      return '<div class="card ' + cls + ' card-bg-image reveal" style="background-image:url(\'' + escapeHtmlUtil(tile.bgImage) + '\')">' +
        '<div class="card-bg-overlay"></div>' +
        '<div class="card-bg-content">' +
          '<h3>' + escapeHtmlUtil(tile.title) + '</h3>' +
          '<p>' + escapeHtmlUtil(tile.description) + '</p>' +
        '</div>' +
      '</div>';
    }

    var iconHtml = BENTO_ICON_MAP[tile.icon] || BENTO_ICON_MAP.scale;
    return '<div class="card ' + cls + ' reveal">' +
      '<div class="card-icon">' + iconHtml + '</div>' +
      '<h3>' + escapeHtmlUtil(tile.title) + '</h3>' +
      '<p>' + escapeHtmlUtil(tile.description) + '</p>' +
    '</div>';
  }).join('');

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

  nav.innerHTML =
    '<div class="nav-content">' +
      '<a href="index.html" class="nav-logo">O\u2019Brien Immigration</a>' +
      '<ul class="nav-links" id="navLinks">' +
        '<li><a href="index.html#services-grid">Services</a></li>' +
        '<li><a href="staff.html">Staff</a></li>' +
        '<li><a href="testimonials.html">Testimonials</a></li>' +
        '<li><a href="locations.html">Locations</a></li>' +
        '<li><a href="#" class="nav-cta">Book a Consultation</a></li>' +
      '</ul>' +
    '</div>';

  // Mobile FAB
  var fab = document.createElement("button");
  fab.className = "mobile-fab";
  fab.setAttribute("aria-label", "Book a Consultation");
  fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Book';
  fab.addEventListener("click", function() { openConsultModal(); });
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

  var overlay = document.createElement("div");
  overlay.id = "consultOverlay";
  overlay.className = "consult-overlay";
  overlay.innerHTML =
    '<div class="consult-modal">' +
      '<button class="consult-close" aria-label="Close">&times;</button>' +
      '<form id="consultForm" action="https://formspree.io/f/mpqjddon" method="POST">' +
        '<h2>Book a Consultation</h2>' +
        '<p class="consult-sub">Tell us about your situation and we\u2019ll get back to you within 24 hours.</p>' +
        '<input type="hidden" name="_next" value="' + window.location.origin + '/thank-you.html">' +
        '<input type="hidden" name="_subject" value="New Consultation Request">' +
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
        '<div class="consult-form-group">' +
          '<label for="consultIssue">Legal Issue</label>' +
          '<select id="consultIssue" name="issue">' +
            '<option value="">Select an issue\u2026</option>' +
            '<option value="Family">Family</option>' +
            '<option value="Removal">Removal</option>' +
            '<option value="Citizenship">Citizenship</option>' +
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

  // Client-side validation highlight
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
    }
  });
}

function openConsultModal() {
  if (!isConsultEnabled()) return;
  buildConsultModal();

  // Reset form state
  var form = document.getElementById("consultForm");
  var success = document.getElementById("consultSuccess");
  if (form) {
    form.style.display = "";
    form.querySelectorAll("input, select, textarea").forEach(function(el) { el.value = ""; });
  }
  if (success) success.classList.remove("visible");

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
  });
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

function initBentoTilt() {
  var cards = document.querySelectorAll(".bento-grid .card");
  var maxTilt = 5; // degrees

  cards.forEach(function(card) {
    // Inject the Aurora glow layer
    var glow = document.createElement("div");
    glow.className = "bento-glow";
    card.insertBefore(glow, card.firstChild);

    card.addEventListener("mousemove", function(e) {
      var rect = card.getBoundingClientRect();
      var px = e.clientX - rect.left;
      var py = e.clientY - rect.top;

      // Update CSS variables for radial-gradient position
      card.style.setProperty("--mouse-x", px + "px");
      card.style.setProperty("--mouse-y", py + "px");

      // Normalized -1 to 1 from center
      var x = (px / rect.width) * 2 - 1;
      var y = (py / rect.height) * 2 - 1;

      // rotateY follows x, rotateX is inverted y (tilt toward cursor)
      var rotateY = x * maxTilt;
      var rotateX = -y * maxTilt;

      card.style.transform = "perspective(800px) rotateX(" + rotateX + "deg) rotateY(" + rotateY + "deg) translateY(-4px) scale(1.01)";
    });

    card.addEventListener("mouseleave", function() {
      card.style.transform = "";
    });
  });
}

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
