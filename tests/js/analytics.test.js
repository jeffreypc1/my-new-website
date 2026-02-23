/**
 * Tests for analytics.js — event tracking, aggregation, and localStorage.
 *
 * The module uses an IIFE that attaches to window.siteAnalytics.
 * We mock localStorage and fetch before loading the module.
 */

"use strict";

// ── localStorage mock ─────────────────────────────────────────────────────

function makeLocalStorage() {
  const store = {};
  return {
    getItem: (k) => store[k] ?? null,
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { Object.keys(store).forEach(k => delete store[k]); },
    _store: store,
  };
}

// ── Window / global setup ─────────────────────────────────────────────────

let analytics;

function loadAnalytics(ls) {
  // Provide browser globals Jest doesn't have
  global.localStorage = ls;
  global.window = {
    siteAnalytics: null,
    innerWidth: 1200,
    location: { href: "" },
  };
  global.fetch = jest.fn(() => Promise.resolve({
    json: () => Promise.resolve({ city: "Boston", region: "MA", country_name: "United States" })
  }));

  // Reset module cache and re-require
  jest.resetModules();
  require("../../analytics.js");
  return global.window.siteAnalytics;
}

beforeEach(() => {
  analytics = loadAnalytics(makeLocalStorage());
});


// ── getDateKey ────────────────────────────────────────────────────────────

describe("getDateKey (via getSubmissionsLast7Days structure)", () => {
  test("last7Days returns 7 entries with label M/D", () => {
    const days = analytics.getSubmissionsLast7Days();
    expect(days).toHaveLength(7);
    days.forEach(d => {
      expect(d).toHaveProperty("date");
      expect(d).toHaveProperty("label");
      expect(d).toHaveProperty("count");
      // label is "M/D" format
      expect(d.label).toMatch(/^\d+\/\d+$/);
    });
  });

  test("days are in ascending order", () => {
    const days = analytics.getSubmissionsLast7Days();
    for (let i = 1; i < days.length; i++) {
      expect(days[i].date >= days[i - 1].date).toBe(true);
    }
  });
});


// ── track & getEvents ─────────────────────────────────────────────────────

describe("track / getEvents", () => {
  test("getEvents returns empty array initially", () => {
    expect(analytics.getEvents()).toEqual([]);
  });

  test("track adds an event", () => {
    analytics.track("book_click");
    const events = analytics.getEvents();
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("book_click");
  });

  test("track stores device type", () => {
    analytics.track("page_view");
    expect(analytics.getEvents()[0].device).toBe("Desktop");
  });

  test("track stores meta", () => {
    analytics.track("form_submission", { status: "submitted", goal: "green card" });
    const ev = analytics.getEvents()[0];
    expect(ev.meta.status).toBe("submitted");
    expect(ev.meta.goal).toBe("green card");
  });

  test("track stores timestamp", () => {
    const before = Date.now();
    analytics.track("test_event");
    const after = Date.now();
    const ts = analytics.getEvents()[0].ts;
    expect(ts).toBeGreaterThanOrEqual(before);
    expect(ts).toBeLessThanOrEqual(after);
  });
});


// ── MAX_EVENTS cap ────────────────────────────────────────────────────────

describe("MAX_EVENTS cap (500)", () => {
  test("storage is trimmed to last 500 events", () => {
    for (let i = 0; i < 520; i++) {
      analytics.track("test");
    }
    // Re-read raw storage
    const stored = JSON.parse(global.localStorage.getItem("siteAnalytics"));
    expect(stored.events.length).toBeLessThanOrEqual(500);
  });
});


// ── Convenience trackers ──────────────────────────────────────────────────

describe("convenience trackers", () => {
  test("trackBookClick records book_click", () => {
    analytics.trackBookClick();
    expect(analytics.getEvents()[0].type).toBe("book_click");
  });

  test("trackFormSubmission records form_submission with meta", () => {
    analytics.trackFormSubmission("submitted", "green card");
    const ev = analytics.getEvents()[0];
    expect(ev.type).toBe("form_submission");
    expect(ev.meta.status).toBe("submitted");
    expect(ev.meta.goal).toBe("green card");
  });

  test("trackPathFinderChoice records step/value/label", () => {
    analytics.trackPathFinderChoice("goal", "green_card", "Green Card");
    const ev = analytics.getEvents()[0];
    expect(ev.type).toBe("pathfinder_choice");
    expect(ev.meta.step).toBe("goal");
    expect(ev.meta.label).toBe("Green Card");
  });

  test("trackLanguageChange records language", () => {
    analytics.trackLanguageChange("es");
    const ev = analytics.getEvents()[0];
    expect(ev.type).toBe("language_change");
    expect(ev.meta.language).toBe("es");
  });

  test("trackScrollDepth records section and depth", () => {
    analytics.trackScrollDepth("hero", 50);
    const ev = analytics.getEvents()[0];
    expect(ev.type).toBe("scroll_depth");
    expect(ev.meta.section).toBe("hero");
    expect(ev.meta.depth).toBe(50);
  });

  test("trackModalTime records tile and duration", () => {
    analytics.trackModalTime("Work Permits", 5000);
    const ev = analytics.getEvents()[0];
    expect(ev.type).toBe("modal_time");
    expect(ev.meta.tile).toBe("Work Permits");
    expect(ev.meta.duration).toBe(5000);
  });
});


// ── Aggregation helpers ───────────────────────────────────────────────────

describe("getTotalBookClicks", () => {
  test("counts book_click events", () => {
    analytics.trackBookClick();
    analytics.trackBookClick();
    analytics.trackFormSubmission("submitted", "");
    expect(analytics.getTotalBookClicks()).toBe(2);
  });
});

describe("getTotalSubmissions", () => {
  test("counts form_submission events", () => {
    analytics.trackFormSubmission("submitted", "");
    analytics.trackFormSubmission("submitted", "");
    analytics.trackBookClick();
    expect(analytics.getTotalSubmissions()).toBe(2);
  });
});

describe("getTopGoals", () => {
  test("ranks goals by count descending", () => {
    analytics.trackFormSubmission("submitted", "green card");
    analytics.trackFormSubmission("submitted", "green card");
    analytics.trackFormSubmission("submitted", "citizenship");
    const top = analytics.getTopGoals(5);
    expect(top[0].goal).toBe("green card");
    expect(top[0].count).toBe(2);
    expect(top[1].goal).toBe("citizenship");
  });

  test("includes pathfinder goals", () => {
    analytics.trackPathFinderChoice("goal", "asylum", "Asylum");
    const top = analytics.getTopGoals(5);
    expect(top.some(g => g.goal === "Asylum")).toBe(true);
  });

  test("respects limit", () => {
    for (let i = 0; i < 10; i++) {
      analytics.trackFormSubmission("submitted", `goal-${i}`);
    }
    expect(analytics.getTopGoals(3)).toHaveLength(3);
  });
});

describe("getLanguageBreakdown", () => {
  test("counts language from form_submission events", () => {
    analytics.track("form_submission", { status: "submitted" });
    const breakdown = analytics.getLanguageBreakdown();
    expect(typeof breakdown).toBe("object");
    expect(Object.values(breakdown).reduce((a, b) => a + b, 0)).toBeGreaterThan(0);
  });
});

describe("getDeviceBreakdown", () => {
  test("categorizes Mobile vs Desktop", () => {
    analytics.track("page_view"); // innerWidth=1200 → Desktop
    const breakdown = analytics.getDeviceBreakdown();
    expect(breakdown.Desktop).toBeGreaterThan(0);
    expect(typeof breakdown.Mobile).toBe("number");
  });

  test("mobile when innerWidth <= 768", () => {
    global.window.innerWidth = 375;
    analytics.track("page_view");
    const breakdown = analytics.getDeviceBreakdown();
    expect(breakdown.Mobile).toBeGreaterThan(0);
  });
});

describe("getSubmissionsLast7Days", () => {
  test("counts only form_submission events in the last 7 days", () => {
    analytics.trackFormSubmission("submitted", "");
    analytics.trackFormSubmission("submitted", "");
    const days = analytics.getSubmissionsLast7Days();
    const totalCount = days.reduce((sum, d) => sum + d.count, 0);
    expect(totalCount).toBe(2);
  });
});


// ── clearAll ──────────────────────────────────────────────────────────────

describe("clearAll", () => {
  test("removes all stored events", () => {
    analytics.trackBookClick();
    analytics.trackBookClick();
    expect(analytics.getEvents()).toHaveLength(2);
    analytics.clearAll();
    expect(analytics.getEvents()).toHaveLength(0);
  });
});
