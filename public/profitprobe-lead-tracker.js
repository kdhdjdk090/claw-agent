/*
 * ProfitProbe Lead Popup + Attribution Tracker
 * Drop-in script for landing-page-only popup gating and full lead attribution capture.
 */
(function () {
  "use strict";

  var CONFIG = {
    popupId: "profitprobeLeadPopup",
    formSelector: "#profitprobeLeadForm, form[data-lead-form='profitprobe'], form.lead-form",
    endpoint: "/api/lead-events",
    popupDelayMs: 18000,
    minScrollPct: 45,
    maxShowsPerSession: 1,
    cooldownHours: 24,
    cookieDays: 90,
    landingPaths: [
      "/learn/trading/",
      "/free-forex-guide",
      "/technical-analysis",
      "/crypto-trading",
      "/stock-market-101",
      "/trading-psychology",
      "/risk-management",
      "/free-trading-signals",
      "/best-forex-brokers",
      "/gold-trading",
      "/free-trading-academy",
      "/live-webinars",
      "/forex-india",
      "/day-trading-strategies",
      "/mt4-mt5-guide",
      "/small-account-trading",
      "/price-action-trading",
      "/fundamental-analysis",
      "/algo-trading",
      "/free-ebooks",
      "/swing-trading",
      "/free-mentorship",
      "/trading-calculators"
    ],
    landingCampaignMap: {
      "/free-forex-guide": { campaign_id: "ForexTradingGuide", campaign: "Forex basics & currency pairs" },
      "/technical-analysis": { campaign_id: "TechnicalAnalysis", campaign: "Chart reading & indicators" },
      "/crypto-trading": { campaign_id: "CryptoTrading", campaign: "Bitcoin & altcoin trading" },
      "/stock-market-101": { campaign_id: "StockMarket101", campaign: "Stock investing for beginners" },
      "/trading-psychology": { campaign_id: "TradingPsychology", campaign: "Mindset & emotional discipline" },
      "/risk-management": { campaign_id: "RiskManagement", campaign: "Position sizing & capital protection" },
      "/free-trading-signals": { campaign_id: "FreeTradingSignals", campaign: "Daily trade signals" },
      "/best-forex-brokers": { campaign_id: "BestForexBrokers", campaign: "Broker comparison & reviews" },
      "/gold-trading": { campaign_id: "GoldTrading", campaign: "XAU/USD trading strategies" },
      "/free-trading-academy": { campaign_id: "TradingAcademy", campaign: "Structured learning tracks" },
      "/live-webinars": { campaign_id: "LiveWebinars", campaign: "Weekly live sessions schedule" },
      "/forex-india": { campaign_id: "ForexForIndians", campaign: "SEBI regulations & INR pairs" },
      "/day-trading-strategies": { campaign_id: "DayTradingStrategies", campaign: "Intraday trading tactics" },
      "/mt4-mt5-guide": { campaign_id: "MT4MT5Guide", campaign: "MetaTrader setup & usage" },
      "/small-account-trading": { campaign_id: "SmallAccountTrading", campaign: "Grow small capital accounts" },
      "/price-action-trading": { campaign_id: "PriceActionTrading", campaign: "Naked chart setups" },
      "/fundamental-analysis": { campaign_id: "FundamentalAnalysis", campaign: "Macro & news driven trading" },
      "/algo-trading": { campaign_id: "AlgoTrading", campaign: "Automated system trading" },
      "/free-ebooks": { campaign_id: "FreeEbooks", campaign: "Downloadable trading ebooks" },
      "/swing-trading": { campaign_id: "SwingTrading", campaign: "Multi-day position trading" },
      "/free-mentorship": { campaign_id: "FreeMentorship", campaign: "Mentor-led coaching" },
      "/trading-calculators": { campaign_id: "TradingCalculators", campaign: "Risk and lot size calculators" },
      "/learn/trading": { campaign_id: "TradingHub", campaign: "Trading education hub" }
    },
    hiddenFieldMap: {
      visitor_id: "visitor_id",
      lead_score: "lead_score",
      landing_path: "landing_path",
      landing_url: "landing_url",
      referrer: "referrer",
      source: "source",
      medium: "medium",
      campaign: "campaign",
      campaign_id: "campaign_id",
      term: "term",
      keyword: "keyword",
      search_term: "search_term",
      adgroup: "adgroup",
      ad_id: "ad_id",
      gclid: "gclid",
      fbclid: "fbclid",
      msclkid: "msclkid",
      ttclid: "ttclid",
      twclid: "twclid",
      li_fat_id: "li_fat_id",
      gbraid: "gbraid",
      wbraid: "wbraid",
      yclid: "yclid",
      first_touch_ts: "first_touch_ts",
      last_touch_ts: "last_touch_ts"
    }
  };

  var PARAM_KEYS = {
    source: ["utm_source", "source", "src"],
    medium: ["utm_medium", "medium"],
    campaign: ["utm_campaign", "campaign", "cmp", "cn"],
    campaign_id: ["utm_id", "campaign_id", "cid", "cmpid"],
    term: ["utm_term", "term", "kw", "keyword"],
    keyword: ["keyword", "kw", "utm_term", "match_kw"],
    adgroup: ["adgroup", "ad_group", "adgroupid"],
    ad_id: ["ad_id", "adid", "creative", "creative_id"],
    search_term: ["search_term", "searchterm", "query", "q", "s", "p"],
    gclid: ["gclid"],
    fbclid: ["fbclid"],
    msclkid: ["msclkid"],
    ttclid: ["ttclid"],
    twclid: ["twclid"],
    li_fat_id: ["li_fat_id"],
    gbraid: ["gbraid"],
    wbraid: ["wbraid"],
    yclid: ["yclid"]
  };

  function normalizePath(pathname) {
    var p = (pathname || "").toLowerCase();
    if (!p) {
      return "/";
    }
    if (p.length > 1 && p.endsWith("/")) {
      p = p.slice(0, -1);
    }
    return p;
  }

  function isLandingPage(pathname) {
    var current = normalizePath(pathname);
    for (var i = 0; i < CONFIG.landingPaths.length; i++) {
      var allowed = normalizePath(CONFIG.landingPaths[i]);
      if (current === allowed) {
        return true;
      }
    }
    return false;
  }

  function getLandingCampaign(pathname) {
    var key = normalizePath(pathname);
    return CONFIG.landingCampaignMap[key] || null;
  }

  function getCookie(name) {
    var escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    var match = document.cookie.match(new RegExp("(?:^|; )" + escaped + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : "";
  }

  function setCookie(name, value, days) {
    var maxAge = Math.floor((days || CONFIG.cookieDays) * 24 * 60 * 60);
    var secure = location.protocol === "https:" ? "; Secure" : "";
    document.cookie = name + "=" + encodeURIComponent(value) + "; Max-Age=" + maxAge + "; Path=/; SameSite=Lax" + secure;
  }

  function safeJsonParse(raw) {
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (_) {
      return null;
    }
  }

  function getQueryParams() {
    var out = {};
    var search = new URLSearchParams(location.search || "");
    search.forEach(function (value, key) {
      if (!out[key]) {
        out[key] = value;
      }
    });
    if (location.hash && location.hash.indexOf("=") !== -1) {
      var hash = new URLSearchParams(location.hash.replace(/^#/, ""));
      hash.forEach(function (value, key) {
        if (!out[key]) {
          out[key] = value;
        }
      });
    }
    return out;
  }

  function pickFirstValue(params, keys) {
    for (var i = 0; i < keys.length; i++) {
      var value = params[keys[i]];
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }
    }
    return "";
  }

  function inferFromReferrer(referrer) {
    if (!referrer) {
      return { source: "direct", medium: "none", search_term: "" };
    }
    try {
      var r = new URL(referrer);
      var host = (r.hostname || "").toLowerCase();
      var p = new URLSearchParams(r.search || "");
      var query = p.get("q") || p.get("p") || p.get("query") || p.get("s") || "";
      if (host.indexOf("google.") >= 0) {
        return { source: "google", medium: "organic", search_term: query };
      }
      if (host.indexOf("bing.") >= 0) {
        return { source: "bing", medium: "organic", search_term: query };
      }
      if (host.indexOf("yahoo.") >= 0) {
        return { source: "yahoo", medium: "organic", search_term: query };
      }
      if (host.indexOf("duckduckgo.") >= 0) {
        return { source: "duckduckgo", medium: "organic", search_term: query };
      }
      if (host.indexOf("facebook.") >= 0 || host.indexOf("instagram.") >= 0) {
        return { source: "meta", medium: "social", search_term: "" };
      }
      return { source: host, medium: "referral", search_term: query };
    } catch (_) {
      return { source: "unknown", medium: "referral", search_term: "" };
    }
  }

  function parseStorageAttribution() {
    var first = safeJsonParse(localStorage.getItem("pp_first_touch"));
    var last = safeJsonParse(sessionStorage.getItem("pp_last_touch"));
    return { first: first, last: last };
  }

  function resolveAttribution() {
    var params = getQueryParams();
    var storage = parseStorageAttribution();
    var nowIso = new Date().toISOString();
    var ref = document.referrer || "";
    var inferred = inferFromReferrer(ref);

    var landingCampaign = getLandingCampaign(location.pathname) || { campaign_id: "", campaign: "" };

    var payload = {
      visitor_id: getVisitorId(),
      landing_path: location.pathname,
      landing_url: location.href,
      referrer: ref,
      source: pickFirstValue(params, PARAM_KEYS.source) || inferred.source,
      medium: pickFirstValue(params, PARAM_KEYS.medium) || inferred.medium,
      campaign: pickFirstValue(params, PARAM_KEYS.campaign) || landingCampaign.campaign,
      campaign_id: pickFirstValue(params, PARAM_KEYS.campaign_id) || landingCampaign.campaign_id,
      term: pickFirstValue(params, PARAM_KEYS.term),
      keyword: pickFirstValue(params, PARAM_KEYS.keyword),
      search_term: pickFirstValue(params, PARAM_KEYS.search_term) || inferred.search_term,
      adgroup: pickFirstValue(params, PARAM_KEYS.adgroup),
      ad_id: pickFirstValue(params, PARAM_KEYS.ad_id),
      gclid: pickFirstValue(params, PARAM_KEYS.gclid),
      fbclid: pickFirstValue(params, PARAM_KEYS.fbclid),
      msclkid: pickFirstValue(params, PARAM_KEYS.msclkid),
      ttclid: pickFirstValue(params, PARAM_KEYS.ttclid),
      twclid: pickFirstValue(params, PARAM_KEYS.twclid),
      li_fat_id: pickFirstValue(params, PARAM_KEYS.li_fat_id),
      gbraid: pickFirstValue(params, PARAM_KEYS.gbraid),
      wbraid: pickFirstValue(params, PARAM_KEYS.wbraid),
      yclid: pickFirstValue(params, PARAM_KEYS.yclid),
      first_touch_ts: "",
      last_touch_ts: nowIso
    };

    if (storage.first && storage.first.first_touch_ts) {
      payload.first_touch_ts = storage.first.first_touch_ts;
    } else {
      payload.first_touch_ts = nowIso;
    }

    if (storage.last && storage.last.last_touch_ts) {
      payload.last_touch_ts = storage.last.last_touch_ts;
    }

    return payload;
  }

  function persistAttribution(attrs) {
    var first = safeJsonParse(localStorage.getItem("pp_first_touch"));
    if (!first) {
      localStorage.setItem("pp_first_touch", JSON.stringify(attrs));
      setCookie("pp_source", attrs.source || "", CONFIG.cookieDays);
      setCookie("pp_campaign", attrs.campaign || "", CONFIG.cookieDays);
      setCookie("pp_campaign_id", attrs.campaign_id || "", CONFIG.cookieDays);
      setCookie("pp_keyword", attrs.keyword || attrs.term || "", CONFIG.cookieDays);
      setCookie("pp_search_term", attrs.search_term || "", CONFIG.cookieDays);
    }
    sessionStorage.setItem("pp_last_touch", JSON.stringify(attrs));
  }

  function getVisitorId() {
    var id = localStorage.getItem("pp_visitor_id") || getCookie("pp_visitor_id");
    if (!id) {
      id = "pp_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem("pp_visitor_id", id);
      setCookie("pp_visitor_id", id, 365);
    }
    return id;
  }

  function getEngagementSnapshot() {
    var doc = document.documentElement;
    var body = document.body;
    var scrollTop = window.pageYOffset || doc.scrollTop || body.scrollTop || 0;
    var scrollHeight = Math.max(body.scrollHeight || 0, doc.scrollHeight || 0);
    var viewport = window.innerHeight || doc.clientHeight || 0;
    var pct = scrollHeight > 0 ? Math.round(((scrollTop + viewport) / scrollHeight) * 100) : 0;
    return {
      scroll_pct: Math.max(0, Math.min(100, pct)),
      viewport_w: window.innerWidth || 0,
      viewport_h: viewport,
      tz_offset_min: new Date().getTimezoneOffset(),
      lang: navigator.language || "",
      ua: navigator.userAgent || ""
    };
  }

  function calculateLeadScore(attrs, engagement) {
    var score = 25;

    if (attrs.gclid || attrs.msclkid || attrs.fbclid || attrs.ttclid || attrs.twclid) {
      score += 20;
    }
    if (attrs.campaign_id || attrs.campaign) {
      score += 15;
    }
    if (attrs.keyword || attrs.term) {
      score += 15;
    }
    if (attrs.search_term) {
      score += 10;
    }
    if (attrs.medium === "cpc" || attrs.medium === "paid" || attrs.medium === "ppc") {
      score += 10;
    }
    if (engagement.scroll_pct >= 55) {
      score += 10;
    }
    if (engagement.scroll_pct >= 75) {
      score += 5;
    }

    if (!attrs.source || attrs.source === "direct") {
      score -= 10;
    }

    return Math.max(0, Math.min(100, score));
  }

  function enrichAttribution() {
    var attrs = resolveAttribution();
    persistAttribution(attrs);
    var engagement = getEngagementSnapshot();
    attrs.lead_score = calculateLeadScore(attrs, engagement);
    attrs.engagement = engagement;
    return attrs;
  }

  function ensureHiddenInput(form, name, value) {
    var el = form.querySelector('input[name="' + name + '"]');
    if (!el) {
      el = document.createElement("input");
      el.type = "hidden";
      el.name = name;
      form.appendChild(el);
    }
    el.value = value == null ? "" : String(value);
  }

  function bindTrackingToForms() {
    var forms = document.querySelectorAll(CONFIG.formSelector);
    if (!forms.length) {
      return;
    }
    var attrs = enrichAttribution();
    for (var i = 0; i < forms.length; i++) {
      var form = forms[i];
      Object.keys(CONFIG.hiddenFieldMap).forEach(function (key) {
        var inputName = CONFIG.hiddenFieldMap[key];
        ensureHiddenInput(form, inputName, attrs[key] || "");
      });

      if (form.dataset.ppTrackingBound === "1") {
        continue;
      }
      form.dataset.ppTrackingBound = "1";
      form.addEventListener("submit", function () {
        var latest = enrichAttribution();
        sendLeadEvent("lead_submit", latest);
      });
    }
  }

  function getSessionShowCount() {
    var v = parseInt(sessionStorage.getItem("pp_popup_show_count") || "0", 10);
    if (isNaN(v)) {
      return 0;
    }
    return v;
  }

  function shouldShowPopup() {
    if (!isLandingPage(location.pathname)) {
      return false;
    }
    if (getSessionShowCount() >= CONFIG.maxShowsPerSession) {
      return false;
    }

    var lastShown = parseInt(localStorage.getItem("pp_popup_last_shown_ts") || "0", 10);
    var cooldownMs = CONFIG.cooldownHours * 60 * 60 * 1000;
    if (lastShown > 0 && Date.now() - lastShown < cooldownMs) {
      return false;
    }
    return true;
  }

  function markPopupShown() {
    sessionStorage.setItem("pp_popup_show_count", String(getSessionShowCount() + 1));
    localStorage.setItem("pp_popup_last_shown_ts", String(Date.now()));
  }

  function getPopupElement() {
    return document.getElementById(CONFIG.popupId);
  }

  function openPopup(trigger) {
    if (!shouldShowPopup()) {
      return;
    }
    var popup = getPopupElement();
    if (!popup) {
      return;
    }
    popup.classList.add("open");
    popup.setAttribute("aria-hidden", "false");
    markPopupShown();

    var attrs = enrichAttribution();
    attrs.popup_trigger = trigger || "unknown";
    sendLeadEvent("popup_open", attrs);
  }

  function closePopup() {
    var popup = getPopupElement();
    if (!popup) {
      return;
    }
    popup.classList.remove("open");
    popup.setAttribute("aria-hidden", "true");
  }

  function sendLeadEvent(eventType, payload) {
    var body = {
      event_type: eventType,
      ts: new Date().toISOString(),
      page: {
        url: location.href,
        path: location.pathname,
        title: document.title
      },
      payload: payload || {}
    };

    var raw = JSON.stringify(body);
    try {
      if (navigator.sendBeacon) {
        var blob = new Blob([raw], { type: "application/json" });
        navigator.sendBeacon(CONFIG.endpoint, blob);
        return;
      }
    } catch (_) {}

    try {
      fetch(CONFIG.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: raw,
        keepalive: true
      }).catch(function () {});
    } catch (_) {}
  }

  function setupPopupTriggers() {
    if (!shouldShowPopup()) {
      return;
    }

    var opened = false;
    function openOnce(trigger) {
      if (opened) {
        return;
      }
      opened = true;
      openPopup(trigger);
    }

    setTimeout(function () {
      openOnce("timer");
    }, CONFIG.popupDelayMs);

    function onScroll() {
      var doc = document.documentElement;
      var body = document.body;
      var scrollTop = window.pageYOffset || doc.scrollTop || body.scrollTop || 0;
      var scrollHeight = Math.max(body.scrollHeight || 0, doc.scrollHeight || 0);
      var viewport = window.innerHeight || doc.clientHeight || 0;
      if (!scrollHeight) {
        return;
      }
      var pct = ((scrollTop + viewport) / scrollHeight) * 100;
      if (pct >= CONFIG.minScrollPct) {
        window.removeEventListener("scroll", onScroll, { passive: true });
        openOnce("scroll");
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });

    document.addEventListener("mouseout", function (e) {
      if (e.clientY <= 0) {
        openOnce("exit_intent");
      }
    });

    var popup = getPopupElement();
    if (!popup) {
      return;
    }
    var closeEls = popup.querySelectorAll("[data-popup-close]");
    for (var i = 0; i < closeEls.length; i++) {
      closeEls[i].addEventListener("click", closePopup);
    }
    popup.addEventListener("click", function (e) {
      if (e.target === popup) {
        closePopup();
      }
    });
  }

  function init() {
    var attrs = enrichAttribution();
    sendLeadEvent("landing_view", attrs);
    bindTrackingToForms();
    setupPopupTriggers();

    window.ProfitProbeLead = {
      openPopup: openPopup,
      closePopup: closePopup,
      isLandingPage: function () { return isLandingPage(location.pathname); },
      getAttribution: enrichAttribution,
      sendLeadEvent: sendLeadEvent
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
