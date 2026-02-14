document.addEventListener("DOMContentLoaded", () => {
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

  /* ── Staff & Posts from localStorage ── */
  renderStaffSection();
  renderPostsSection();

  /* ── Dynamic navigation & routing ── */
  renderDynamicNav();
  renderDynamicFooter();
  handleRoute();

  window.addEventListener("popstate", handleRoute);

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
   Bento Grid (localStorage driven)
   ══════════════════════════════════════════════ */

var BENTO_ICON_MAP = {
  users: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  shield: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  flag: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
  heart: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
  star: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  gavel: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="8" height="8" rx="1" transform="rotate(-45 6 10)"/><path d="M14.5 9.5L18 6l-3-3-3.5 3.5"/><line x1="3" y1="21" x2="21" y2="21"/></svg>',
  home: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  globe: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
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
    { id: "tile3", title: "Citizenship", description: "From naturalization applications to citizenship interviews, we help you reach the final milestone on your immigration journey.", icon: "flag", layout: "medium" },
    { id: "tile4", title: "Work Visas", description: "H-1B, L-1, O-1 and other employment-based visas for professionals and their families.", icon: "globe", layout: "medium" },
    { id: "tile5", title: "Asylum", description: "Protection for those fleeing persecution. We build strong cases grounded in compassion and legal expertise.", icon: "heart", layout: "small" }
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
    var iconHtml = BENTO_ICON_MAP[tile.icon] || BENTO_ICON_MAP.star;
    var cls = layoutClasses[tile.layout] || "card-medium";
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

  pages.forEach(function(page) {
    var li = document.createElement("li");
    li.className = "dynamic-nav-link";
    var a = document.createElement("a");
    a.href = "index.html?page=" + encodeURIComponent(page.slug);
    a.textContent = page.title;
    a.addEventListener("click", function(e) {
      e.preventDefault();
      navigateTo(page.slug);
    });
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

  pages.forEach(function(page) {
    var a = document.createElement("a");
    a.href = "index.html?page=" + encodeURIComponent(page.slug);
    a.textContent = page.title;
    a.addEventListener("click", function(e) {
      e.preventDefault();
      navigateTo(page.slug);
    });
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
   Staff Gallery (rendered from localStorage)
   ══════════════════════════════════════════════ */

function renderStaffSection() {
  var container = document.getElementById("staffGallery");
  if (!container) return;

  var staff = getStaff();
  if (staff.length === 0) {
    container.innerHTML = "";
    var section = document.getElementById("staffSection");
    if (section) section.style.display = "none";
    return;
  }

  var section = document.getElementById("staffSection");
  if (section) section.style.display = "";

  container.innerHTML = staff.map(function(member) {
    return '<div class="staff-card reveal">' +
      '<div class="staff-avatar">' + escapeHtmlUtil(member.name.charAt(0)) + '</div>' +
      '<h3 class="staff-name">' + escapeHtmlUtil(member.name) + '</h3>' +
      '<p class="staff-title">' + escapeHtmlUtil(member.title) + '</p>' +
      '<p class="staff-office">' + escapeHtmlUtil(member.office) + '</p>' +
      '<p class="staff-bio">' + escapeHtmlUtil(member.bio) + '</p>' +
    '</div>';
  }).join('');

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

function applySiteSettings(settings) {
  var root = document.documentElement;
  for (var key in settings) {
    if (settings[key]) {
      root.style.setProperty(key, settings[key]);
    }
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
