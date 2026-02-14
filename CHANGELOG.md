# Changelog

## v1.9 — 2026-02-14

### Hero Clock Relocation & Education Path Finder

- **Hero clock whisper line** — The living clock and office status have been relocated from the navigation bar to the top of the hero section, sitting just above the main headline as a delicate whisper of text. Format: `San Francisco, CA — 10:42 AM · Office is Open`. Styled with `font-weight: 300`, `letter-spacing: 0.12em`, `text-transform: uppercase`, and `color: rgba(255,255,255,0.55)` — ambient information that blends into the hero without competing for attention. The 6px status dot with its breathing glow animation sits inline to the left.
- **Navigation decluttered** — The top-bar strip has been removed entirely from the navbar. The nav now contains only the logo, five links (Services, Staff, Testimonials, Education, Locations), and the CTA button, with `40px` gaps for breathing room. The nav is clean and focused.
- **Education page (`education.html`)** — A new "Immigration Path Finder" interactive tool that guides visitors through their options in two steps:
  - **Step 1** — "I am..." with four status categories: U.S. Citizen, Lawful Permanent Resident, Undocumented/No Status, Visa Holder.
  - **Step 2** — "And I want to..." with dependent options that change based on Step 1 (e.g., Citizen → Sponsor a spouse, Sponsor a parent, Apply for a fiance visa, Sponsor a sibling).
  - **Result card** — A glassmorphism card appears with: the goal title, an estimated timeline badge, a detailed process description, and a "Request Deep Dive" CTA that opens the consultation modal.
- **Premium custom selects** — No native browser `<select>` elements. Both picklists use custom-built dropdown menus with: glassmorphism backgrounds (`backdrop-filter: blur(30px)`), fade-in animation (`translateY(-8px) → 0`, `scale(0.97) → 1`), hover highlights, selected state indicators, and a rotating chevron icon. They close on outside click and feel native to the site's design language.
- **Step animations** — Step 2 fades in (`opacity 0→1`, `translateY(16px)→0` over `0.5s`) only after Step 1 is answered. The result card uses a similar entrance at `0.6s`. Each transition uses the site's premium cubic-bezier curve.
- **Admin "Education Logic" tab** — Full CRUD for the Path Finder in admin.html:
  - **Status list** — View, edit, and delete status categories.
  - **Goal editor** — For each status, add/edit/delete goals with fields: Goal Label, Process Description (textarea), Estimated Timeline, CTA Button Text.
  - Data stored in `sitePathFinder` localStorage key with seed defaults matching the hardcoded data.
- **Education nav link** — Added "Education" to the global navigation between Testimonials and Locations.

**Why:** Prospective clients visiting an immigration lawyer's website often don't know what legal path applies to them. The Path Finder turns a confusing landscape into a two-click guided experience — select who you are, then what you want, and get a clear explanation with timeline and next steps. The admin panel ensures the firm can update legal pathways as immigration law evolves, without touching code.

## v1.8.1 — 2026-02-14

### Header Declutter & Clock Refinement
- **Apple-style top bar** — The living clock and status dot have been relocated from the main navigation row into a dedicated slim strip above it (`.top-bar`). This mirrors Apple.com's global promo bar pattern — a single centered line of whisper-light text that stays out of the way. The top bar auto-hides when the user scrolls (`.navbar.scrolled .top-bar { display: none }`), keeping the compact scrolled nav clean.
- **Refined clock typography** — Replaced the monospaced font stack (`SF Mono`, `Fira Code`, `Consolas`) with the site's primary `Inter` font at `10px` with `letter-spacing: 0.06em` and `opacity: 0.7`. The result is a subtle, barely-there timestamp that reads as ambient information rather than a UI element.
- **6px breathing status glow** — The status dot has been shrunk from 8px to 6px. The green "open" state now uses a soft `box-shadow` glow animation (`status-glow`) that pulses between `2px` and `6px` spread over 2.5 seconds, replacing the previous expanding ring. The amber "closed" dot uses a static `3px` warm glow. Both feel like gentle indicator lights rather than bold UI dots.
- **Increased nav link spacing** — The gap between navigation links (Services, Staff, Testimonials, Locations) has been increased from `32px` to `40px`, giving each link room to breathe and improving the overall sense of openness in the header.
- **Top bar visual treatment** — The top bar has a `1px` bottom border at `4%` opacity (adjusts for dark mode) — no background color, no visual weight. The clock text uses `var(--mid-gray)` at reduced opacity, making it feel like metadata rather than content.

**Why:** The original clock placement competed with navigation links for horizontal space, creating a crowded header that undermined the site's premium feel. Apple's own site solves this exact problem with a thin promo strip above the nav — information is visible but never in the way. The refined 6px glow dots and whisper-weight typography ensure the clock reads as ambient environmental data, not a UI widget.

## v1.8 — 2026-02-14

### Intelligent Office Environment & Adaptive Calendar

- **Business Hours admin tab** — A new "Business Hours" tab in admin.html lets you set daily open/close times for each day of the week (default Mon–Fri 9 AM–5 PM, Sat–Sun closed). A "Special Closures" section allows adding specific dates (e.g., July 4th, Dec 25th) with custom labels. Data persists in `siteBusinessHours` localStorage key.
- **Living Clock & Status Engine** — The navigation bar now displays a real-time digital clock ("Berkeley, CA — 2:42 PM") using a monospaced font (`SF Mono` / `Fira Code` / `Consolas`). A status dot adjacent to the clock indicates office status: **green** (Open, with a subtle pulse animation), **amber** (Closed — outside business hours or weekend), or **red** (Holiday/Special Closure). The status is computed by checking the current time against the stored business hours schedule and special closures list. The clock updates every 30 seconds.
- **Sun-Aware Adaptive Image Engine** — The system now automatically detects when local time crosses the 6 PM or 6 AM boundary and triggers a theme switch (light → dark at 6 PM, dark → light at 6 AM), invoking the adaptive image cross-fade. Manual overrides via the dark mode toggle still work and use the same transition.
- **3-second cross-fade** — The adaptive image cross-fade duration has been upgraded from 2 seconds to 3 seconds for an even more cinematic transition. Both CSS transitions (`.hero-crossfade`, `.location-hero-crossfade`, filter transitions) and JS `setTimeout` callbacks have been updated to 3s / 3000ms.
- **Status dot pulse animation** — When the office is open, the green status dot has a `status-pulse` keyframe animation: a soft expanding ring (`box-shadow`) that fades out over 2 seconds, creating a "breathing" effect that signals live status.

**Why:** Visitors checking the firm's website should immediately know if the office is currently open. The living clock and status dot provide at-a-glance awareness, while the sun-aware image engine ensures the site's visuals match the time of day — a blazing daytime skyline at 10 PM feels wrong, and now it automatically corrects itself. The 3-second cross-fade makes the day/night transition feel unhurried and premium.

## v1.7 — 2026-02-14

### Adaptive Image Engine (Day/Night Cross-Fade)
- **Dual image fields in admin** — The Hero Background panel in Site Settings now has two fields: "Day Image URL" and "Night Image URL." The Locations Manager form similarly replaces the single "City Photo URL" with "Day Photo URL" and "Night Photo URL." Both night fields are optional.
- **Theme-aware image swapping** — A new `applyAdaptiveImages()` function in main.js detects the current theme (`data-theme="dark"` → night, otherwise → day). When the dark mode toggle is clicked, the function fires and swaps hero and location background images to the appropriate variant.
- **2-second cross-fade transition** — Image swaps use a `.hero-crossfade` overlay layer (and `.location-hero-crossfade` for locations). The new image fades in via `opacity 0 → 1` over `2s cubic-bezier(0.15, 0.83, 0.66, 1)`, then the base layer is updated and the overlay removed. This eliminates the jarring "blink" of a direct `background-image` swap.
- **Smart defaults** — When no night image is provided, the day image stays but receives `filter: brightness(0.5) contrast(1.1)` automatically, creating a convincing nighttime feel. The filter also transitions over 2 seconds via CSS. A dedicated `.hero-night-filter` / `.location-hero-night-filter` class is toggled to control this. When switching back to light mode, the filter smoothly fades out.
- **Location grid thumbnails** — The locations listing page also respects the current theme: grid card thumbnails show the night photo (or the smart-filtered day photo) in dark mode.
- **Settings persistence** — Night image URLs are stored in `siteSettings` under `--hero-bg-image-night` and in each location object as `cityPhotoNight`. The `applySiteSettings()` function skips `--hero-bg-image-night` (it's not a CSS variable — it's consumed by the adaptive engine directly).
- **Runs on page load** — `applyAdaptiveImages()` is called during `DOMContentLoaded` after `initDarkMode()`, so if a user has dark mode persisted, the night images display immediately on first paint.

**Why:** A law firm website viewed at 9 PM shouldn't show a blazing daytime skyline. The adaptive image engine lets the admin set beautiful dusk/night city photos that swap seamlessly with the theme toggle. The 2-second cross-fade makes the transition feel cinematic rather than abrupt, and the smart brightness/contrast fallback means the feature works even if no night photo is uploaded.

## v1.6 — 2026-02-14

### Staff Location Muting System
- **iOS-style Segmented Control** — A sleek `[ All ] [ San Francisco ] [ Stockton ]` toggle sits below the staff hero section. Built with `.segmented-control` — a pill-shaped container with `border-radius: 12px`, background `var(--off-white)`, and inner buttons that slide between states using `0.3s cubic-bezier(0.15, 0.83, 0.66, 1)`. The active button gets a white background with a soft box-shadow, mimicking iOS UISegmentedControl. Adapts to dark mode with darker backgrounds and adjusted shadows.
- **Grayscale muting effect** — When a location is selected (San Francisco or Stockton), staff members at the *other* location receive `filter: grayscale(100%)` and `opacity: 0.4` via a `.muted` CSS class. The transition animates over `0.5s` with the premium cubic-bezier curve, creating a smooth, intentional dimming effect. Muted cards remain fully clickable — clicking a muted card still opens the bio modal normally.
- **Blue Aurora Glow on active cards** — Staff members at the selected location receive a `.location-active` class that adds a subtle blue aurora ring: `box-shadow: 0 0 0 1px rgba(100, 160, 255, 0.2), 0 0 24px rgba(100, 160, 255, 0.12)`. On hover, the glow intensifies to `0.3` border and `0.18` spread. This draws the eye to the active-location staff.
- **"All" resets both effects** — Selecting "All" removes both `.muted` and `.location-active` classes, returning all cards to their default state with full color.
- **Admin "Primary Location" dropdown** — The Staff form's "Office Location" dropdown has been renamed to "Primary Location" with options: San Francisco and Stockton. Each staff card carries a `data-office` attribute used by the switcher logic. Updated seed defaults from "Berkeley" to "San Francisco" to match the new location names.

**Why:** Immigration firms with multiple offices need visitors to quickly identify their local team. The segmented control provides instant visual filtering, while the grayscale muting creates a striking before/after effect that directs attention to the relevant staff members. The blue aurora glow ties the active cards into the site-wide Aurora design language.

## v1.5 — 2026-02-14

### Site-Wide Aurora Glow System
- **Global cursor-tracking glow** — All primary interactive elements (`.nav-links a`, `.nav-cta`, `.hero-btn`, `.consult-submit`, `.mobile-fab`) now have a cursor-reactive blue radial glow (`rgba(100, 160, 255, 0.15)`) that follows the mouse via `--glow-x` / `--glow-y` CSS variables. The glow is implemented as `::after` pseudo-elements on nav links and `::before` pseudo-elements on buttons, using the same premium cubic-bezier timing (`0.15, 0.83, 0.66, 1`). A new `initAuroraGlow()` function in main.js updates the CSS variables on every `mousemove` event for all matching elements.
- **Layered with existing effects** — The button glow layers beneath text content via `pointer-events: none`, and works alongside the existing magnetic button effect and bento card glow. Nav link glows extend slightly beyond the link bounds (`inset: -8px -12px`) for a more generous light radius.

### Sophisticated Page Transitions
- **Fade-in on load** — `body` starts at `opacity: 0` and transitions to `opacity: 1` over `0.6s` using the premium cubic-bezier curve when the `page-loaded` class is added on `DOMContentLoaded`.
- **Fade-out on navigate** — When clicking any local `.html` link (excluding anchors, CTAs, and external links), `initPageTransitions()` adds a `page-leaving` class that fades the body to `opacity: 0` over `0.4s`, then navigates after the animation completes. This creates a smooth, sophisticated transition between pages.
- **Smart exclusions** — Anchor links, `mailto:`, `tel:`, `javascript:` URLs, `target="_blank"` links, and CTA buttons (which open modals) are all excluded from the fade transition.

### Locations Engine — Admin CRUD + Public Page
- **Admin Locations Manager** — New "Locations" tab in the admin sidebar with full CRUD: Office Name, Tagline, Address, Phone, Email, City Photo URL, Parking & Access info, and Specialties. List rows show address and phone badges. Dashboard includes a new "Locations" stat card.
- **`siteLocations` localStorage** — Data model: `{ id, name, tagline, address, phone, email, cityPhoto, parking, specialties, createdAt }`. Shared `getLocations()` / `saveLocations()` helpers in main.js.
- **`locations.html` — Split-Hero layout** — Two views in one page:
  - **Grid view** (default): Responsive card grid showing all locations with city photo thumbnails, office names, and addresses. Cards link to the detail view.
  - **Detail view** (`?loc=id`): Split-Hero with a full-width city photo background + dark gradient overlay. Left side shows office name and tagline; right side shows a glassmorphism contact card with address, phone, and email (with clickable `tel:` and `mailto:` links). Below the hero, a 3-box bento grid provides Parking & Access info, Specialties, and a local Contact Form (Formspree-integrated).
- **Navigation link** — "Locations" added to the shared nav in `renderGlobalNav()`, between Testimonials and the CTA button.
- **Dark mode support** — Location cards, contact card, and bento cards all adapt to dark theme with appropriate background and border overrides.
- **Responsive** — Location hero stacks vertically on tablet/mobile, bento grid collapses to single column.

**Why:** The site-wide Aurora glow transforms every clickable element into a reactive light surface, creating a cohesive "living interface" feel across all pages. The page transition fade adds cinematic polish to navigation. The Locations Engine gives the firm a professional multi-office presence with rich detail pages — all managed from the admin panel without touching code.

## v1.4 — 2026-02-14

### Aurora Reactive Glow System
- **Cursor-reactive `.bento-glow`** — Each bento card now contains an absolutely-positioned `.bento-glow` div whose `radial-gradient` follows `--mouse-x` and `--mouse-y` CSS variables. JavaScript updates these on `mousemove`, creating a soft blue spotlight that tracks the cursor across the card surface. The glow fades in on hover (`opacity: 0` → `1`) and out on leave, with separate dark mode gradient values.
- **Glass + Aurora layering** — Cards retain their glassmorphism base (`rgba(255,255,255,0.6)` + `backdrop-filter: blur(16px)`) while the Aurora glow layer sits on top with `pointer-events: none` and `z-index: 0`. Card content (icon, heading, text) is lifted to `z-index: 1` so it renders above the glow.
- **Staff modal Aurora bloom** — When a staff card is clicked, a `::before` pseudo-element on `.staff-modal-overlay` captures the click coordinates (`--bloom-x`, `--bloom-y`) and expands a blue radial glow from `scale(0.3)` to `scale(2.5)` over 600ms. This bloom fills the screen before the backdrop blur kicks in (delayed by 150ms), creating a "light expanding outward" reveal effect.
- **Premium micro-interaction timing** — All card transitions now use `transition: all 0.4s cubic-bezier(0.15, 0.83, 0.66, 1)` — a heavy, decelerating curve that feels like an expensive car door closing. The same curve is applied to the staff modal overlay, bloom, and modal entrance (staggered with delays for sequenced choreography: bloom → blur → modal scale).

**Why:** The Aurora system adds a reactive light layer that responds to the user's cursor, making the interface feel alive and tactile. The bloom transition on the staff modal creates a moment of theatrical elegance — the blue light expands from exactly where you clicked, naturally drawing your eye to the modal as it materializes.

## v1.3 — 2026-02-14

### Sophisticated Ambient Motion System
- **Cursor Glow** — A hidden `.ambient-glow` div follows the mouse cursor with a soft blue-white radial gradient and `filter: blur(200px)`. Movement uses `requestAnimationFrame` with an ease factor of `0.08`, creating a gentle trailing lag. The glow sits at `z-index: 0` with `pointer-events: none` so it never interferes with clicks. Adapts to dark mode with softer opacity.
- **Bento Perspective Tilt** — The `.bento-grid` container receives `perspective: 1200px`. Each `.card` inside gets `transform-style: preserve-3d` and a `mousemove` handler that calculates normalized cursor position (-1 to 1 from center) and applies `rotateX`/`rotateY` capped at 5 degrees. On `mouseleave`, the card smoothly resets to flat via the existing CSS transition. Cards tilt toward the cursor for a natural 3D feel.
- **Reveal Tuning** — The scroll-reveal animation (`IntersectionObserver` + `.reveal` class) now uses `translateY(20px)` instead of `24px` for a tighter, more deliberate entrance. Bento cards fade in and slide up as the user scrolls, making content "arrive" rather than just "be there."

**Why:** The three layers — ambient glow, perspective tilt, and scroll reveal — create a cohesive motion system. The glow adds environmental depth, the tilt gives interactive feedback, and the staggered reveal adds narrative pacing. Together they elevate the homepage from static to alive without being distracting.

## v1.2 — 2026-02-14

### SF Hero Image Restoration
- **Fixed hero background disappearing** — `applySiteSettings()` was applying `--hero-bg-image: none` from localStorage when the admin had saved an empty Hero URL field. The string `"none"` is truthy, so it passed the `if (settings[key])` guard and overwrote the CSS `:root` default (`url('https://images.unsplash.com/photo-1501594907352-04cda38ebc29...')`). Fixed by skipping `--hero-bg-image` when its value is `"none"`, letting the CSS default persist.
- **Hero gradient overlay intact** — The `.hero::before` pseudo-element applies a 3-stop `linear-gradient` (`rgba(0,0,0,0.52)` top → `rgba(0,0,0,0.40)` middle → `rgba(0,0,0,0.58)` bottom) so white text remains perfectly readable against the San Francisco skyline.

**Why:** The SF skyline is the site's visual anchor. A stale localStorage value was silently killing it — now the CSS default is resilient against empty admin saves.

### Colorful Initials Circles
- **Name-hashed color palette** — Each testimonial's initials circle now picks from a palette of 8 distinct colors (blue, purple, green, amber, red, cyan, magenta, indigo) using a character-code hash of the client's name. Same name always maps to the same color for visual consistency.
- **Inline style override** — Colors are applied via inline `style` attributes, so they work in both light and dark mode without additional CSS overrides.

**Why:** Monochrome circles looked flat. Colorful initials add personality, help visually distinguish clients at a glance, and match the sophistication of modern SaaS review walls.

## v1.1 — 2026-02-14

### Global Navigation — Absolute Paths & Sub-Page Fix
- **Absolute-style navigation paths** — `renderGlobalNav()` now uses absolute paths on every page: Services → `index.html#services-grid`, Staff → `staff.html`, Testimonials → `testimonials.html`, Logo → `index.html`. Removed the per-page conditional that produced different `#services` vs `index.html#services` hrefs.
- **Renamed services anchor** — The bento grid section on `index.html` changed from `id="services"` to `id="services-grid"` so the anchor target is explicit and unambiguous across all pages.
- **Fixed broken navigation on sub-pages** — `renderDynamicNav()` and `renderDynamicFooter()` were calling `e.preventDefault()` + `navigateTo()` (SPA pushState routing) on every page, but the virtual router elements (`#homeView`, `#pageView`) only exist on `index.html`. On sub-pages like `staff.html`, `testimonials.html`, or `thank-you.html`, this silently ate the click and nothing happened. Fixed by checking `isIndexPage` — SPA navigation is only used on the homepage; sub-pages let the browser follow the `index.html?page=slug` href normally.
- **Testimonials nav link** — Added between "Staff" and the CTA button in the shared nav, visible on all pages.

**Why:** Absolute paths and the sub-page routing fix eliminate the broken navigation on Locations, Test, Staff, and other sub-pages. Every link now works identically regardless of which page the visitor is on.

### Mobile Navigation FAB
- **Hidden nav links on mobile** — At `≤768px`, `.nav-links` is hidden (`display: none`) to declutter the mobile header. The logo remains visible for branding.
- **Floating Action Button** — A fixed pill-shaped FAB appears bottom-right on mobile with a calendar icon and "Book" label. Tapping it opens the Consultation Concierge modal via `openConsultModal()`. Styled with the button engine CSS variables so it follows the admin's chosen button style (Pill, Modern, or Glass).
- **Shared across all pages** — The FAB is appended to `document.body` by `renderGlobalNav()` in `main.js`, so it appears on `index.html`, `staff.html`, `thank-you.html`, and `testimonials.html` automatically.
- **Positioned to avoid dark mode toggle** — FAB sits at `right: 80px` to avoid overlapping the theme toggle at `right: 24px`.

**Why:** On mobile, the horizontal nav links were squished and the primary CTA ("Book a Consultation") was buried. The FAB provides a persistent, thumb-friendly conversion point.

### Testimonials Engine — Admin CRUD + Wall of Love
- **Admin Testimonials tab** — New sidebar link in `admin.html` with full CRUD: Add/Edit/Delete testimonials with Client Name, Practice Area (Asylum, Family, Removal, Citizenship, Work Visas), Quote textarea, Star Rating (1–5), and Active toggle. List rows show Active/Inactive badges, practice area badge, and star count.
- **Dashboard stat** — New "Testimonials" stat card on the admin dashboard showing active testimonial count.
- **`siteTestimonials` localStorage** — Data model: `{ id, name, area, quote, rating, active, createdAt }`. Shared `getTestimonials()` / `saveTestimonials()` helpers in `main.js`.
- **`testimonials.html` — Wall of Love** — New public page with a hero section and CSS-columns bento masonry grid (3 columns → 2 on tablet → 1 on mobile). Long and short quotes pack together naturally via `break-inside: avoid` + `column-count`. Each card is a glassmorphism panel with filled/empty star ratings, italic quote text, an initials circle avatar (e.g., "JO" for Jeffrey O'Brien), client name, and practice area badge. Cards use the same lift hover effect as bento cards (`translateY(-6px) scale(1.01)`). Scroll-reveal animations on each card.
- **Initials circles** — Each testimonial card shows a dark circular avatar with the client's initials (first + last name), providing a clean, sophisticated look without needing photos. Adapts to dark mode with inverted colors.
- **Glassmorphism consistency** — The navbar on `testimonials.html` uses the same shared `renderGlobalNav()` with `backdrop-filter: saturate(180%) blur(15px)`, matching every other page.
- **Dark mode support** — Testimonial cards, initials circles, and area badges all adapt to the dark theme.

**Why:** Client testimonials are a high-trust conversion driver for immigration law firms. The bento masonry layout creates visual variety where long and short quotes fit together perfectly, and the initials circles add a sophisticated personal touch without requiring client photos.

## v1.0 — 2026-02-14

### Global Navigation & Glassmorphism Refresh
- **`renderGlobalNav()` in main.js** — Single function that builds the identical navigation bar on every page. All three public pages (`index.html`, `staff.html`, `thank-you.html`) now use an empty `<nav class="navbar" id="globalNav">` placeholder that `renderGlobalNav()` populates on `DOMContentLoaded`. This eliminates the prior inconsistencies: staff.html had an inline `style` override on the Staff link, thank-you.html had "Home" instead of "Book a Consultation" as its CTA, and each page had a slightly different link structure.
- **Smart links** — The Services link auto-detects whether you're on the homepage (`#services`) or a subpage (`index.html#services`). The Staff link always points to `staff.html`. The logo always links back to `index.html`.
- **Glassmorphism navbar** — Switched from `position: fixed` to `position: sticky; top: 0; z-index: 1000` with `backdrop-filter: saturate(180%) blur(15px)` and `background: rgba(255,255,255,0.7)`. The bento grid and page content now visibly blur behind the nav as you scroll. Adjusted hero, page-view, and post-view top padding from 120–140px down to 80px since the sticky nav is in the document flow.
- **200ms nav link hover** — All `.nav-links a` elements use `transition: color 0.2s ease` for a subtle, consistent fade on hover.
- **Magnetic "Book a Consultation"** — The CTA button in the global nav (and the hero) follows the cursor with a gentle `translate()` on `mousemove`, built in the prior polish layer and now working across all pages via the shared nav.
- **Enhanced smooth scroll** — Updated `initSmoothScroll()` to handle both pure anchors (`#services`) and same-page anchors with a path prefix (`index.html#services`), with a 60px navbar offset.

**Why:** A single source of truth for navigation means zero drift between pages. The sticky glassmorphism bar creates the signature "content sliding behind frosted glass" effect that defines the Apple aesthetic, while the micro-interactions (magnetic CTA, 200ms fade) add tactile polish.

### Sophisticated Polish Layer
- **Typography tightening** — Added `letter-spacing: -0.01em` baseline to all heading elements (h1–h6) for that Apple typographic feel. Body text `line-height: 1.6` was already in place.
- **Magnetic button hover** — Primary buttons (nav CTA, hero CTA, consultation submit) now subtly follow the cursor with a `translate()` effect on `mousemove`, snapping back on `mouseleave`. Gives an interactive, tactile feel without being distracting.
- **Enhanced bento card lift** — Bento cards now lift higher on hover (`translateY(-6px) scale(1.01)`) with a deeper, more diffused shadow (`0 20px 60px`) for a premium floating effect.
- **Smooth scroll** — All internal anchor links (`href="#..."`) now use JS-based smooth scrolling with a 60px navbar offset, delegated at the document level so dynamically rendered links also work.
- **Navbar glassmorphism tuned** — Reduced navbar `backdrop-filter` from `blur(20px)` to `blur(10px)` so content sliding underneath is subtly visible through the frosted glass, adding depth without sacrificing readability.
- **Dark mode** — A small circular toggle (moon/sun icons) fixed in the bottom-right corner switches between light and dark themes. Dark mode overrides the CSS custom property palette (`--white`, `--off-white`, `--light-gray`, `--mid-gray`, `--dark`), plus targeted overrides for the navbar, bento cards, post cards, footer, hero button, consultation modal, and form inputs. Preference is persisted to `localStorage` under the `theme` key and restored on every page load.

**Why:** Elevates the site from functional to premium with attention to micro-interactions, typographic precision, and adaptive theming — the kind of details that distinguish an Apple-quality experience.

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
