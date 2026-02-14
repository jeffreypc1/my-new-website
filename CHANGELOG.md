# Changelog

## v1.0 — 2026-02-14

### Formspree Integration & Thank-You Page
- **Live form submissions** — Both the Consultation Concierge modal (on all pages) and the Staff Contact form (on `staff.html`) now submit to Formspree at `https://formspree.io/f/mpqjddon` via real `<form method="POST">` elements. Previously, submissions only logged to the console.
- **Proper `name` attributes** — All form inputs carry `name` attributes (`name`, `email`, `phone`, `issue`, `message`, `inquiry`) so Formspree captures every field.
- **Hidden routing fields** — Each form includes a `_subject` hidden field for email subject lines (e.g., "New Consultation Request" or "Inquiry for [Staff Name]") and a `_next` hidden field that redirects the user to `thank-you.html` after submission.
- **`thank-you.html` created** — Elegant confirmation page with an animated green checkmark (circle scales in via `ty-pop`, check path draws via `ty-draw` with `stroke-dashoffset`), "Thank You" heading, follow-up message, and a "Back to Home" button styled with the button engine CSS variables.
- **Duplicate mobile CSS fix** — Merged two duplicate `.bento-grid` blocks in the `@media (max-width: 768px)` breakpoint into a single clean rule.

**Why:** Completes the site's lead capture pipeline — visitor inquiries now reach the firm's inbox via Formspree, and every submission lands on a polished confirmation page. This is the final piece needed for a production-ready v1.0 launch.

### Bento Grid — 12-Column System
- **12-column grid** — Replaced `repeat(3, 1fr)` with `repeat(12, 1fr)` on `.bento-grid`. This gives precise fractional control: **Small** = `span 3` (1/4 row), **Medium** = `span 6` (1/2 row), **Large** = `span 12` (full row).
- **Dense auto-fill** — `grid-auto-rows: 1fr` combined with `grid-auto-flow: dense` ensures the browser back-fills any holes by promoting smaller tiles upward, eliminating white space gaps.
- **Uniform card height** — Added `height: 100%` to `.card` so tiles stretch to match their row neighbors perfectly, regardless of content length.
- **Admin preview synced** — The live preview in the Homepage Layout tab now uses the same 12-column dense grid so what you see in admin is exactly what renders on the homepage.
- **Mobile fallback** — On screens below 768px, the grid collapses to `grid-template-columns: 1fr` with `grid-auto-rows: auto`, and all size classes reset to natural height.

**Why:** The previous 3-column grid couldn't cleanly handle mixed tile sizes without leaving awkward holes. The 12-column system gives mathematical precision — 4 Small tiles fill a row exactly, 2 Medium tiles fill a row, and 1 Large tile fills a row — with `dense` packing as a safety net.

### Bento Grid — Dynamic Sync & Dense Spanning
- **Removed hardcoded bento cards** — Deleted the 3 static service cards (Family Petitions, Removal Defense, Citizenship) from `index.html`. The `.bento-grid` container is now empty on load and populated entirely by `renderBentoGrid()` in `main.js` from the `bentoTiles` localStorage key. Whatever you configure in the Admin Panel's Homepage Layout tab is exactly what appears on the homepage.
- **Dense grid flow** — Added `grid-auto-flow: dense` to `.bento-grid` so tiles pack tightly and never leave awkward holes in the layout.
- **3-column spanning system** — Updated the size classes to span the full 3-column grid: **Large** spans all 3 columns (full width), **Medium** spans 2 columns, **Small** spans 1 column. On mobile, all tiles collapse to full-width (`1 / -1`).
- **Consistent 24px gap** — Changed the grid gap from 20px to 24px for uniform spacing between all tiles.
- **Legacy classes simplified** — The old `card-wide`, `card-tall`, and `card-short` classes are preserved for backward compatibility but simplified to basic span rules.
- **Admin preview updated** — The live preview in the Homepage Layout tab now uses the same 3-column spanning logic.

**Why:** The homepage bento grid was split between hardcoded HTML and a dynamic renderer, causing stale content and empty white space. Now the admin panel is the single source of truth, tiles pack densely with no gaps, and the 3-column span system gives clean, predictable layouts at every size.

### Homepage Streamlined & Staff Architecture Cleanup
- **Removed homepage "Our Team" section** — Deleted the `#staffSection` / `#staffGallery` markup from `index.html`. The homepage now focuses on the Services bento grid and high-level mission. Removed the `renderStaffSection()` function and ~95 lines of homepage staff CSS (`.staff-section`, `.staff-gallery`, `.staff-card`, `.staff-avatar`, `.staff-name`, `.staff-title`, `.staff-office`, `.staff-bio`).
- **Staff page is the single source** — `staff.html` is now the only place team members are displayed. It reads exclusively from `localStorage` via `getStaff()`.
- **Centralized seed in `main.js`** — Replaced the inline auto-populate block in `staff.html` with a `seedDefaultStaff()` function in `main.js` that runs on every page load. If `siteStaff` is empty, it writes all 8 team members (Jeffrey O'Brien, Daska Babcock, Elena Applebaum, Rosanna Katz, Maria Amaya, Roshani Sitaula, Esteban Lasso, Guisselle Castellon) to localStorage. This means the Admin Panel's Staff tab also shows them on first visit — no need to open `staff.html` first.
- **Navigation intact** — The "Staff" link in the navbar on both `index.html` and `staff.html` continues to point to `staff.html`.

**Why:** Eliminated the architectural split where staff appeared on both the homepage and the staff page. The homepage is now a clean services-focused landing, and the staff gallery lives exclusively on its dedicated page, with localStorage as the single source of truth populated by `main.js`.

### Button Style Engine & Staff Contact Integration
- **Button Style dropdown** — New "Button Style" panel in Site Settings with three options: **Pill** (rounded 980px, Apple-esque — default), **Modern** (8px rounding, professional), and **Glass** (semi-transparent `rgba(255,255,255,0.15)` with a 1px border and `blur(12px)` backdrop). Selection is saved to `siteSettings` under the `--btn-style` key.
- **CSS variable-driven buttons** — Added `--btn-radius`, `--btn-bg`, `--btn-color`, `--btn-border`, and `--btn-backdrop` variables to `:root`. The `.nav-cta`, `.hero-btn`, `.consult-submit`, `.careers-cta-btn`, `.staff-modal-form-btn`, and staff modal close button all consume these variables, so changing the dropdown updates every button site-wide instantly.
- **Staff "Contact First" modal** — When a staff card is clicked, the focus modal now shows a **Send a Message** contact form directly below the staff member's contact links, before the bio. The form includes Your Name, Your Email, and Message fields. A hidden `inquiry` field is pre-filled with "Inquiry for [Staff Name]" so the firm knows which team member the client is interested in. Form validates name/email, logs to console, and shows a success message on submit.
- **Direct Email & Direct Phone labels** — Admin staff form field labels renamed from "Email" / "Phone" to "Direct Email" / "Direct Phone" for clarity.
- **Button-aware close button** — The staff modal close button now follows the chosen button style (border-radius, border, backdrop) for visual consistency.

**Why:** The button style engine gives the admin one-click control over the entire site's button aesthetic — from rounded Apple pills to frosted glass — without touching CSS. The contact-first modal turns every staff profile into a lead capture opportunity, pre-routing inquiries to the right team member.

### Staff Visibility Toggle
- **"Show on Website" checkbox** — New toggle in the admin Staff form controls whether a team member appears on the public `staff.html` page. Defaults to checked for new entries. Admin list rows now show green "Visible" or gray "Hidden" badges.
- **Filtered rendering** — `staff.html` filters the staff array by `showOnWebsite !== false` before rendering the grid. Hidden members remain in localStorage and can be toggled back on at any time.
- **Backdrop blur upgrade** — Staff focus modal overlay increased from `blur(15px)` to `blur(20px)` for a heavier iOS-style frosted effect.
- **Default staff visibility** — All 8 auto-populated team members now include `showOnWebsite: true` so they appear immediately on first visit.

**Why:** Gives the admin granular control over which team members are publicly visible without deleting their records, and deepens the Apple-style frosted glass feel of the focus modal.

### Interactive Staff Gallery with Focus Modal
- **Admin expansion** — Added Email and Phone Number fields to the Staff form in `admin.html`, alongside the existing Name, Title, Office, Image URL, Bio, and Hiring toggle. Both fields are saved to the staff data model and pre-populated on edit.
- **Staff grid layout** — Replaced the vertical card list on `staff.html` with a responsive 3-column grid (2-column on tablet, 1-column on mobile). Each card shows a square photo (or initial avatar fallback), name, and job title with hover lift and press-down transitions.
- **Focus modal** — Clicking any staff card opens a liquid glass modal that scales up from `scale(0.88)` to `scale(1)` with a spring curve. The background site gets a heavy `backdrop-filter: blur(15px)` overlay. Inside the modal: large photo on the left, Name, Title, Office, Email (with envelope icon), Phone (with phone icon), and full Bio on the right. On mobile the layout stacks vertically.
- **Close behaviors** — Close via the X button (circular, top-right), clicking the blurred background overlay, or pressing Escape.
- **Auto-populated staff** — When the `siteStaff` localStorage key is empty, `staff.html` pre-fills 8 team members sourced from obrienimmigration.com: Jeffrey O'Brien (Founding Partner), Daska Babcock, Elena Applebaum, and Rosanna Katz (Senior Attorneys), Maria Amaya and Roshani Sitaula (Senior Paralegals), Esteban Lasso (Paralegal), and Guisselle Castellon (Intake Specialist). Each includes office location and bio text.

**Why:** Transformed the staff page from a simple list into a high-end interactive gallery with an Apple-style grid and focus modal, letting visitors explore team profiles without leaving the page. Real firm data provides meaningful placeholder content out of the box.

### Bento Manager — Icon/Image Toggle & Live Preview
- **Display mode toggle** — Each bento tile in the admin Homepage Layout now has an "Use Icon" / "Use Background Image" radio toggle. The icon picker shows when icon mode is selected; a background image URL input shows when image mode is selected.
- **New Apple-style icon set** — Replaced the 8-icon set with 4 clean icons: Scale (balance/justice), Shield, Users, and Document. Applied across both admin selectors and the public-facing bento grid.
- **Background image mode** — When a tile uses a background image, the card renders with `background-size: cover`, a gradient darken overlay (`rgba(0,0,0,0.25)` to `rgba(0,0,0,0.6)`), and a subtle `blur(2px)` so white text remains perfectly readable over any photo.
- **Live preview panel** — A new "Preview" section below the tile editors renders a miniature bento grid in real-time as you type. Shows the same grid layout (span sizes), icon/image modes, and text truncation so you can check if a card looks too busy before saving.
- **Data model update** — Tile objects now include `displayMode` ("icon" or "image") and `bgImage` (URL string). Existing tiles are automatically migrated with `displayMode: "icon"` as default.

**Why:** Gives the admin fine-grained visual control over each bento card — choose between a clean icon or a rich background photo — while the live preview eliminates save-and-check guesswork.

### Consultation Concierge Modal
- **Liquid Glass modal overlay** — "Book a Consultation" buttons on both `index.html` and `staff.html` now open a frosted-glass modal instead of navigating away. The overlay uses `backdrop-filter: blur(20px)` with a dark tint, and the modal panel uses `blur(40px)` with translucent white for the signature liquid glass effect. Appears with a smooth `scale(0.92) -> scale(1)` spring animation.
- **Consultation form** — Modal contains Name, Phone (side-by-side row), Email, Legal Issue dropdown (Family, Removal, Citizenship), and a Message textarea. Clean uppercase labels with the same form styling used across the site.
- **Thank-you success state** — On submit, the form fades out and a checkmark animation plays (green circle scales in via `consult-pop`, then the check path draws itself via `consult-draw` with `stroke-dashoffset`). "Thank You" heading with a follow-up message. Submission data is logged to the console for future email routing.
- **Form validation** — Name and Email are required. Empty required fields flash red borders for 1.5 seconds on submit attempt.
- **Close behaviors** — Close via the X button, clicking outside the modal, or pressing Escape.
- **Admin toggle** — New "Consultation Pop-up" panel in Site Settings with an "Enable Consultation Pop-up" checkbox. When disabled, the CTA buttons remain inert. Setting stored in `siteSettings` under the `--consult-popup` key.
- **Shared across pages** — The modal is built dynamically by `main.js` on first open and works on any page that loads `main.js` and `style.css`, including `index.html` and `staff.html`.

**Why:** Converted the static "Book a Consultation" CTA into an interactive intake form with a premium liquid glass design, keeping visitors on-page instead of navigating away. The admin toggle provides easy control over the feature without touching code.

### Staff & Careers Management System
- **Enhanced Staff tab in admin** — Added Image URL field and "Actively Hiring" checkbox to the Staff form. Staff list rows now show hiring badges (green) and office location badges (blue). The staff data object now includes `imageUrl` and `hiring` properties.
- **Created `staff.html`** — Dedicated staff page with Apple-style gallery layout: large vertical cards with 160px rounded photos (or initial avatars as fallback), generous white space, and clean typography. Each card shows name, title, office, and full bio.
- **Hiring integration** — When "Actively Hiring" is checked for a staff member, their card displays a green "Join the Team" badge (positioned top-right on desktop, inline on mobile) and a "View Job Description" pill button that opens an email to `careers@obrienimmigration.com` with the role pre-filled in the subject line.
- **Careers CTA section** — A bottom section on staff.html reading "Interested in Joining Our Team?" auto-shows only when at least one staff member is marked as hiring.
- **Navigation updates** — Added "Staff" link to the top navbar in `index.html` pointing to `staff.html`. Added a static "Careers" link to the footer. The staff.html page includes its own navbar with the Staff link highlighted.
- **Responsive layout** — Staff cards stack vertically on mobile with centered content, smaller avatars (120px), and the hiring badge repositioned inline above the card content.

**Why:** Gave the firm a professional public-facing team page with a clean Apple aesthetic, and integrated a lightweight careers system that flags open positions with hiring badges and email-driven applications — all without a backend.

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
