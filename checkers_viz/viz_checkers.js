(function (w) {
  'use strict';
  // загрузка  json, воспроизведение ходов по шагам, отрисовка шашек на canvas
  var CELLS = (w.CELLS) ? w.CELLS : [];
  var Board = w.Board || null;
  var GRID_W = 960;
  var GRID_H = 840;

  var data = null;
  var step = 0;
  var canvas = null;

  var COLORS = {
    white: '#f8f6f0',
    red: '#c44',
    black: '#2c2c2c',
    kingDot: '#5a5a5a'
  };

  function getCellCenter(cell) {
    if (Board && Board.getCellCenter) return Board.getCellCenter(cell);
    if (!cell || !cell.corners || cell.corners.length < 4) return null;
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

  function normBoard(board) {
    // ключи клеток -> число (json приходит строками)
    var out = {};
    if (!board) return out;
    for (var key in board) {
      var id = typeof key === 'string' ? parseInt(key, 10) : key;
      if (isNaN(id)) continue;
      out[id] = board[key];
    }
    return out;
  }

  function buildStateAtStep(initialBoard, moveHistory, stepIndex) {
    // от начальной доски применяем первые stepIndex ходов
    var board = {};
    var k, id;
    for (k in initialBoard) {
      id = typeof k === 'string' ? parseInt(k, 10) : k;
      board[id] = initialBoard[k];
    }
    var history = moveHistory || [];
    var n = Math.min(stepIndex, history.length);
    for (var i = 0; i < n; i++) {
      var mv = history[i];
      var fromId = typeof mv.from === 'string' ? parseInt(mv.from, 10) : mv.from;
      var toId = typeof mv.to === 'string' ? parseInt(mv.to, 10) : mv.to;
      var piece = board[fromId];
      if (piece) {
        delete board[fromId];
        board[toId] = piece;
        if (mv.captured != null) {
          var cap = Array.isArray(mv.captured) ? mv.captured : [mv.captured];
          for (var c = 0; c < cap.length; c++) {
            var cid = typeof cap[c] === 'string' ? parseInt(cap[c], 10) : cap[c];
            delete board[cid];
          }
        }
      }
    }
    return board;
  }

  function buildStateByReversing(finalBoard, moveHistory, stepIndex) {
    // от финальной доски откатываем ходы назад (если нет initial_board)
    var board = {};
    var k, id;
    for (k in finalBoard) {
      id = typeof k === 'string' ? parseInt(k, 10) : k;
      board[id] = finalBoard[k];
    }
    var history = moveHistory || [];
    var toUndo = history.length - stepIndex;
    for (var i = history.length - 1; i >= 0 && toUndo > 0; i--, toUndo--) {
      var mv = history[i];
      var fromId = typeof mv.from === 'string' ? parseInt(mv.from, 10) : mv.from;
      var toId = typeof mv.to === 'string' ? parseInt(mv.to, 10) : mv.to;
      var piece = board[toId];
      if (piece) {
        delete board[toId];
        board[fromId] = piece;
      }
    }
    return board;
  }

  function getCurrentBoard() {
    if (!data) return {};
    var history = data.move_history || [];
    var total = history.length;
    if (data.initial_board) {
      var initial = normBoard(data.initial_board);
      return buildStateAtStep(initial, history, step);
    }
    var board = normBoard(data.board);
    if (!board || Object.keys(board).length === 0) return {};
    return buildStateByReversing(board, history, step);
  }

  function drawPiece(ctx, cellId, piece) {
    var cell = null;
    for (var i = 0; i < CELLS.length; i++) {
      if (CELLS[i].id === cellId) { cell = CELLS[i]; break; }
    }
    if (!cell || !isCellDefined(cell)) return;
    var center = getCellCenter(cell);
    if (!center) return;
    var r = 18;
    var col = COLORS[piece.player] || '#888';
    ctx.beginPath();
    ctx.arc(center.x, center.y, r, 0, Math.PI * 2);
    ctx.fillStyle = col;
    ctx.fill();
    ctx.strokeStyle = '#5a5a5a';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    if (piece.is_king) {
      ctx.fillStyle = COLORS.kingDot;
      ctx.beginPath();
      ctx.arc(center.x, center.y, r * 0.35, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.fillStyle = (piece.player === 'white') ? '#2c2c2c' : '#f8f6f0';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(cellId), center.x, center.y);
  }

  function draw() {
    var el = canvas || (canvas = document.getElementById('checkers-layer'));
    if (!el) return;
    if (el.width !== GRID_W || el.height !== GRID_H) {
      el.width = GRID_W;
      el.height = GRID_H;
    }
    var ctx = el.getContext('2d');
    ctx.clearRect(0, 0, el.width, el.height);

    if (data && (data.board || data.initial_board)) {
      var board = getCurrentBoard();
      for (var id in board) {
        drawPiece(ctx, parseInt(id, 10), board[id]);
      }
    }
  }

  function setErr(msg) {
    var el = document.getElementById('err');
    if (el) el.textContent = msg || '';
  }

  function updateStepInfo() {
    var total = (data && data.move_history ? data.move_history.length : 0) || 0;
    step = Math.max(0, Math.min(step, total));
    var slider = document.getElementById('slider');
    var info = document.getElementById('stepInfo');
    if (slider) { slider.max = total; slider.value = step; }
    if (info) info.textContent = step + ' / ' + total;
    var prev = document.getElementById('btnPrev');
    var next = document.getElementById('btnNext');
    if (prev) prev.disabled = step <= 0;
    if (next) next.disabled = step >= total;
  }

  function loadFromFile(file) {
    var reader = new FileReader();
    reader.onload = function () {
      try {
        data = JSON.parse(reader.result);
        if (!data.board && !data.initial_board) {
          setErr('В JSON должен быть board или initial_board.');
          return;
        }
        setErr('');
        step = 0;
        updateStepInfo();
        resize();
        draw();
      } catch (e) {
        setErr('Ошибка JSON: ' + e.message);
      }
    };
    reader.readAsText(file, 'utf-8');
  }

  function onLoadClick() {
    var input = document.getElementById('file');
    if (!input || !input.files || !input.files[0]) {
      setErr('Выбери файл JSON.');
      return;
    }
    loadFromFile(input.files[0]);
  }

  function resize() {
    if (!canvas) canvas = document.getElementById('checkers-layer');
    if (!canvas) return;
    if (canvas.width !== GRID_W || canvas.height !== GRID_H) {
      canvas.width = GRID_W;
      canvas.height = GRID_H;
    }
    draw();
  }

  function init() {
    canvas = document.getElementById('checkers-layer');
    var fileInput = document.getElementById('file');
    var btnLoad = document.getElementById('btnLoad');
    var btnPrev = document.getElementById('btnPrev');
    var btnNext = document.getElementById('btnNext');
    if (fileInput) fileInput.addEventListener('change', function () {
      if (this.files[0]) loadFromFile(this.files[0]);
    });
    if (btnLoad) btnLoad.addEventListener('click', onLoadClick);
    if (btnPrev) btnPrev.addEventListener('click', function () {
      step--;
      updateStepInfo();
      draw();
    });
    if (btnNext) btnNext.addEventListener('click', function () {
      step++;
      updateStepInfo();
      draw();
    });
    var slider = document.getElementById('slider');
    if (slider) slider.addEventListener('input', function () {
      step = parseInt(this.value, 10);
      updateStepInfo();
      draw();
    });
    w.addEventListener('resize', resize);
    updateStepInfo();
    resize();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(typeof window !== 'undefined' ? window : this);
