/* =============================================
   app.js - Router + Data Loading
   ============================================= */

(function () {
  'use strict';

  // Global state
  window.APP = {
    papers: [],
    filteredPapers: [],
    currentSession: 'all',
    filters: {
      process: '',
      application: '',
      innovationType: '',
      analyticalTags: [],
      search: ''
    },
    sortCol: null,
    sortAsc: true,
    lightboxImages: [],
    lightboxCaptions: [],
    lightboxLabels: [],
    lightboxIndex: 0,
    privateMode: false
  };

  // Base path for data files (relative to server root)
  var basePath = (function () {
    var p = window.location.pathname;
    var dir = p.substring(0, p.lastIndexOf('/') + 1);
    return dir + '../';
  })();

  // Image directory: use images_web/ for compressed (GitHub Pages), images/ for full-res (local)
  // Auto-detect: if images_web/ exists, use it; otherwise fall back to images/
  var imageDir = 'images_web';
  (function detectImageDir() {
    var testUrl = basePath + 'images_web/2.1/fig_1.png';
    var xhr = new XMLHttpRequest();
    xhr.open('HEAD', testUrl, true);
    xhr.onload = function () {
      if (xhr.status >= 400) {
        window.APP.imageDir = 'images';
      }
    };
    xhr.onerror = function () {
      window.APP.imageDir = 'images';
    };
    xhr.send();
  })();

  window.APP.basePath = basePath;
  window.APP.imageDir = imageDir;

  // Fetch papers.json
  function loadPapers() {
    var app = document.getElementById('app');
    app.innerHTML = '<div class="loading"><div class="loading-spinner"></div><div>Loading papers...</div></div>';

    return fetch(basePath + 'data/papers.json')
      .then(function (res) {
        if (!res.ok) throw new Error('Failed to load papers.json: ' + res.status);
        return res.json();
      })
      .then(function (data) {
        window.APP.papers = data;
        window.APP.filteredPapers = data.slice();
        return data;
      });
  }

  // Route handler
  function handleRoute() {
    var hash = window.location.hash || '#overview';
    var app = document.getElementById('app');

    if (hash === '#overview' || hash === '' || hash === '#') {
      if (typeof window.renderOverview === 'function') {
        window.renderOverview(app);
      }
    } else if (hash.startsWith('#paper/')) {
      var id = hash.replace('#paper/', '');
      if (typeof window.renderDetail === 'function') {
        window.renderDetail(app, id);
      }
    } else {
      if (typeof window.renderOverview === 'function') {
        window.renderOverview(app);
      }
    }
  }

  // Lightbox controls
  function initLightbox() {
    var overlay = document.getElementById('lightbox');
    var img = document.getElementById('lightbox-img');
    var closeBtn = document.getElementById('lightbox-close');
    var prevBtn = document.getElementById('lightbox-prev');
    var nextBtn = document.getElementById('lightbox-next');

    closeBtn.addEventListener('click', closeLightbox);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeLightbox();
    });

    prevBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var idx = window.APP.lightboxIndex - 1;
      if (idx < 0) idx = window.APP.lightboxImages.length - 1;
      showLightboxImage(idx);
    });

    nextBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var idx = window.APP.lightboxIndex + 1;
      if (idx >= window.APP.lightboxImages.length) idx = 0;
      showLightboxImage(idx);
    });

    document.addEventListener('keydown', function (e) {
      if (!overlay.classList.contains('active')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') prevBtn.click();
      if (e.key === 'ArrowRight') nextBtn.click();
    });
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('active');
  }

  function showLightboxImage(idx) {
    window.APP.lightboxIndex = idx;
    var img = document.getElementById('lightbox-img');
    img.src = window.APP.lightboxImages[idx];

    // Update caption
    var captionEl = document.getElementById('lightbox-caption');
    var counterEl = document.getElementById('lightbox-counter');

    if (captionEl) {
      var captions = window.APP.lightboxCaptions;
      captionEl.textContent = (captions && captions[idx]) ? captions[idx] : '';
      captionEl.style.display = (captions && captions[idx]) ? 'block' : 'none';
    }

    if (counterEl) {
      var labels = window.APP.lightboxLabels;
      counterEl.textContent = (labels && labels[idx]) ? labels[idx] : ((idx + 1) + '/' + window.APP.lightboxImages.length);
    }
  }

  window.openLightbox = function (images, idx, captions, labels) {
    window.APP.lightboxImages = images;
    window.APP.lightboxCaptions = captions || [];
    window.APP.lightboxLabels = labels || [];
    window.APP.lightboxIndex = idx;
    var overlay = document.getElementById('lightbox');
    var img = document.getElementById('lightbox-img');
    img.src = images[idx];
    overlay.classList.add('active');

    // Update caption and counter
    var captionEl = document.getElementById('lightbox-caption');
    var counterEl = document.getElementById('lightbox-counter');

    if (captionEl) {
      captionEl.textContent = (captions && captions[idx]) ? captions[idx] : '';
      captionEl.style.display = (captions && captions[idx]) ? 'block' : 'none';
    }

    if (counterEl) {
      counterEl.textContent = (labels && labels[idx]) ? labels[idx] : ((idx + 1) + '/' + images.length);
    }
  };

  // Helper: get innovation type CSS class
  window.getTypeClass = function (type) {
    if (!type) return 'tag-neutral';
    var t = type.toLowerCase().replace(/[-_\s]/g, '');
    if (t === 'hwarch') return 'tag-hw-arch';
    if (t === 'hwcircuit') return 'tag-hw-circuit';
    if (t === 'sw') return 'tag-sw';
    if (t === 'codesign') return 'tag-codesign';
    if (t === 'system') return 'tag-system';
    return 'tag-neutral';
  };

  // Helper: get type CSS class for idea cards
  window.getIdeaTypeClass = function (type) {
    if (!type) return '';
    var t = type.toLowerCase().replace(/[-_\s]/g, '');
    if (t === 'hwarch') return 'type-hw-arch';
    if (t === 'hwcircuit') return 'type-hw-circuit';
    if (t === 'sw') return 'type-sw';
    if (t === 'codesign') return 'type-codesign';
    if (t === 'system') return 'type-system';
    return '';
  };

  // Helper: escape HTML
  window.escapeHtml = function (str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  };

  // Helper: get sorted paper list for navigation
  window.getPaperIds = function () {
    return window.APP.papers.map(function (p) { return p.id; });
  };

  // Helper: find paper by id
  window.findPaper = function (id) {
    return window.APP.papers.find(function (p) { return p.id === id; });
  };

  // Init
  document.addEventListener('DOMContentLoaded', function () {
    initLightbox();
    loadPapers()
      .then(function () {
        handleRoute();
      })
      .catch(function (err) {
        document.getElementById('app').innerHTML =
          '<div class="empty-state"><p>Failed to load data.</p><p style="color:var(--text-muted);font-size:0.85rem;">' +
          escapeHtml(err.message) + '</p></div>';
      });

    window.addEventListener('hashchange', handleRoute);
  });
})();
