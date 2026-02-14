/* ══════════════════════════════════════════════
   Lightweight Analytics Engine — Phase 2
   Privacy-first · localStorage only · No cookies
   ══════════════════════════════════════════════ */

(function() {
  "use strict";

  var STORAGE_KEY = "siteAnalytics";
  var MAX_EVENTS = 500;
  var GEO_CACHE_KEY = "siteAnalyticsGeo";
  var GEO_CACHE_TTL = 86400000; // 24 hours

  function getAnalyticsData() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null") || { events: [] };
    } catch (e) {
      return { events: [] };
    }
  }

  function saveAnalyticsData(data) {
    if (data.events.length > MAX_EVENTS) {
      data.events = data.events.slice(-MAX_EVENTS);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function getDeviceType() {
    return window.innerWidth <= 768 ? "Mobile" : "Desktop";
  }

  function getDateKey(date) {
    var d = date || new Date();
    return d.getFullYear() + "-" +
      String(d.getMonth() + 1).padStart(2, "0") + "-" +
      String(d.getDate()).padStart(2, "0");
  }

  // ── Geo lookup (cached 24h, privacy-friendly) ──

  var _geoData = null;

  function fetchGeo(callback) {
    if (_geoData) { callback(_geoData); return; }

    // Check cache
    try {
      var cached = JSON.parse(localStorage.getItem(GEO_CACHE_KEY) || "null");
      if (cached && cached.ts && (Date.now() - cached.ts < GEO_CACHE_TTL)) {
        _geoData = cached.data;
        callback(_geoData);
        return;
      }
    } catch (e) {}

    // Fetch from ipapi.co (free, no API key, privacy-friendly)
    fetch("https://ipapi.co/json/", { mode: "cors" })
      .then(function(res) { return res.json(); })
      .then(function(json) {
        _geoData = { city: json.city || "", region: json.region || "", country: json.country_name || "" };
        localStorage.setItem(GEO_CACHE_KEY, JSON.stringify({ data: _geoData, ts: Date.now() }));
        callback(_geoData);
      })
      .catch(function() {
        _geoData = { city: "Unknown", region: "Unknown", country: "Unknown" };
        callback(_geoData);
      });
  }

  // Initialize geo on load
  fetchGeo(function() {});

  // ── Public API ──

  window.siteAnalytics = {

    track: function(type, meta) {
      var self = this;
      var baseMeta = meta || {};

      function save(geo) {
        var data = getAnalyticsData();
        data.events.push({
          type: type,
          meta: baseMeta,
          device: getDeviceType(),
          language: localStorage.getItem("siteLanguage") || "en",
          city: geo ? geo.city : "",
          region: geo ? geo.region : "",
          date: getDateKey(),
          ts: Date.now()
        });
        saveAnalyticsData(data);
      }

      if (_geoData) {
        save(_geoData);
      } else {
        fetchGeo(function(geo) { save(geo); });
      }
    },

    trackBookClick: function() {
      this.track("book_click");
    },

    trackFormSubmission: function(status, goal) {
      this.track("form_submission", { status: status || "", goal: goal || "" });
    },

    trackPathFinderChoice: function(step, value, label) {
      this.track("pathfinder_choice", { step: step, value: value || "", label: label || "" });
    },

    trackLanguageChange: function(langCode) {
      this.track("language_change", { language: langCode });
    },

    trackScrollDepth: function(section, depth) {
      this.track("scroll_depth", { section: section, depth: depth });
    },

    trackModalTime: function(tileTitle, durationMs) {
      this.track("modal_time", { tile: tileTitle, duration: durationMs });
    },

    // ── Query helpers ──

    getEvents: function() {
      return getAnalyticsData().events;
    },

    getSubmissionsLast7Days: function() {
      var events = this.getEvents();
      var now = new Date();
      var days = [];
      for (var i = 6; i >= 0; i--) {
        var d = new Date(now);
        d.setDate(d.getDate() - i);
        days.push(getDateKey(d));
      }
      var counts = {};
      days.forEach(function(day) { counts[day] = 0; });
      events.forEach(function(ev) {
        if (ev.type === "form_submission" && counts[ev.date] !== undefined) {
          counts[ev.date]++;
        }
      });
      return days.map(function(day) {
        var parts = day.split("-");
        return { date: day, label: parseInt(parts[1]) + "/" + parseInt(parts[2]), count: counts[day] };
      });
    },

    getTopGoals: function(limit) {
      var events = this.getEvents();
      var goalCounts = {};
      events.forEach(function(ev) {
        if (ev.type === "form_submission" && ev.meta && ev.meta.goal) {
          goalCounts[ev.meta.goal] = (goalCounts[ev.meta.goal] || 0) + 1;
        }
        if (ev.type === "pathfinder_choice" && ev.meta && ev.meta.step === "goal") {
          var gKey = ev.meta.label || ev.meta.value;
          if (gKey) goalCounts[gKey] = (goalCounts[gKey] || 0) + 1;
        }
      });
      return Object.keys(goalCounts).map(function(key) {
        return { goal: key, count: goalCounts[key] };
      }).sort(function(a, b) { return b.count - a.count; }).slice(0, limit || 5);
    },

    getLanguageBreakdown: function() {
      var events = this.getEvents();
      var langCounts = {};
      events.forEach(function(ev) {
        if (ev.type === "form_submission" || ev.type === "book_click") {
          langCounts[ev.language || "en"] = (langCounts[ev.language || "en"] || 0) + 1;
        }
      });
      return langCounts;
    },

    getRegionalBreakdown: function() {
      var events = this.getEvents();
      var regionCounts = {};
      events.forEach(function(ev) {
        if (ev.city && ev.city !== "Unknown") {
          var label = ev.city + (ev.region ? ", " + ev.region : "");
          regionCounts[label] = (regionCounts[label] || 0) + 1;
        }
      });
      return Object.keys(regionCounts).map(function(k) {
        return { region: k, count: regionCounts[k] };
      }).sort(function(a, b) { return b.count - a.count; });
    },

    getDeviceBreakdown: function() {
      var events = this.getEvents();
      var counts = { Mobile: 0, Desktop: 0 };
      events.forEach(function(ev) {
        if (ev.device === "Mobile") counts.Mobile++;
        else counts.Desktop++;
      });
      return counts;
    },

    getTotalBookClicks: function() {
      return this.getEvents().filter(function(ev) { return ev.type === "book_click"; }).length;
    },

    getTotalSubmissions: function() {
      return this.getEvents().filter(function(ev) { return ev.type === "form_submission"; }).length;
    },

    clearAll: function() {
      localStorage.removeItem(STORAGE_KEY);
    }
  };
})();
