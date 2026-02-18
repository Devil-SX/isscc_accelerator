/* =============================================
   overview.js - Overview Page
   ============================================= */

(function () {
  'use strict';

  var sessionList = [
    { key: 'all', label: 'All' },
    { key: '2', label: 'Session 2' },
    { key: '10', label: 'Session 10' },
    { key: '18', label: 'Session 18' },
    { key: '30', label: 'Session 30' },
    { key: '31', label: 'Session 31' }
  ];

  var columnDefs = [
    { key: 'id', label: '#', sortable: true },
    { key: 'title', label: '标题', sortable: true },
    { key: 'affiliation', label: '单位', sortable: true },
    { key: 'process_node', label: '工艺', sortable: true },
    { key: 'die_area_mm2', label: '面积', sortable: true },
    { key: 'power_mw', label: '功耗', sortable: true },
    { key: 'energy_efficiency', label: '能效', sortable: false },
    { key: 'target_model', label: '目标模型', sortable: true },
    { key: 'innovations', label: '创新点', sortable: false }
  ];

  // Session color palette for stats bar
  var sessionColors = {
    '2': '#58a6ff',
    '10': '#e74c3c',
    '18': '#2ecc71',
    '30': '#e67e22',
    '31': '#9b59b6'
  };

  function getMetricValue(paper, key) {
    // Try metrics object first, then top-level
    var m = paper.metrics || {};
    if (key === 'process_node') return m.technology || paper.process_node;
    if (key === 'die_area_mm2') return m.die_area_mm2 || paper.die_area_mm2;
    if (key === 'power_mw') return m.power_mw || paper.power_mw;
    if (key === 'energy_efficiency') return m.energy_efficiency || paper.energy_efficiency;
    return paper[key];
  }

  function formatPowerShort(val) {
    if (!val) return '-';
    var num = parseFloat(val);
    if (isNaN(num)) return String(val);
    if (num >= 1000000) return (num / 1000000).toFixed(1) + ' W';
    if (num >= 1000) return (num / 1000).toFixed(1) + ' W';
    return num + ' mW';
  }

  function countryFlag(code) {
    if (!code) return '';
    return String.fromCodePoint.apply(null, code.toUpperCase().split('').map(function (c) { return c.charCodeAt(0) + 127397; }));
  }

  function applyFilters() {
    var papers = window.APP.papers;
    var s = window.APP.currentSession;
    var f = window.APP.filters;

    var result = papers.filter(function (p) {
      if (s !== 'all' && String(p.session) !== s) return false;

      if (f.process && p.process_node !== f.process) return false;

      if (f.application && p.application !== f.application) return false;

      if (f.innovationType) {
        var hasType = (p.innovations || []).some(function (inn) {
          return inn.type === f.innovationType;
        });
        if (!hasType) return false;
      }

      if (f.analyticalTags && f.analyticalTags.length > 0) {
        var paperTags = p.analytical_tags || [];
        var allMatch = f.analyticalTags.every(function (tag) {
          return paperTags.indexOf(tag) !== -1;
        });
        if (!allMatch) return false;
      }

      if (f.search) {
        var q = f.search.toLowerCase();
        var haystack = [
          p.title, p.title_zh, p.affiliation,
          (p.tags || []).join(' ')
        ].join(' ').toLowerCase();
        if (haystack.indexOf(q) === -1) return false;
      }

      return true;
    });

    // Sort
    if (window.APP.sortCol) {
      var col = window.APP.sortCol;
      var asc = window.APP.sortAsc;
      result.sort(function (a, b) {
        var va = getSortValue(a, col);
        var vb = getSortValue(b, col);
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
      });
    }

    window.APP.filteredPapers = result;
  }

  function getSortValue(paper, col) {
    switch (col) {
      case 'id':
        return parseFloat(paper.id) || 0;
      case 'title':
        return (paper.title || '').toLowerCase();
      case 'affiliation':
        return (paper.affiliation || '').toLowerCase();
      case 'process_node':
        return parseFloat(paper.process_node) || 999;
      case 'die_area_mm2':
        return parseFloat(getMetricValue(paper, 'die_area_mm2')) || 999;
      case 'power_mw':
        return parseFloat(getMetricValue(paper, 'power_mw')) || 999999;
      case 'target_model':
        return (paper.target_model || '').toLowerCase();
      default:
        return (paper[col] || '').toString().toLowerCase();
    }
  }

  function extractUniqueValues(papers, key) {
    var seen = {};
    var result = [];
    papers.forEach(function (p) {
      var v = p[key];
      if (v && !seen[v]) {
        seen[v] = true;
        result.push(v);
      }
    });
    return result.sort();
  }

  function extractInnovationTypes(papers) {
    var seen = {};
    var result = [];
    papers.forEach(function (p) {
      (p.innovations || []).forEach(function (inn) {
        if (inn.type && !seen[inn.type]) {
          seen[inn.type] = true;
          result.push(inn.type);
        }
      });
    });
    return result.sort();
  }

  function buildStatsBar(papers) {
    // Process node distribution
    var nodeCounts = {};
    papers.forEach(function (p) {
      var node = p.process_node || 'N/A';
      nodeCounts[node] = (nodeCounts[node] || 0) + 1;
    });
    var nodeEntries = Object.keys(nodeCounts).map(function (k) {
      return { label: k, count: nodeCounts[k] };
    }).sort(function (a, b) {
      return (parseFloat(a.label) || 999) - (parseFloat(b.label) || 999);
    });
    var maxNodeCount = Math.max.apply(null, nodeEntries.map(function (e) { return e.count; }));

    // Session distribution
    var sessCounts = {};
    papers.forEach(function (p) {
      var s = String(p.session);
      sessCounts[s] = (sessCounts[s] || 0) + 1;
    });
    var sessEntries = Object.keys(sessCounts).map(function (k) {
      return { label: 'S' + k, session: k, count: sessCounts[k] };
    }).sort(function (a, b) {
      return parseInt(a.session) - parseInt(b.session);
    });
    var maxSessCount = Math.max.apply(null, sessEntries.map(function (e) { return e.count; }));

    var nodeBarColors = ['#58a6ff', '#3498db', '#2ecc71', '#e67e22', '#e74c3c', '#9b59b6', '#f1c40f', '#1abc9c'];

    var html = '<div class="stats-bar">';

    // Process node stat card
    html += '<div class="stat-card"><h3>工艺节点分布</h3>';
    nodeEntries.forEach(function (e, i) {
      var pct = maxNodeCount > 0 ? (e.count / maxNodeCount * 100) : 0;
      var color = nodeBarColors[i % nodeBarColors.length];
      html += '<div class="stat-bar-row">' +
        '<span class="stat-bar-label">' + escapeHtml(e.label) + '</span>' +
        '<div class="stat-bar-track"><div class="stat-bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
        '<span class="stat-bar-value">' + e.count + '</span>' +
        '</div>';
    });
    html += '</div>';

    // Session stat card
    html += '<div class="stat-card"><h3>Session 分布</h3>';
    sessEntries.forEach(function (e) {
      var pct = maxSessCount > 0 ? (e.count / maxSessCount * 100) : 0;
      var color = sessionColors[e.session] || '#58a6ff';
      html += '<div class="stat-bar-row">' +
        '<span class="stat-bar-label">' + escapeHtml(e.label) + '</span>' +
        '<div class="stat-bar-track"><div class="stat-bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
        '<span class="stat-bar-value">' + e.count + '</span>' +
        '</div>';
    });
    html += '</div>';

    // Academia/Industry pie chart
    var typeCounts = {};
    papers.forEach(function (p) {
      var info = p.affiliation_info;
      var t = (info && info.type) ? info.type : 'unknown';
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });
    var typeColors = { academia: '#58a6ff', industry: '#e74c3c', research_inst: '#2ecc71', unknown: '#6e7681' };
    var typeLabels = { academia: '学界', industry: '业界', research_inst: '研究所', unknown: '未知' };
    var typeEntries = Object.keys(typeCounts).map(function (k) {
      return { key: k, count: typeCounts[k], color: typeColors[k] || '#6e7681', label: typeLabels[k] || k };
    }).sort(function (a, b) { return b.count - a.count; });
    var typeTotal = typeEntries.reduce(function (s, e) { return s + e.count; }, 0);

    html += '<div class="stat-card"><h3>学界 / 业界分布</h3>';
    html += '<div class="pie-chart-container">';
    html += buildDonutSVG(typeEntries, typeTotal);
    html += '<div class="pie-legend">';
    typeEntries.forEach(function (e) {
      html += '<div class="pie-legend-item">';
      html += '<span class="pie-legend-dot" style="background:' + e.color + '"></span>';
      html += '<span>' + escapeHtml(e.label) + '</span>';
      html += '<span class="pie-legend-count">' + e.count + '</span>';
      html += '</div>';
    });
    html += '</div></div></div>';

    // Country distribution pie chart
    var countryCounts = {};
    papers.forEach(function (p) {
      var info = p.affiliation_info;
      var c = (info && info.country) ? info.country : 'Unknown';
      countryCounts[c] = (countryCounts[c] || 0) + 1;
    });
    var countryColors = ['#58a6ff', '#e74c3c', '#2ecc71', '#e67e22', '#9b59b6', '#f1c40f', '#1abc9c', '#3498db', '#e91e63', '#00bcd4', '#ff9800', '#8bc34a'];
    var countryEntries = Object.keys(countryCounts).map(function (k) {
      return { key: k, count: countryCounts[k], label: k };
    }).sort(function (a, b) { return b.count - a.count; });
    countryEntries.forEach(function (e, i) { e.color = countryColors[i % countryColors.length]; });
    var countryTotal = countryEntries.reduce(function (s, e) { return s + e.count; }, 0);

    html += '<div class="stat-card"><h3>国家/地区分布</h3>';
    html += '<div class="pie-chart-container">';
    html += buildDonutSVG(countryEntries, countryTotal);
    html += '<div class="pie-legend">';
    countryEntries.forEach(function (e) {
      html += '<div class="pie-legend-item">';
      html += '<span class="pie-legend-dot" style="background:' + e.color + '"></span>';
      html += '<span>' + escapeHtml(e.label) + '</span>';
      html += '<span class="pie-legend-count">' + e.count + '</span>';
      html += '</div>';
    });
    html += '</div></div></div>';

    html += '</div>';
    return html;
  }

  function buildDonutSVG(entries, total) {
    var r = 42;
    var circumference = 2 * Math.PI * r; // ~263.89
    var svg = '<svg viewBox="0 0 120 120" class="pie-chart">';
    var offset = 0;
    entries.forEach(function (e) {
      var segLen = (e.count / total) * circumference;
      svg += '<circle cx="60" cy="60" r="' + r + '" fill="none" stroke="' + e.color + '" stroke-width="28"' +
        ' stroke-dasharray="' + segLen.toFixed(2) + ' ' + circumference.toFixed(2) + '"' +
        ' stroke-dashoffset="' + (-offset).toFixed(2) + '"' +
        ' transform="rotate(-90 60 60)" />';
      offset += segLen;
    });
    svg += '</svg>';
    return svg;
  }

  function buildSessionTabs() {
    var html = '<div class="session-tabs" id="session-tabs">';
    sessionList.forEach(function (s) {
      var cls = s.key === window.APP.currentSession ? ' active' : '';
      html += '<div class="session-tab' + cls + '" data-session="' + s.key + '">' + s.label + '</div>';
    });
    html += '</div>';
    return html;
  }

  function buildFilterPanel(papers) {
    var processes = extractUniqueValues(papers, 'process_node');
    var applications = extractUniqueValues(papers, 'application');
    var innovTypes = extractInnovationTypes(papers);

    var html = '<div class="filter-panel" id="filter-panel">';

    // Process dropdown
    html += '<select id="filter-process"><option value="">全部工艺</option>';
    processes.forEach(function (v) {
      var sel = window.APP.filters.process === v ? ' selected' : '';
      html += '<option value="' + escapeHtml(v) + '"' + sel + '>' + escapeHtml(v) + '</option>';
    });
    html += '</select>';

    // Application dropdown
    html += '<select id="filter-application"><option value="">全部应用</option>';
    applications.forEach(function (v) {
      var sel = window.APP.filters.application === v ? ' selected' : '';
      html += '<option value="' + escapeHtml(v) + '"' + sel + '>' + escapeHtml(v) + '</option>';
    });
    html += '</select>';

    // Innovation type dropdown
    html += '<select id="filter-innovation"><option value="">全部创新类型</option>';
    innovTypes.forEach(function (v) {
      var sel = window.APP.filters.innovationType === v ? ' selected' : '';
      html += '<option value="' + escapeHtml(v) + '"' + sel + '>' + escapeHtml(v) + '</option>';
    });
    html += '</select>';

    // Search
    html += '<input type="text" id="filter-search" placeholder="搜索标题、标签、单位..." value="' +
      escapeHtml(window.APP.filters.search) + '">';

    // Paper count
    html += '<span class="paper-count" id="paper-count"></span>';

    html += '</div>';
    return html;
  }

  function buildAnalyticalTagsFilter(papers) {
    var seen = {};
    var allTags = [];
    papers.forEach(function (p) {
      (p.analytical_tags || []).forEach(function (tag) {
        if (!seen[tag]) {
          seen[tag] = true;
          allTags.push(tag);
        }
      });
    });
    allTags.sort();

    var selected = window.APP.filters.analyticalTags || [];
    var html = '<div class="analytical-tags-filter" id="analytical-tags-filter">';
    allTags.forEach(function (tag) {
      var isActive = selected.indexOf(tag) !== -1;
      var cls = isActive ? ' active' : '';
      html += '<button class="analytical-tag-btn' + cls + '" data-tag="' + escapeHtml(tag) + '">' + escapeHtml(tag) + '</button>';
    });
    html += '</div>';
    return html;
  }

  function buildTable(papers) {
    var html = '<div class="table-wrapper"><div class="comp-table" id="comp-table">';

    // Header
    columnDefs.forEach(function (col) {
      var arrow = '';
      if (col.sortable) {
        var isActive = window.APP.sortCol === col.key;
        var arrowChar = isActive ? (window.APP.sortAsc ? '\u25B2' : '\u25BC') : '\u25B2';
        var activeClass = isActive ? ' active' : '';
        arrow = ' <span class="sort-arrow' + activeClass + '">' + arrowChar + '</span>';
      }
      html += '<div class="th" data-col="' + col.key + '" data-sortable="' + col.sortable + '">' +
        col.label + arrow + '</div>';
    });

    // Rows
    papers.forEach(function (p) {
      html += '<div class="row" data-id="' + escapeHtml(p.id) + '">';

      // #
      html += '<div class="td">' + escapeHtml(p.id) + '</div>';

      // Title
      html += '<div class="td title-cell">';
      html += '<span class="paper-title">' + escapeHtml(p.title || '') + '</span>';
      if (p.title_zh) {
        html += '<span class="paper-title-zh">' + escapeHtml(p.title_zh) + '</span>';
      }
      html += '</div>';

      // Affiliation
      var affilInfo = p.affiliation_info || {};
      var affilHtml = '';
      if (affilInfo.logo) {
        affilHtml += '<img class="affil-logo" src="' + escapeHtml(window.APP.basePath + affilInfo.logo) + '" alt="" onerror="this.style.display=\'none\'">';
      }
      affilHtml += escapeHtml(p.affiliation || '-');
      if (affilInfo.country_code) {
        affilHtml += ' ' + countryFlag(affilInfo.country_code);
      }
      html += '<div class="td">' + affilHtml + '</div>';

      // Process
      html += '<div class="td">' + escapeHtml(getMetricValue(p, 'process_node') || '-') + '</div>';

      // Area
      var area = getMetricValue(p, 'die_area_mm2');
      html += '<div class="td">' + escapeHtml(area ? area + ' mm\u00B2' : '-') + '</div>';

      // Power (new column)
      var power = getMetricValue(p, 'power_mw');
      html += '<div class="td">' + escapeHtml(formatPowerShort(power)) + '</div>';

      // Efficiency
      html += '<div class="td">' + escapeHtml(getMetricValue(p, 'energy_efficiency') || '-') + '</div>';

      // Target model
      html += '<div class="td">' + escapeHtml(p.target_model || '-') + '</div>';

      // Innovations with tooltip
      html += '<div class="td tags-cell">';
      (p.innovations || []).forEach(function (inn) {
        var cls = getTypeClass(inn.type);
        html += '<span class="tag-pill ' + cls + '" title="' + escapeHtml(inn.tag) + '">' + escapeHtml(inn.tag) + '</span>';
      });
      html += '</div>';

      html += '</div>';
    });

    html += '</div></div>';
    return html;
  }

  function updatePaperCount() {
    var el = document.getElementById('paper-count');
    if (el) {
      el.textContent = '显示 ' + window.APP.filteredPapers.length + ' / ' + window.APP.papers.length + ' 篇论文';
    }
  }

  function bindOverviewEvents() {
    // Session tabs
    var tabsEl = document.getElementById('session-tabs');
    if (tabsEl) {
      tabsEl.addEventListener('click', function (e) {
        var tab = e.target.closest('.session-tab');
        if (!tab) return;
        window.APP.currentSession = tab.dataset.session;
        rerender();
      });
    }

    // Filters
    var filterProcess = document.getElementById('filter-process');
    var filterApp = document.getElementById('filter-application');
    var filterInnov = document.getElementById('filter-innovation');
    var filterSearch = document.getElementById('filter-search');

    if (filterProcess) {
      filterProcess.addEventListener('change', function () {
        window.APP.filters.process = this.value;
        rerender();
      });
    }
    if (filterApp) {
      filterApp.addEventListener('change', function () {
        window.APP.filters.application = this.value;
        rerender();
      });
    }
    if (filterInnov) {
      filterInnov.addEventListener('change', function () {
        window.APP.filters.innovationType = this.value;
        rerender();
      });
    }
    if (filterSearch) {
      var searchTimeout;
      filterSearch.addEventListener('input', function () {
        var val = this.value;
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
          window.APP.filters.search = val;
          rerender();
        }, 200);
      });
    }

    // Analytical tags filter
    var tagsFilter = document.getElementById('analytical-tags-filter');
    if (tagsFilter) {
      tagsFilter.addEventListener('click', function (e) {
        var btn = e.target.closest('.analytical-tag-btn');
        if (!btn) return;
        var tag = btn.dataset.tag;
        var tags = window.APP.filters.analyticalTags || [];
        var idx = tags.indexOf(tag);
        if (idx === -1) {
          tags.push(tag);
        } else {
          tags.splice(idx, 1);
        }
        window.APP.filters.analyticalTags = tags;
        rerender();
      });
    }

    // Table header sort
    var table = document.getElementById('comp-table');
    if (table) {
      table.addEventListener('click', function (e) {
        var th = e.target.closest('.th');
        if (th && th.dataset.sortable === 'true') {
          var col = th.dataset.col;
          if (window.APP.sortCol === col) {
            window.APP.sortAsc = !window.APP.sortAsc;
          } else {
            window.APP.sortCol = col;
            window.APP.sortAsc = true;
          }
          rerender();
          return;
        }

        var row = e.target.closest('.row');
        if (row) {
          window.location.hash = '#paper/' + row.dataset.id;
        }
      });
    }
  }

  function rerender() {
    var app = document.getElementById('app');
    window.renderOverview(app);
  }

  window.renderOverview = function (container) {
    applyFilters();
    var papers = window.APP.filteredPapers;

    var html = '';
    html += buildSessionTabs();
    html += buildFilterPanel(window.APP.papers);
    html += buildAnalyticalTagsFilter(window.APP.papers);
    html += buildStatsBar(window.APP.papers);
    html += buildTable(papers);

    container.innerHTML = html;

    updatePaperCount();
    bindOverviewEvents();
  };

})();
