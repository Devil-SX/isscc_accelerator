/* =============================================
   detail.js - Detail Page
   ============================================= */

(function () {
  'use strict';

  function countryFlag(code) {
    if (!code) return '';
    return String.fromCodePoint.apply(null, code.toUpperCase().split('').map(function (c) { return c.charCodeAt(0) + 127397; }));
  }

  function getAdjacentPapers(currentId) {
    var ids = window.getPaperIds();
    var idx = ids.indexOf(currentId);
    return {
      prev: idx > 0 ? ids[idx - 1] : null,
      next: idx < ids.length - 1 ? ids[idx + 1] : null
    };
  }

  function buildSidebar(currentId) {
    var papers = window.APP.papers || [];
    // Group papers by session
    var sessions = {};
    var sessionOrder = [];
    papers.forEach(function (p) {
      var s = p.session || 'Other';
      if (!sessions[s]) {
        sessions[s] = [];
        sessionOrder.push(s);
      }
      sessions[s].push(p);
    });

    var html = '<aside class="detail-sidebar" id="detail-sidebar">';
    sessionOrder.forEach(function (s) {
      html += '<div class="sidebar-session">';
      html += '<div class="sidebar-session-title">Session ' + escapeHtml(String(s)) + '</div>';
      sessions[s].forEach(function (p) {
        var cls = p.id === currentId ? ' active' : '';
        var label = p.id + ' ' + (p.title || '').substring(0, 30);
        html += '<a class="sidebar-item' + cls + '" href="#paper/' + escapeHtml(p.id) + '" title="' + escapeHtml(p.title || '') + '">';
        html += escapeHtml(label);
        html += '</a>';
      });
      html += '</div>';
    });
    html += '</aside>';
    return html;
  }

  function buildDetailNav(currentId) {
    var adj = getAdjacentPapers(currentId);
    var html = '<div class="detail-nav">';
    html += '<a class="back-link" href="#overview">\u2190 返回总览</a>';
    html += '<div class="paper-nav">';
    if (adj.prev) {
      html += '<a href="#paper/' + adj.prev + '">\u2190 上一篇 (' + escapeHtml(adj.prev) + ')</a>';
    } else {
      html += '<span class="disabled">\u2190 上一篇</span>';
    }
    html += '<span style="color:var(--text-muted)">|</span>';
    if (adj.next) {
      html += '<a href="#paper/' + adj.next + '">下一篇 (' + escapeHtml(adj.next) + ') \u2192</a>';
    } else {
      html += '<span class="disabled">下一篇 \u2192</span>';
    }
    html += '</div></div>';
    return html;
  }

  function buildAbstractSection(paper) {
    if (!paper.abstract) return '';
    var html = '<div class="abstract-section">';
    html += '<h2 class="section-heading">Abstract</h2>';
    html += '<p class="abstract-text">' + escapeHtml(paper.abstract) + '</p>';
    html += '</div>';
    return html;
  }

  function buildTitleAnnotation(paper) {
    if (!paper.title_annotation || !paper.title_annotation.segments || paper.title_annotation.segments.length === 0) {
      return '';
    }
    var segments = paper.title_annotation.segments;
    var html = '<h2 class="section-heading">说文解字</h2>';
    html += '<div class="title-annotated">';
    segments.forEach(function (seg) {
      var color = seg.color || 'var(--accent)';
      html += '<span class="segment" style="--seg-color:' + color + '">';
      html += '<span class="original">' + escapeHtml(seg.text) + '</span>';
      if (seg.meaning) {
        html += '<span class="annotation">' + escapeHtml(seg.meaning) + '</span>';
      }
      html += '</span>';
    });
    html += '</div>';
    return html;
  }

  function buildMetaCards(paper) {
    var metrics = paper.metrics || {};
    var md = paper.metrics_detailed || {};
    var hasDetailed = Object.keys(md).length > 0;

    // Affiliation card with enhancement
    var affilInfo = paper.affiliation_info || {};
    var affilHtml = '';
    if (affilInfo.logo) {
      affilHtml += '<img class="affil-logo" src="' + escapeHtml(window.APP.basePath + affilInfo.logo) + '" alt="" onerror="this.style.display=\'none\'" style="width:24px;height:24px;"> ';
    }
    affilHtml += escapeHtml(paper.affiliation || '');
    if (affilInfo.country_code) {
      affilHtml += ' ' + countryFlag(affilInfo.country_code);
    }
    if (affilInfo.type) {
      var typeLabels = { academia: '学界', industry: '业界', research_inst: '研究所' };
      var typeLabel = typeLabels[affilInfo.type] || affilInfo.type;
      affilHtml += ' <span class="affil-badge ' + escapeHtml(affilInfo.type) + '">' + escapeHtml(typeLabel) + '</span>';
    }

    if (hasDetailed) {
      return buildDetailedMetaCards(paper, md, affilHtml);
    }

    // Fallback: original simple cards
    var fields = [
      { label: 'Session', value: paper.session ? 'Session ' + paper.session : null },
      { label: '单位', rawHtml: affilHtml },
      { label: '工艺', value: metrics.technology || paper.process_node },
      { label: '面积', value: (metrics.die_area_mm2 || paper.die_area_mm2) ? (metrics.die_area_mm2 || paper.die_area_mm2) + ' mm\u00B2' : null, highlight: true },
      { label: '供电电压', value: metrics.supply_voltage || paper.supply_voltage },
      { label: 'SRAM', value: metrics.sram_kb },
      { label: '频率', value: metrics.frequency_mhz ? metrics.frequency_mhz + ' MHz' : (paper.frequency_mhz ? paper.frequency_mhz + ' MHz' : null) },
      { label: '功耗', value: (metrics.power_mw || paper.power_mw) ? (metrics.power_mw || paper.power_mw) + ' mW' : null },
      { label: '能效', value: metrics.energy_efficiency || paper.energy_efficiency, highlight: true },
      { label: '吞吐量', value: metrics.throughput },
      { label: '目标模型', value: metrics.target_model || paper.target_model },
      { label: '应用', value: paper.application }
    ];

    var html = '<div class="meta-grid">';
    fields.forEach(function (f) {
      if (!f.value && !f.rawHtml) return;
      var cls = f.highlight ? ' meta-card-highlight' : '';
      html += '<div class="meta-card' + cls + '">';
      html += '<div class="meta-label">' + escapeHtml(f.label) + '</div>';
      if (f.rawHtml) {
        html += '<div class="meta-value">' + f.rawHtml + '</div>';
      } else {
        html += '<div class="meta-value">' + escapeHtml(String(f.value)) + '</div>';
      }
      html += '</div>';
    });
    html += '</div>';
    return html;
  }

  function buildDetailedMetaCards(paper, md, affilHtml) {
    var metrics = paper.metrics || {};
    var html = '<div class="meta-grid">';

    // Session
    if (paper.session) {
      html += '<div class="meta-card">';
      html += '<div class="meta-label">SESSION</div>';
      html += '<div class="meta-value">' + escapeHtml('Session ' + paper.session) + '</div>';
      html += '</div>';
    }

    // Affiliation (enhanced)
    html += '<div class="meta-card">';
    html += '<div class="meta-label">单位</div>';
    html += '<div class="meta-value">' + affilHtml + '</div>';
    html += '</div>';

    // Simple fields from metrics_detailed
    var simpleFields = [
      { key: 'technology', label: '工艺', fallback: metrics.technology || paper.process_node },
      { key: 'die_area', label: '面积', fallback: (metrics.die_area_mm2 || paper.die_area_mm2) ? (metrics.die_area_mm2 || paper.die_area_mm2) + ' mm\u00B2' : null, highlight: true },
      { key: 'sram', label: 'SRAM', fallback: metrics.sram_kb },
      { key: 'quantization', label: '量化', fallback: null }
    ];

    simpleFields.forEach(function (sf) {
      var val = md[sf.key] || sf.fallback;
      if (!val) return;
      var cls = sf.highlight ? ' meta-card-highlight' : '';
      html += '<div class="meta-card' + cls + '">';
      html += '<div class="meta-label">' + escapeHtml(sf.label) + '</div>';
      html += '<div class="meta-value">' + escapeHtml(String(val)) + '</div>';
      html += '</div>';
    });

    // Multi-value fields
    var multiFields = [
      { key: 'supply_voltage', label: '供电电压', fallback: metrics.supply_voltage || paper.supply_voltage },
      { key: 'frequency', label: '频率', fallback: metrics.frequency_mhz ? metrics.frequency_mhz + ' MHz' : null },
      { key: 'power', label: '功耗', fallback: (metrics.power_mw || paper.power_mw) ? (metrics.power_mw || paper.power_mw) + ' mW' : null },
      { key: 'energy_efficiency', label: '能效', fallback: metrics.energy_efficiency || paper.energy_efficiency, highlight: true },
      { key: 'throughput', label: '吞吐量', fallback: metrics.throughput }
    ];

    multiFields.forEach(function (mf) {
      var field = md[mf.key];
      if (field && field.values && field.values.length > 0) {
        var cls = mf.highlight ? ' meta-card-highlight' : '';
        html += '<div class="meta-card' + cls + '">';
        html += '<div class="meta-label">' + escapeHtml(mf.label) + '</div>';
        html += '<div class="meta-multi-values">';
        field.values.forEach(function (v) {
          html += '<div>';
          html += '<span class="meta-multi-value">' + escapeHtml(String(v.value || '')) + '</span>';
          if (v.condition) {
            html += ' <span class="meta-condition">' + escapeHtml(v.condition) + '</span>';
          }
          html += '</div>';
        });
        html += '</div>';
        html += '</div>';
      } else if (mf.fallback) {
        var cls2 = mf.highlight ? ' meta-card-highlight' : '';
        html += '<div class="meta-card' + cls2 + '">';
        html += '<div class="meta-label">' + escapeHtml(mf.label) + '</div>';
        html += '<div class="meta-value">' + escapeHtml(String(mf.fallback)) + '</div>';
        html += '</div>';
      }
    });

    // Target model & Application
    var extraFields = [
      { label: '目标模型', value: metrics.target_model || paper.target_model },
      { label: '应用', value: paper.application }
    ];
    extraFields.forEach(function (ef) {
      if (!ef.value) return;
      html += '<div class="meta-card">';
      html += '<div class="meta-label">' + escapeHtml(ef.label) + '</div>';
      html += '<div class="meta-value">' + escapeHtml(String(ef.value)) + '</div>';
      html += '</div>';
    });

    // Comparison card
    if (md.comparison) {
      html += '<div class="meta-card meta-card-comparison">';
      html += '<div class="meta-label">COMPARISON</div>';
      html += '<div class="meta-value">' + escapeHtml(String(md.comparison)) + '</div>';
      html += '</div>';
    }

    html += '</div>';

    // Model benchmarks table
    if (md.model_benchmarks && md.model_benchmarks.length > 0) {
      html += '<table class="benchmarks-table">';
      html += '<thead><tr><th>Model</th><th>Metric</th><th>Detail</th></tr></thead>';
      html += '<tbody>';
      md.model_benchmarks.forEach(function (b) {
        html += '<tr>';
        html += '<td>' + escapeHtml(b.model || '') + '</td>';
        html += '<td>' + escapeHtml(b.metric || '') + '</td>';
        html += '<td>' + escapeHtml(b.detail || '') + '</td>';
        html += '</tr>';
      });
      html += '</tbody></table>';
    }

    return html;
  }

  function buildChallengeIdea(paper) {
    var challenges = paper.challenges || [];
    var ideas = paper.ideas || [];
    if (challenges.length === 0 && ideas.length === 0) return '';

    var html = '<h2 class="section-heading">挑战与创新思路</h2>';

    // Build paired rows for challenge-idea connections
    var maxLen = Math.max(challenges.length, ideas.length);

    html += '<div class="challenge-idea-section">';

    // Challenge column
    html += '<div class="challenge-column">';
    for (var i = 0; i < maxLen; i++) {
      if (i < challenges.length) {
        html += '<div class="challenge-card">';
        html += '<span class="card-index">C' + (i + 1) + '</span>';
        html += '<div class="card-text-zh">' + escapeHtml(challenges[i].text) + '</div>';
        if (challenges[i].text_en) {
          html += '<div class="card-text-en">' + escapeHtml(challenges[i].text_en) + '</div>';
        }
        html += '</div>';
      } else {
        html += '<div style="min-height:60px"></div>';
      }
    }
    html += '</div>';

    // Connector column
    html += '<div class="connector-column">';
    for (var j = 0; j < maxLen; j++) {
      if (j < challenges.length) {
        var targetIdx = challenges[j].related_idea_idx;
        var arrowLabel = typeof targetIdx === 'number' ? 'I' + (targetIdx + 1) : '';
        html += '<div class="connector-arrow" title="' + escapeHtml('C' + (j + 1) + ' \u2192 ' + arrowLabel) + '">\u2192</div>';
      } else {
        html += '<div class="connector-arrow">&nbsp;</div>';
      }
    }
    html += '</div>';

    // Idea column
    html += '<div class="idea-column">';
    for (var k = 0; k < maxLen; k++) {
      if (k < ideas.length) {
        var idea = ideas[k];
        var typeClass = getIdeaTypeClass(idea.type);
        html += '<div class="idea-card ' + typeClass + '">';
        html += '<span class="card-index">I' + (k + 1) + '</span>';
        html += '<div class="card-text-zh">' + escapeHtml(idea.text) + '</div>';
        if (idea.text_en) {
          html += '<div class="card-text-en">' + escapeHtml(idea.text_en) + '</div>';
        }
        html += '</div>';
      } else {
        html += '<div style="min-height:60px"></div>';
      }
    }
    html += '</div>';

    html += '</div>';
    return html;
  }

  function buildInnovations(paper) {
    var innovations = paper.innovations || [];
    if (innovations.length === 0) return '';

    var html = '<h2 class="section-heading">创新点</h2>';
    html += '<div class="innovations-grid">';
    innovations.forEach(function (inn) {
      var cls = getTypeClass(inn.type);
      html += '<span class="innovation-pill ' + cls + '">' + escapeHtml(inn.tag) + '</span>';
    });
    html += '</div>';
    return html;
  }

  function buildTags(paper) {
    var analyticalTags = paper.analytical_tags || [];
    var tags = paper.tags || [];
    if (analyticalTags.length === 0 && tags.length === 0) return '';

    var html = '<h2 class="section-heading">标签</h2>';

    // Analytical tags (colored pills)
    if (analyticalTags.length > 0) {
      html += '<div class="tags-grid" style="margin-bottom:8px;">';
      analyticalTags.forEach(function (tag) {
        html += '<span class="tag-pill tag-analytical">' + escapeHtml(tag) + '</span>';
      });
      html += '</div>';
    }

    // Original tags (grey pills)
    if (tags.length > 0) {
      html += '<div class="tags-grid">';
      tags.forEach(function (tag) {
        html += '<span class="tag-pill tag-neutral">' + escapeHtml(tag) + '</span>';
      });
      html += '</div>';
    }

    return html;
  }

  function resolveImagePath(path) {
    // Replace "images/" prefix with APP.imageDir for compressed/original switching
    if (path && window.APP.imageDir !== 'images' && path.indexOf('images/') === 0) {
      return path.replace('images/', window.APP.imageDir + '/');
    }
    return path;
  }

  function buildReaderContainer(paper) {
    var figures = paper.figures || [];
    var hasFigures = figures.some(function (f) { return f.path; });
    if (!hasFigures) return '';

    var html = '<div class="reader-container" id="reader-container">';

    // Mode buttons
    html += '<div class="reader-modes">';
    html += '<button class="reader-mode-btn active" data-mode="paired">图文</button>';
    html += '<button class="reader-mode-btn" data-mode="fulltext">全文</button>';
    html += '<button class="reader-mode-btn" data-mode="gallery">图片</button>';
    html += '</div>';

    // Reader content area
    html += '<div class="reader-content" id="reader-content"></div>';

    // Navigation (for paired mode)
    html += '<div class="reader-nav" id="reader-nav">';
    html += '<button class="reader-nav-btn" id="reader-prev">\u2190</button>';
    html += '<div class="reader-dots" id="reader-dots"></div>';
    html += '<button class="reader-nav-btn" id="reader-next">\u2192</button>';
    html += '</div>';

    html += '</div>';
    return html;
  }

  function initReader(paper) {
    var container = document.getElementById('reader-container');
    if (!container) return;

    var basePath = window.APP.basePath;
    var figures = (paper.figures || []).filter(function (f) { return f.path; });
    var currentSlide = 0;
    var currentMode = 'paired';

    // Build a figNum -> image path lookup
    var figPathMap = {};
    figures.forEach(function (fig) {
      figPathMap[fig.num] = basePath + resolveImagePath(fig.path);
    });

    var slides = [];
    var textSections = null;
    var dataLoaded = false;

    // Fetch text.json for structured content
    var textJsonUrl = basePath + 'data/' + paper.id + '/text.json';
    fetch(textJsonUrl)
      .then(function (res) {
        if (!res.ok) throw new Error('No text.json');
        return res.json();
      })
      .then(function (data) {
        textSections = data.sections || [];
        dataLoaded = true;

        // Build slides from body sections grouped by figure number
        var figGroups = {};
        var figOrder = [];
        textSections.forEach(function (sec) {
          if (sec.type === 'body' && sec.figure) {
            var fn = sec.figure;
            if (!figGroups[fn]) {
              figGroups[fn] = [];
              figOrder.push(fn);
            }
            figGroups[fn].push(sec.text);
          }
        });

        slides = figOrder.map(function (fn) {
          return {
            figNum: fn,
            imgSrc: figPathMap[fn] || '',
            label: 'Fig. ' + fn,
            text: figGroups[fn].join('\n\n')
          };
        });

        // Add figures that have no corresponding body sections
        figures.forEach(function (fig) {
          var hasSlide = slides.some(function (s) { return s.figNum === fig.num; });
          if (!hasSlide) {
            slides.push({
              figNum: fig.num,
              imgSrc: figPathMap[fig.num] || '',
              label: 'Fig. ' + fig.num,
              text: fig.caption || ''
            });
          }
        });

        // Sort by figure number
        slides.sort(function (a, b) { return a.figNum - b.figNum; });

        if (currentMode === 'paired') renderPairedMode();
      })
      .catch(function () {
        // Fallback: use figures with captions only
        dataLoaded = true;
        textSections = [];
        slides = figures.map(function (fig) {
          return {
            figNum: fig.num,
            imgSrc: figPathMap[fig.num] || '',
            label: 'Fig. ' + fig.num,
            text: fig.caption || ''
          };
        });
        if (currentMode === 'paired') renderPairedMode();
      });

    var contentEl = document.getElementById('reader-content');
    var navEl = document.getElementById('reader-nav');
    var dotsEl = document.getElementById('reader-dots');

    function renderPairedMode() {
      if (!dataLoaded) {
        contentEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div><div>加载论文内容...</div></div>';
        navEl.style.display = 'none';
        return;
      }
      if (slides.length === 0) {
        contentEl.innerHTML = '<div style="padding:20px;color:var(--text-muted);">暂无图文内容</div>';
        navEl.style.display = 'none';
        return;
      }
      navEl.style.display = 'flex';
      var s = slides[currentSlide];
      var html = '<div class="reader-slide">';
      html += '<div class="reader-figure">';
      if (s.imgSrc) {
        html += '<img src="' + escapeHtml(s.imgSrc) + '" alt="' + escapeHtml(s.label) + '" data-reader-img="true">';
      }
      html += '</div>';
      html += '<div class="reader-text">';
      if (s.label) {
        html += '<div class="reader-text-label">' + escapeHtml(s.label) + '</div>';
      }
      var paras = s.text.split('\n\n');
      paras.forEach(function (para) {
        if (para.trim()) {
          html += '<p class="reader-paragraph">' + escapeHtml(para.trim()) + '</p>';
        }
      });
      html += '</div>';
      html += '</div>';
      contentEl.innerHTML = html;

      // Render dots
      var dotsHtml = '';
      for (var i = 0; i < slides.length; i++) {
        var cls = i === currentSlide ? ' active' : '';
        dotsHtml += '<span class="reader-dot' + cls + '" data-slide="' + i + '"></span>';
      }
      dotsEl.innerHTML = dotsHtml;

      // Bind image click for lightbox
      var readerImg = contentEl.querySelector('[data-reader-img]');
      if (readerImg) {
        readerImg.addEventListener('click', function () {
          var allImgs = slides.map(function (sl) { return sl.imgSrc; });
          var allCaptions = slides.map(function (sl) { return sl.label; });
          window.openLightbox(allImgs, currentSlide, allCaptions);
        });
      }
    }

    function renderFulltextMode() {
      navEl.style.display = 'none';
      var ftEl = document.createElement('div');
      ftEl.className = 'reader-fulltext';
      ftEl.id = 'reader-fulltext';

      if (!dataLoaded) {
        ftEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div><div>加载全文...</div></div>';
        contentEl.innerHTML = '';
        contentEl.appendChild(ftEl);
        setTimeout(function () { renderFulltextMode(); }, 500);
        return;
      }

      // Use text.json body sections if available
      if (textSections && textSections.length > 0) {
        var html = '<div class="markdown-content">';
        textSections.forEach(function (sec) {
          if (sec.type === 'body') {
            html += '<p class="reader-paragraph">' + escapeHtml(sec.text) + '</p>';
          }
        });
        html += '</div>';
        ftEl.innerHTML = html;
        contentEl.innerHTML = '';
        contentEl.appendChild(ftEl);
        return;
      }

      // Fallback: load raw text.md (private mode only)
      if (paper.id) {
        ftEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div><div>加载全文...</div></div>';
        contentEl.innerHTML = '';
        contentEl.appendChild(ftEl);
        fetch(basePath + 'data/' + paper.id + '/text.md')
          .then(function (res) {
            if (!res.ok) throw new Error('Failed');
            return res.text();
          })
          .then(function (md) {
            if (typeof marked !== 'undefined' && marked.parse) {
              ftEl.innerHTML = '<div class="markdown-content">' + marked.parse(md) + '</div>';
            } else {
              ftEl.innerHTML = '<div class="markdown-content"><pre>' + escapeHtml(md) + '</pre></div>';
            }
          })
          .catch(function () {
            ftEl.innerHTML = '<div style="padding:20px;color:var(--text-muted);">全文内容加载失败</div>';
          });
        return;
      }

      ftEl.innerHTML = '<div style="padding:20px;color:var(--text-muted);">全文内容不可用</div>';
      contentEl.innerHTML = '';
      contentEl.appendChild(ftEl);
    }

    function renderGalleryMode() {
      navEl.style.display = 'none';
      var html = '<div class="reader-gallery">';
      figures.forEach(function (fig, idx) {
        var src = basePath + resolveImagePath(fig.path);
        html += '<div class="figure-card" data-reader-gallery-idx="' + idx + '">';
        html += '<img src="' + escapeHtml(src) + '" alt="Fig. ' + fig.num + '" loading="lazy">';
        html += '<div class="figure-label">Fig. ' + fig.num + '</div>';
        if (fig.caption) {
          html += '<div class="figure-caption">' + escapeHtml(fig.caption) + '</div>';
        }
        html += '</div>';
      });
      html += '</div>';
      contentEl.innerHTML = html;

      // Bind gallery lightbox
      contentEl.addEventListener('click', function (e) {
        var card = e.target.closest('[data-reader-gallery-idx]');
        if (card) {
          var idx = parseInt(card.dataset.readerGalleryIdx, 10);
          var allImgs = figures.map(function (f) { return basePath + resolveImagePath(f.path); });
          var allCaptions = figures.map(function (f) { return 'Fig. ' + f.num + ': ' + (f.caption || ''); });
          window.openLightbox(allImgs, idx, allCaptions);
        }
      });
    }

    function renderMode() {
      if (currentMode === 'paired') renderPairedMode();
      else if (currentMode === 'fulltext') renderFulltextMode();
      else if (currentMode === 'gallery') renderGalleryMode();
    }

    // Mode buttons
    var modeButtons = container.querySelectorAll('.reader-mode-btn');
    for (var i = 0; i < modeButtons.length; i++) {
      modeButtons[i].addEventListener('click', function () {
        for (var j = 0; j < modeButtons.length; j++) {
          modeButtons[j].classList.remove('active');
        }
        this.classList.add('active');
        currentMode = this.dataset.mode;
        renderMode();
      });
    }

    // Nav prev/next
    var prevBtn = document.getElementById('reader-prev');
    var nextBtn = document.getElementById('reader-next');
    if (prevBtn) {
      prevBtn.addEventListener('click', function () {
        if (slides.length === 0) return;
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        renderPairedMode();
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        if (slides.length === 0) return;
        currentSlide = (currentSlide + 1) % slides.length;
        renderPairedMode();
      });
    }

    // Dot navigation
    dotsEl.addEventListener('click', function (e) {
      var dot = e.target.closest('.reader-dot');
      if (dot) {
        currentSlide = parseInt(dot.dataset.slide, 10);
        renderPairedMode();
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', function (e) {
      var lightbox = document.getElementById('lightbox');
      if (lightbox && lightbox.classList.contains('active')) return;
      if (currentMode !== 'paired') return;
      if (!container || !document.body.contains(container)) return;
      if (e.key === 'ArrowLeft') {
        if (slides.length === 0) return;
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        renderPairedMode();
      } else if (e.key === 'ArrowRight') {
        if (slides.length === 0) return;
        currentSlide = (currentSlide + 1) % slides.length;
        renderPairedMode();
      }
    });

    // Initial render
    renderMode();
  }

  function buildImageGallery(paper) {
    var figures = paper.figures || [];
    if (figures.length === 0) return '';

    // Public mode: show placeholders + captions only (images are not deployed)
    var html = '<h2 class="section-heading">论文图表</h2>';
    html += '<div class="figure-gallery" id="image-gallery">';
    figures.forEach(function (fig, idx) {
      html += '<div class="figure-card" data-idx="' + idx + '" data-type="figure">';
      html += '<div class="figure-placeholder">Fig. ' + fig.num + '</div>';
      html += '<div class="figure-label">Fig. ' + fig.num + '</div>';
      if (fig.caption) {
        html += '<div class="figure-caption">' + escapeHtml(fig.caption) + '</div>';
      }
      html += '</div>';
    });
    html += '</div>';
    return html;
  }

  function buildBottomNav(currentId) {
    var adj = getAdjacentPapers(currentId);
    var html = '<div class="bottom-nav">';
    if (adj.prev) {
      html += '<a href="#paper/' + adj.prev + '">\u2190 ' + escapeHtml(adj.prev) + '</a>';
    } else {
      html += '<span class="disabled">\u2190</span>';
    }
    if (adj.next) {
      html += '<a href="#paper/' + adj.next + '">' + escapeHtml(adj.next) + ' \u2192</a>';
    } else {
      html += '<span class="disabled">\u2192</span>';
    }
    html += '</div>';
    return html;
  }

  function bindDetailEvents(paper) {
    var basePath = window.APP.basePath;
    var figures = paper.figures || [];
    var pageImages = (paper.page_images || paper.images || []).map(function (p) { return basePath + p; });

    // Figure gallery lightbox (individual figures with captions)
    var figGallery = document.getElementById('image-gallery');
    if (figGallery && figures.length > 0) {
      var figImages = figures.filter(function (f) { return f.path; }).map(function (f) { return basePath + resolveImagePath(f.path); });
      var figCaptions = figures.filter(function (f) { return f.path; }).map(function (f) {
        return 'Figure ' + paper.id + '.' + f.num + ': ' + (f.caption || '');
      });

      figGallery.addEventListener('click', function (e) {
        var card = e.target.closest('.figure-card');
        if (card) {
          var idx = parseInt(card.dataset.idx, 10);
          window.openLightbox(figImages, idx, figCaptions);
        }
      });
    }

    // Page gallery lightbox
    var pageGallery = document.getElementById('page-gallery');
    if (pageGallery && pageImages.length > 0) {
      pageGallery.addEventListener('click', function (e) {
        var thumb = e.target.closest('.gallery-thumb');
        if (thumb) {
          var idx = parseInt(thumb.dataset.idx, 10);
          var pageCaptions = pageImages.map(function (_, i) { return 'Page ' + (i + 1); });
          window.openLightbox(pageImages, idx, pageCaptions);
        }
      });
    }

    // Fallback: if no figures, use old image gallery
    if (figures.length === 0 && figGallery && pageImages.length > 0) {
      figGallery.addEventListener('click', function (e) {
        var thumb = e.target.closest('.gallery-thumb');
        if (thumb) {
          var idx = parseInt(thumb.dataset.idx, 10);
          window.openLightbox(pageImages, idx);
        }
      });
    }
  }

  window.renderDetail = function (container, id) {
    var paper = window.findPaper(id);

    if (!paper) {
      container.innerHTML = '<div class="detail-layout"><div class="detail-page">' +
        '<div class="detail-nav"><a class="back-link" href="#overview">\u2190 返回总览</a></div>' +
        '<div class="empty-state"><p>未找到论文: ' + escapeHtml(id) + '</p></div></div></div>';
      return;
    }

    var isPrivate = window.APP.privateMode === true;
    var html = '<div class="detail-layout">';
    html += buildSidebar(id);
    html += '<div class="detail-page">';

    html += buildDetailNav(id);

    // Title
    html += '<h1 class="detail-title">' + escapeHtml(paper.title || '') + '</h1>';
    if (paper.title_zh) {
      html += '<div class="detail-title-zh">' + escapeHtml(paper.title_zh) + '</div>';
    }

    // Abstract (always visible when available)
    html += buildAbstractSection(paper);

    // Title annotation
    html += buildTitleAnnotation(paper);

    // Meta cards
    html += buildMetaCards(paper);

    // Challenge <-> Idea
    html += buildChallengeIdea(paper);

    // Innovations
    html += buildInnovations(paper);

    // Tags
    html += buildTags(paper);

    if (isPrivate) {
      // Reader replaces both markdown-section and figure gallery
      html += buildReaderContainer(paper);
    } else {
      // Public: placeholders + captions only (no full text, no images)
      html += buildImageGallery(paper);
    }

    // Bottom nav
    html += buildBottomNav(id);

    html += '</div>'; // close .detail-page
    html += '</div>'; // close .detail-layout

    container.innerHTML = html;

    // Scroll active sidebar item into view
    var activeSidebarItem = document.querySelector('.sidebar-item.active');
    if (activeSidebarItem) {
      activeSidebarItem.scrollIntoView({ block: 'center', behavior: 'instant' });
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (isPrivate) {
      // Initialize reader
      initReader(paper);
    }

    // Bind events (for non-private gallery)
    bindDetailEvents(paper);
  };

})();
