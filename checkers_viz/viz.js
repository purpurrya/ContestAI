(function () {
  'use strict';
  // сетка и подписи id клеток на доске
  var gridStep = 10;
  var canvas = null;
  var ctx = null;
  var GRID_W = 960;
  var GRID_H = 840;

  var CELLS = (typeof window !== 'undefined' && window.CELLS) ? window.CELLS : (function () {
    var arr = [];
    for (var i = 0; i < 96; i++) {
      arr.push({
        id: i,
        corners: [
          { x: 0, y: 0 },
          { x: 0, y: 0 },
          { x: 0, y: 0 },
          { x: 0, y: 0 }
        ]
      });
    }
    return arr;
  })();

  var Board = (typeof window !== 'undefined' && window.Board) ? window.Board : null;

  function getCellCenter(cell) {
    if (Board && Board.getCellCenter) return Board.getCellCenter(cell);
    var c = cell.corners;
    return {
      x: (c[0].x + c[1].x + c[2].x + c[3].x) / 4,
      y: (c[0].y + c[1].y + c[2].y + c[3].y) / 4
    };
  }

  function isCellDefined(cell) {
    if (Board && Board.isCellDefined) return Board.isCellDefined(cell);
    if (!cell || !cell.corners || cell.corners.length < 4) return false;
    var c = cell.corners;
    var sum = 0;
    for (var i = 0; i < 4; i++) sum += c[i].x + c[i].y;
    return sum !== 0;
  }

  function drawCellIds() {
    var c = getCtx();
    if (!c || !CELLS.length) return;
    c.font = '11px sans-serif';
    c.textAlign = 'center';
    c.textBaseline = 'middle';
    for (var i = 0; i < CELLS.length; i++) {
      var cell = CELLS[i];
      if (!isCellDefined(cell)) continue;
      var center = getCellCenter(cell);
      if (!center) continue;
      c.fillStyle = 'rgba(0, 0, 0, 0.75)';
      c.strokeStyle = 'rgba(255, 255, 255, 0.9)';
      c.lineWidth = 2;
      c.strokeText(String(cell.id), center.x, center.y);
      c.fillText(String(cell.id), center.x, center.y);
    }
  }

  function getGridCanvas() {
    if (!canvas) canvas = document.getElementById('grid');
    return canvas;
  }

  function getCtx() {
    if (!ctx) ctx = getGridCanvas() && getGridCanvas().getContext('2d');
    return ctx;
  }

  function resizeGrid() {
    var el = getGridCanvas();
    if (!el) return;
    if (el.width !== GRID_W || el.height !== GRID_H) {
      el.width = GRID_W;
      el.height = GRID_H;
      drawGrid();
    }
  }

  function drawGrid() {
    var el = getGridCanvas();
    var c = getCtx();
    if (!el || !c) return;

    var w = el.width;
    var h = el.height;

    c.clearRect(0, 0, w, h);

    var step = gridStep;
    var x = 0;
    while (x <= w) {
      var isTenth = (x > 0 && x % (step * 10) === 0);
      c.strokeStyle = isTenth ? 'rgba(0, 0, 0, 0.35)' : 'rgba(0, 0, 0, 0.12)';
      c.lineWidth = isTenth ? 2.5 : 1;
      c.beginPath();
      c.moveTo(x, 0);
      c.lineTo(x, h);
      c.stroke();
      if (x > 0) {
        c.fillStyle = 'rgba(0, 0, 0, 0.5)';
        c.font = '4px monospace';
        c.fillText(String(x), x + 1, 5);
      }
      x += step;
    }

    var y = 0;
    while (y <= h) {
      var isTenthY = (y > 0 && y % (step * 10) === 0);
      c.strokeStyle = isTenthY ? 'rgba(0, 0, 0, 0.35)' : 'rgba(0, 0, 0, 0.12)';
      c.lineWidth = isTenthY ? 2.5 : 1;
      c.beginPath();
      c.moveTo(0, y);
      c.lineTo(w, y);
      c.stroke();
      if (y > 0) {
        c.fillStyle = 'rgba(0, 0, 0, 0.5)';
        c.font = '4px monospace';
        c.fillText(String(y), 1, y + 4);
      }
      y += step;
    }

    c.fillStyle = 'rgba(0, 0, 0, 0.7)';
    c.font = '4px monospace';
    c.fillText('0', 1, 5);

    drawCellIds();
  }

  function init() {
    resizeGrid();
    window.addEventListener('resize', resizeGrid);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
