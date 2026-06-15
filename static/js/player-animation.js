// ═══════════════════════════════════════════════════════════════
// EvaMusic — Player Pull-Up Animation Engine
// File: static/js/player-animation.js
// ═══════════════════════════════════════════════════════════════

(function () {
  'use strict';

  // ── State ────────────────────────────────────────────────────
  let _isOpen        = false;
  let _dragStartY    = 0;
  let _dragCurrentY  = 0;
  let _isDragging    = false;
  let _overlay       = null;
  let _sheet         = null;
  const SNAP_CLOSE   = 0.35;   // close if dragged down >35% of sheet height
  const VELOCITY_CLOSE = 0.8;  // px/ms threshold for fast flick-down

  // ── Public API ───────────────────────────────────────────────
  window.EvaAnim = {
    open:  openSheet,
    close: closeSheet,
    isOpen: () => _isOpen,
    init:  init
  };

  // ── Init — called once DOM is ready ─────────────────────────
  function init() {
    _injectStyles();
    _buildSheet();
    _bindSwipeOnBar();
    console.log('[EvaAnim] Pull-up animation engine ready');
  }

  // ── Inject CSS ───────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('__evaAnimStyles')) return;
    const s = document.createElement('style');
    s.id = '__evaAnimStyles';
    s.textContent = `
      /* ── Album art always square — never circular ── */
      #npAlbumArt {
        border-radius: 16px !important;
        animation: none !important;
      }

      /* ── Full-screen sheet wrapper ── */
      #evaPlayerSheet {
        position: fixed;
        inset: 0;
        z-index: 9998;
        display: none;
        pointer-events: none;
      }
      #evaPlayerSheet.ready { display: block; }

      /* Backdrop */
      #evaSheetBackdrop {
        position: absolute; inset: 0;
        background: rgba(0,0,0,0);
        transition: background 0.38s ease;
        pointer-events: none;
      }
      #evaPlayerSheet.open #evaSheetBackdrop {
        background: rgba(0,0,0,0.55);
        pointer-events: auto;
      }

      /* The sliding card */
      #evaSheetCard {
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 100%;
        border-radius: 20px 20px 0 0;
        overflow: hidden;
        transform: translateY(100%);
        transition: transform 0.42s cubic-bezier(0.22, 1, 0.36, 1);
        will-change: transform;
        pointer-events: auto;
        box-shadow: 0 -8px 48px rgba(0,0,0,0.6);
      }
      #evaPlayerSheet.open #evaSheetCard {
        transform: translateY(0);
      }
      #evaPlayerSheet.dragging #evaSheetCard {
        transition: none;
      }

      /* Drag handle at top of card */
      #evaSheetHandle {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 32px;
        display: flex; align-items: center; justify-content: center;
        cursor: grab; z-index: 2;
        -webkit-tap-highlight-color: transparent;
        touch-action: none;
      }
      #evaSheetHandle::after {
        content: '';
        width: 36px; height: 4px;
        border-radius: 2px;
        background: rgba(255,255,255,0.3);
      }
      #evaSheetHandle:active { cursor: grabbing; }

      /* Bounce on open */
      @keyframes evaSheetBounce {
        0%   { transform: translateY(0); }
        40%  { transform: translateY(-6px); }
        65%  { transform: translateY(2px); }
        80%  { transform: translateY(-2px); }
        100% { transform: translateY(0); }
      }
      #evaPlayerSheet.bounce #evaSheetCard {
        animation: evaSheetBounce 0.45s ease forwards;
      }

      /* Wave bars in music bar when playing */
      .eva-wave {
        display: inline-flex;
        align-items: flex-end;
        gap: 2px;
        height: 16px;
        margin-left: 6px;
        vertical-align: middle;
      }
      .eva-wave span {
        width: 3px;
        border-radius: 2px;
        background: var(--accent-color, #1DB954);
        display: inline-block;
      }
      .eva-wave.playing span:nth-child(1) { animation: evaWave 0.8s 0.0s ease-in-out infinite alternate; }
      .eva-wave.playing span:nth-child(2) { animation: evaWave 0.8s 0.2s ease-in-out infinite alternate; }
      .eva-wave.playing span:nth-child(3) { animation: evaWave 0.8s 0.4s ease-in-out infinite alternate; }
      .eva-wave span { height: 4px; }
      @keyframes evaWave {
        0%   { height: 4px; }
        100% { height: 14px; }
      }
    `;
    document.head.appendChild(s);
  }

  // ── Build the sheet wrapper (the actual player lives inside #evaPlayerOverlay) ──
  function _buildSheet() {
    if (document.getElementById('evaPlayerSheet')) return;

    const sheet = document.createElement('div');
    sheet.id = 'evaPlayerSheet';
    sheet.innerHTML = `
      <div id="evaSheetBackdrop"></div>
      <div id="evaSheetCard">
        <div id="evaSheetHandle"></div>
        <div id="evaSheetContent"></div>
      </div>
    `;
    document.body.appendChild(sheet);
    _sheet = sheet;

    // Backdrop tap → close
    sheet.querySelector('#evaSheetBackdrop').addEventListener('click', closeSheet);

    // Drag handle
    const handle = sheet.querySelector('#evaSheetHandle');
    handle.addEventListener('touchstart',  _onDragStart,  { passive: true });
    handle.addEventListener('touchmove',   _onDragMove,   { passive: false });
    handle.addEventListener('touchend',    _onDragEnd,    { passive: true });
    handle.addEventListener('mousedown',   _onDragStart);

    console.log('[EvaAnim] Sheet built');
  }

  // ── Swipe-up gesture on the mini bar itself ──────────────────
  function _bindSwipeOnBar() {
    let _barTouchStartY = 0;
    let _barTouchStartTime = 0;

    const attempt = () => {
      const bar = document.getElementById('musicBar');
      if (!bar) { setTimeout(attempt, 300); return; }

      bar.addEventListener('touchstart', (e) => {
        _barTouchStartY    = e.touches[0].clientY;
        _barTouchStartTime = Date.now();
      }, { passive: true });

      bar.addEventListener('touchend', (e) => {
        const dy       = _barTouchStartY - e.changedTouches[0].clientY;
        const dt       = Date.now() - _barTouchStartTime;
        const velocity = dy / dt; // px/ms, positive = swipe up
        if (dy > 30 || velocity > 0.4) {
          if (window.player && window.player.currentSong) openSheet();
        }
      }, { passive: true });
    };
    attempt();
  }

  // ── Open ─────────────────────────────────────────────────────
  function openSheet() {
    _ensureSheet();

    // Move the real overlay content into our sheet card
    const content = document.getElementById('evaSheetContent');
    let overlay   = document.getElementById('evaPlayerOverlay');

    // If player overlay doesn't exist yet, trigger its creation
    if (!overlay && window.player && window.player.currentSong) {
      if (typeof openPlayerOverlay === 'function') {
        openPlayerOverlay(window.player.currentSong);
        overlay = document.getElementById('evaPlayerOverlay');
      }
    }

    if (overlay && content) {
      // Re-parent overlay children into our sheet
      while (overlay.firstChild) content.appendChild(overlay.firstChild);
      overlay.style.display = 'none';
    }

    if (content) {
      content.style.cssText = 'height:100%;overflow:hidden;';
    }

    _sheet = document.getElementById('evaPlayerSheet');
    _sheet.classList.add('ready');
    document.body.style.overflow = 'hidden';

    // Trigger open animation on next frame
    requestAnimationFrame(() => {
      _sheet.classList.add('open');
      _isOpen = true;

      // Bounce after slide-in completes
      setTimeout(() => {
        _sheet.classList.add('bounce');
        setTimeout(() => _sheet.classList.remove('bounce'), 500);
      }, 380);
    });

    // Sync UI state in overlay
    if (window.player) {
      window.player._updateOverlayUI(window.player.currentSong);
      window.player._syncPlayIcons(window.player.isPlaying);
    }

    console.log('[EvaAnim] Sheet opened');
  }

  // ── Close ────────────────────────────────────────────────────
  function closeSheet() {
    _sheet = document.getElementById('evaPlayerSheet');
    if (!_sheet) return;

    _sheet.classList.remove('open', 'bounce', 'dragging');
    _isOpen = false;
    document.body.style.overflow = '';

    setTimeout(() => {
      if (!_isOpen) {
        _sheet.classList.remove('ready');

        // Move content back into the real overlay div (so player still works)
        const content = document.getElementById('evaSheetContent');
        let overlay   = document.getElementById('evaPlayerOverlay');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.id = 'evaPlayerOverlay';
          overlay.style.display = 'none';
          document.body.appendChild(overlay);
        }
        if (content) {
          while (content.firstChild) overlay.appendChild(content.firstChild);
        }
      }
    }, 420);

    console.log('[EvaAnim] Sheet closed');
  }

  // Hook into player play/pause to sync wave bars
  document.addEventListener('eva:playstate', (e) => {
    const wave = document.querySelector('.eva-wave');
    if (wave && window.player) wave.classList.toggle('playing', window.player.isPlaying);
  });

  // ── Drag gestures ────────────────────────────────────────────
  let _dragStartTime = 0;
  let _lastY = 0;

  function _onDragStart(e) {
    _isDragging    = true;
    _dragStartY    = e.touches ? e.touches[0].clientY : e.clientY;
    _dragStartTime = Date.now();
    _lastY         = _dragStartY;
    _sheet = document.getElementById('evaPlayerSheet');
    if (_sheet) _sheet.classList.add('dragging');
    if (e.type === 'mousedown') {
      document.addEventListener('mousemove', _onDragMove);
      document.addEventListener('mouseup',   _onDragEnd);
    }
  }

  function _onDragMove(e) {
    if (!_isDragging) return;
    const y   = e.touches ? e.touches[0].clientY : e.clientY;
    const dy  = y - _dragStartY;
    _lastY    = y;
    if (dy < 0) return; // don't allow dragging up
    const card = document.getElementById('evaSheetCard');
    if (card) card.style.transform = `translateY(${dy}px)`;
    if (e.cancelable) e.preventDefault();
  }

  function _onDragEnd(e) {
    if (!_isDragging) return;
    _isDragging = false;

    const y        = e.changedTouches ? e.changedTouches[0].clientY : e.clientY;
    const dy       = y - _dragStartY;
    const dt       = Date.now() - _dragStartTime;
    const velocity = dy / dt; // px/ms positive = dragging down

    _sheet = document.getElementById('evaPlayerSheet');
    if (_sheet) _sheet.classList.remove('dragging');

    const card = document.getElementById('evaSheetCard');
    const sh   = card ? card.offsetHeight : window.innerHeight;

    if (velocity > VELOCITY_CLOSE || dy / sh > SNAP_CLOSE) {
      // Flick or drag past threshold → close
      if (card) {
        card.style.transition = 'transform 0.3s cubic-bezier(0.22,1,0.36,1)';
        card.style.transform  = `translateY(100%)`;
        setTimeout(() => { card.style.transform = ''; card.style.transition = ''; closeSheet(); }, 300);
      } else {
        closeSheet();
      }
    } else {
      // Snap back open
      if (card) { card.style.transform = ''; }
    }

    document.removeEventListener('mousemove', _onDragMove);
    document.removeEventListener('mouseup',   _onDragEnd);
  }

  // ── Ensure sheet exists ──────────────────────────────────────
  function _ensureSheet() {
    if (!document.getElementById('evaPlayerSheet')) _buildSheet();
  }

  // ── Wire closePlayerOverlay to our close ─────────────────────
  window.closePlayerOverlay = closeSheet;

  // ── Override expandPlayer to use our sheet ───────────────────
  window.expandPlayer = function(e) {
    if (e) e.stopPropagation();
    if (window.player && window.player.currentSong) openSheet();
  };

  // ── Boot when DOM is ready ───────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // Small delay so pullup-player.js initializes first
    setTimeout(init, 50);
  }

})();
      
