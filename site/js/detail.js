/* =============================================
   detail.js - Detail Page
   ============================================= */

(function () {
  'use strict';

  function getAdjacentPapers(currentId) {
    var ids = window.getPaperIds();
    var idx = ids.indexOf(currentId);
    return {
      prev: idx > 0 ? ids[idx - 1] : null,
      next: idx < ids.length - 1 ? ids[idx + 1] : null
    };
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
    var fields = [
      { label: 'Session', value: paper.session ? 'Session ' + paper.session : null },
      { label: '单位', value: paper.affiliation },
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
      if (!f.value) return;
      var cls = f.highlight ? ' meta-card-highlight' : '';
      html += '<div class="meta-card' + cls + '">';
      html += '<div class="meta-label">' + escapeHtml(f.label) + '</div>';
      html += '<div class="meta-value">' + escapeHtml(String(f.value)) + '</div>';
      html += '</div>';
    });
    html += '</div>';
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
        html += escapeHtml(challenges[i].text);
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
        html += escapeHtml(idea.text);
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
    var tags = paper.tags || [];
    if (tags.length === 0) return '';

    var html = '<h2 class="section-heading">标签</h2>';
    html += '<div class="tags-grid">';
    tags.forEach(function (tag) {
      html += '<span class="tag-pill tag-neutral">' + escapeHtml(tag) + '</span>';
    });
    html += '</div>';
    return html;
  }

  function resolveImagePath(path) {
    // Replace "images/" prefix with APP.imageDir for compressed/original switching
    if (path && window.APP.imageDir !== 'images' && path.indexOf('images/') === 0) {
      return path.replace('images/', window.APP.imageDir + '/');
    }
    return path;
  }

  function buildImageGallery(paper) {
    var basePath = window.APP.basePath;
    var figures = paper.figures || [];
    var pageImages = paper.page_images || paper.images || [];

    // If we have individual figures, show those with captions
    if (figures.length > 0) {
      var hasPaths = figures.some(function (f) { return f.path; });
      var html = '<h2 class="section-heading">论文图表</h2>';
      html += '<div class="figure-gallery" id="image-gallery">';
      figures.forEach(function (fig, idx) {
        if (hasPaths && !fig.path) return;
        html += '<div class="figure-card" data-idx="' + idx + '" data-type="figure">';
        if (fig.path) {
          var src = basePath + resolveImagePath(fig.path);
          html += '<img src="' + escapeHtml(src) + '" alt="Fig. ' + fig.num + '" loading="lazy">';
        } else {
          html += '<div class="figure-placeholder">Fig. ' + fig.num + '</div>';
        }
        html += '<div class="figure-label">Fig. ' + fig.num + '</div>';
        if (fig.caption) {
          html += '<div class="figure-caption">' + escapeHtml(fig.caption) + '</div>';
        }
        html += '</div>';
      });
      html += '</div>';

      // Also show page images in a collapsible section
      if (pageImages.length > 0) {
        html += '<h2 class="section-heading">论文页面</h2>';
        html += '<div class="image-gallery" id="page-gallery">';
        pageImages.forEach(function (imgPath, idx) {
          var src = basePath + imgPath;
          html += '<div class="gallery-thumb" data-idx="' + idx + '" data-type="page">';
          html += '<img src="' + escapeHtml(src) + '" alt="Page ' + (idx + 1) + '" loading="lazy">';
          html += '</div>';
        });
        html += '</div>';
      }

      return html;
    }

    // Fallback: show page images only (original behavior)
    if (pageImages.length === 0) return '';

    var html = '<h2 class="section-heading">论文页面</h2>';
    html += '<div class="image-gallery" id="image-gallery">';
    pageImages.forEach(function (imgPath, idx) {
      var src = basePath + imgPath;
      html += '<div class="gallery-thumb" data-idx="' + idx + '">';
      html += '<img src="' + escapeHtml(src) + '" alt="Page ' + (idx + 1) + '" loading="lazy">';
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

  function loadMarkdownContent(paper, container) {
    if (!paper.markdown_path) return;

    var mdEl = document.getElementById('markdown-section');
    if (!mdEl) return;

    var basePath = window.APP.basePath;
    var url = basePath + paper.markdown_path;

    mdEl.innerHTML = '<div class="loading"><div class="loading-spinner"></div><div>加载详细内容...</div></div>';

    fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error('Failed to load markdown');
        return res.text();
      })
      .then(function (md) {
        if (typeof marked !== 'undefined' && marked.parse) {
          mdEl.innerHTML = '<div class="markdown-content">' + marked.parse(md) + '</div>';
        } else {
          mdEl.innerHTML = '<div class="markdown-content"><pre>' + escapeHtml(md) + '</pre></div>';
        }
      })
      .catch(function () {
        mdEl.innerHTML = '';
      });
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
      container.innerHTML = '<div class="detail-page">' +
        '<div class="detail-nav"><a class="back-link" href="#overview">\u2190 返回总览</a></div>' +
        '<div class="empty-state"><p>未找到论文: ' + escapeHtml(id) + '</p></div></div>';
      return;
    }

    var html = '<div class="detail-page">';

    html += buildDetailNav(id);

    // Title
    html += '<h1 class="detail-title">' + escapeHtml(paper.title || '') + '</h1>';
    if (paper.title_zh) {
      html += '<div class="detail-title-zh">' + escapeHtml(paper.title_zh) + '</div>';
    }

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

    // Markdown content placeholder
    html += '<div id="markdown-section"></div>';

    // Image gallery
    html += buildImageGallery(paper);

    // Bottom nav
    html += buildBottomNav(id);

    html += '</div>';

    container.innerHTML = html;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Load markdown async
    loadMarkdownContent(paper, container);

    // Bind events
    bindDetailEvents(paper);
  };

})();
