# Changelog

## 2026-02-14

### Staff Gallery, Newsroom & Enhanced Bento Manager
- **Staff Manager tab in admin** — Full CRUD interface for team members with Name, Title (e.g., Senior Attorney), Office Location (Berkeley/Stockton dropdown), and Bio. Staff data stored in localStorage under `siteStaff`. Each member has an auto-generated avatar initial, and the admin list shows office badges with Edit/Delete controls.
- **Posts Manager tab in admin** — Full CRUD interface for Immigration News articles with Title, auto-generated Slug, Date picker, Category (News, Policy Update, Case Study, Community), rich Content textarea, and Published checkbox. Posts stored in localStorage under `sitePosts`. Post list shows category and published/draft badges.
- **Staff Gallery on live site** — New "Our Team" section on the homepage renders staff cards from localStorage with glassmorphism styling, avatar initials, name, title, office, and bio. Section auto-hides when no staff exist.
- **Newsroom on live site** — New "Immigration News" section on the homepage renders published posts as clickable cards with category tag, title, and date. Section auto-hides when no published posts exist.
- **Individual post routing** — Clicking a post card navigates to `?post=slug` via pushState. The post view displays category, title, date, and full article content in a centered 720px column.
- **Enhanced Bento Manager** — Replaced 3 hardcoded tile editors with a dynamic system supporting 4–5 tiles. Each tile now has a **Tile Size** selector (Small, Medium, Large) alongside the icon picker. Tiles can be added/removed (max 5). Data stored as an array in `bentoTiles` with backward-compatible migration from the old object format.
- **New bento CSS grid classes** — Added `.card-small` (1 col), `.card-medium` (1 col, taller), `.card-large` (2 col span) for the asymmetric Apple-style bento layout, with mobile fallback to single-column.
- **Dashboard expanded** — Added Staff Members and Published Posts stat cards. Recent Content table now merges pages and posts, sorted by date.

**Why:** Elevated the CMS from a page-only system to a full content platform with team profiles, a newsroom/blog, and a flexible homepage layout — all still running purely client-side with localStorage.

### Initial Project Setup
- **Created `index.html`** — Main landing page with a glassmorphism navbar, full-viewport hero section, and a 3-column feature card grid. Establishes the core public-facing structure of the site.
- **Created `style.css`** — Global stylesheet using Inter/system-ui fonts, a minimalist white/off-white/black palette, 16px border radiuses, and smooth cubic-bezier transitions. Provides the Apple-inspired visual foundation.
- **Created `main.js`** — Scroll-to-reveal animation using IntersectionObserver. Adds polish by fading elements in as the user scrolls.
- **Created `admin.html`** — Self-contained admin panel layout with a fixed sidebar and dashboard view (stat cards + recent content table). Gives us a starting point for future content management.

**Why:** Established the full project scaffold — a premium, Apple-inspired public site and a separate admin panel — using vanilla HTML/CSS/JS with no frameworks.

### Liquid Glass Refinements
- **Navbar shrink on scroll** — Navbar height reduces from 56px to 44px and becomes more translucent (55% opacity) after scrolling 40px. Uses `requestAnimationFrame` for smooth performance. Reinforces the liquid glass aesthetic.
- **Haptic-style button effects** — "Learn More" and "Get Started" buttons now scale *down* to 0.96 on hover and 0.92 on active, using a fast spring-like cubic-bezier curve. Mimics the tactile press feel of Apple's UI.
- **Bento Grid layout** — Replaced the equal 3-column feature grid with an asymmetric bento layout: Performance spans 2 columns, Design is a tall single column, Security sits below as a wide short card. Soft layered box-shadows replace the old single shadow. Collapses to single-column on mobile.

**Why:** Evolved the design from a clean starting point toward a 2026 "Liquid Glass" Apple-inspired aesthetic with dynamic scroll behavior, tactile interactions, and a signature bento grid.

### CSS Variable System & Admin Site Settings
- **Added admin-controllable CSS variables** — Introduced `--primary-font`, `--heading-font`, `--accent-color`, and `--hero-bg-image` in `:root`. Replaced all hard-coded font-family and button background references in `style.css` with these variables. The hero section now accepts a dynamic background image.
- **Built Site Settings panel in `admin.html`** — New "Site Settings" section with: dropdown selects for primary and heading fonts (Inter, SF Pro Display, Georgia, Courier New, System UI), a color picker for accent color, and a text input for hero background image URL. Includes a Save button with toast notification.
- **Sidebar now routes between sections** — Dashboard, Site Settings, Pages, Posts, and Media are toggled via `data-section` attributes. Only the active section is visible.
- **Settings persistence via localStorage** — `main.js` exports `applySiteSettings`, `loadSiteSettings`, and `saveSiteSettings` functions. On page load, `index.html` reads saved settings from localStorage and applies them to `:root`. The admin form pre-populates from the same store.
- **Live preview iframe** — The Settings page includes an embedded iframe of `index.html` that reloads after saving, so you can see changes immediately.

**Why:** Moved from hard-coded styles to a dynamic, variable-driven system so the Admin Panel can control the site's look without touching CSS files. This is the foundation for a full CMS-style theming workflow.

### Admin Keyboard Shortcut & Transition Overlay
- **Global key listener** — `Cmd+Shift+A` (Mac) or `Ctrl+Shift+A` (Windows/Linux) triggers a redirect to `admin.html`. The shortcut is guarded against double-firing.
- **"Loading Admin..." overlay** — A full-screen frosted-glass overlay fades in with a spinner and label, using `backdrop-filter: blur(30px)` and a scale-up content transition. Redirect fires after a 1-second delay so the animation completes.
- **Overlay CSS** — New `.admin-overlay` block in `style.css` with layered transitions on opacity, backdrop blur, and background. The spinner uses a minimal `border-top` animation at 0.7s linear.

**Why:** Replaces a visible link to the admin panel with a hidden keyboard shortcut, keeping the admin entry point out of the public UI while providing an elegant, Apple-style transition when accessed.

### O'Brien Immigration Rebrand
- **Hero content updated** — Headline changed to "Protecting the Path to a New Beginning." Sub-headline now reads "Compassionate legal counsel for families and individuals navigating the U.S. immigration system. Based in Berkeley and Stockton." CTA button changed to "Book a Consultation."
- **Hero background image** — Set `--hero-bg-image` to an Unsplash photo of the Golden Gate at sunrise (California hope theme). Added a multi-stop dark gradient overlay (`::before` pseudo-element) so white text is legible. Hero text color changed from `--dark` to `--white` with a subtle text-shadow.
- **Hero button restyled** — Now a frosted white pill (`rgba(255,255,255,0.92)` with `backdrop-filter: blur(8px)`) with dark text, designed to pop against the photo background.
- **Service cards replace generic features** — "Performance, Design, Security" replaced with "Family Petitions" (users SVG icon), "Removal Defense" (shield icon), and "Citizenship" (flag icon). Each card has real practice-area copy.
- **Glassmorphism cards** — Cards now use `rgba(255,255,255,0.6)` background, `backdrop-filter: blur(16px)`, a 1px white border, and 24px border-radius. Soft layered shadows on hover.
- **Branding updates** — Page title, nav logo, and footer updated to "O'Brien Immigration Law." Nav link changed from "Features" to "Services."

**Why:** Transitioned from a generic placeholder brand to the real O'Brien Immigration Law identity, with California-inspired imagery, actual practice areas, and glassmorphism cards that reinforce the premium, modern aesthetic.

### Dynamic Page Management System
- **Admin Pages section** — Replaced the placeholder "Pages" panel with a full CRUD interface: "Add New Page" button opens a form with Title, URL Slug (auto-generated from title), Content textarea, and two checkboxes ("Show in Top Navigation" / "Show in Footer"). Existing pages display in a list with Edit and Delete buttons. Each row shows the title, slug, and colored badges (blue "Nav", orange "Footer", gray "Hidden").
- **localStorage data layer** — All page data is stored as a JSON array under the `sitePages` key in localStorage. Each page object has: `id`, `title`, `slug`, `content`, `showInNav`, `showInFooter`, `createdAt`. Both `admin.html` and `main.js` share the same `getPages()` / `savePages()` interface.
- **Dynamic navigation injection** — `main.js` reads pages with `showInNav: true` and injects `<li>` elements into `#navLinks`, inserted before the CTA button. Footer links are rendered into a new `#footerLinks` container for pages with `showInFooter: true`.
- **Virtual routing** — Clicking a dynamic nav or footer link uses `history.pushState` to update the URL to `index.html?page=slug` without a full reload. `handleRoute()` reads the `?page` query param, looks up the page in localStorage, and swaps between `#homeView` (hero + bento grid) and `#pageView` (dynamic title + content). The `popstate` event handles browser back/forward.
- **Dashboard now live** — Stat cards show real counts (Total Pages, Nav Links, Footer Links) pulled from localStorage. The Recent Content table shows the 5 most recently created pages with their visibility badges.
- **New CSS** — Added `.page-view` styles (centered 720px content column, heading font, pre-wrap body text), `.footer-links` flexbox row, and responsive adjustments for the page list rows.

**Why:** Moved from static HTML pages to a dynamic, JSON-driven page system. Pages created in the admin panel automatically appear in the site's navigation and footer, and are rendered client-side via virtual routing — all without a server or framework.

### SEO Tools, Homepage Manager, Draft Status & Media Library
- **SEO fields on pages** — Added "SEO Title" and "Meta Description" text inputs to the page form in `admin.html`. Values are saved to the page object (`seoTitle`, `metaDescription`). In `main.js`, the virtual router now sets `document.title` to `seoTitle` (falling back to `title`) and dynamically injects/updates a `<meta name="description">` tag when navigating to a page.
- **Published / Draft status** — New "Published" checkbox on the page form (defaults to checked for new pages). Unpublished pages are excluded from both the top navigation and footer links — the `renderDynamicNav()` and `renderDynamicFooter()` functions now filter on `published !== false`. Page list rows show a green "Published" or gray "Draft" badge. Dashboard stats reflect published counts.
- **Homepage Layout manager** — New "Homepage Layout" tab in the admin sidebar. Contains three tile editor panels (one per bento card) with title, description, and icon dropdown (users, shield, flag, heart, star, gavel, home, globe). Data is stored in localStorage under `bentoTiles`. In `main.js`, `renderBentoGrid()` reads this data on load and dynamically builds the bento cards from a `BENTO_ICON_MAP` of inline SVGs, replacing the previously hard-coded HTML.
- **Media Library** — Replaced the placeholder "Media" tab with a functional image URL manager. "Add Image URL" opens a form with URL and label fields. Saved entries display as rows with a 48x48 rounded thumbnail preview, label, truncated URL, a "Copy URL" button (using the Clipboard API), and a Delete button. Data is stored in localStorage under `mediaLibrary` as `{id, url, label}` objects.
- **Dashboard updates** — "Visitors" stat card replaced with "Published" page count. Nav/Footer stats now filter by published status. Recent Content table shows Published/Draft badges.

**Why:** Elevated the admin panel from a basic page manager to a professional CMS with SEO controls, content lifecycle management (draft/publish), visual homepage editing, and an asset library — all still running purely client-side with localStorage.
