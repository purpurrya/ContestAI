(function (global) {
  'use strict';

  var CELLS = (typeof global !== 'undefined' && global.CELLS) ? global.CELLS : [];

  var BLACK_CELL_IDS = [0,2,4,6,9,11,13,15,16,18,20,22,25,27,29,31,32,34,36,38,41,43,45,47,48,50,52,54,57,59,61,63,64,66,68,70,73,75,77,79,80,82,84,86,89,91,93,95];
  function isBlackCell(id) {
    return BLACK_CELL_IDS.indexOf(id) !== -1;
  }

  function isCellDefined(cell) {
    if (!cell || !cell.corners || cell.corners.length < 4) return false;
    var c = cell.corners;
    var sum = 0;
    for (var i = 0; i < 4; i++) sum += c[i].x + c[i].y;
    return sum !== 0;
  }

  function getCellCenter(cell) {
    if (!cell || !cell.corners || cell.corners.length < 4) return null;
    var c = cell.corners;
    return {
      x: (c[0].x + c[1].x + c[2].x + c[3].x) / 4,
      y: (c[0].y + c[1].y + c[2].y + c[3].y) / 4
    };
  }

  function edgeKey(p1, p2) {
    var swap = p1.x > p2.x || (p1.x === p2.x && p1.y > p2.y);
    if (swap) { var t = p1; p1 = p2; p2 = t; }
    return p1.x + ',' + p1.y + '|' + p2.x + ',' + p2.y;
  }

  function buildBlackGraph() {
    var edgeToCells = {};
    var i, j, cell, c, key, ids, idA, idB;
    for (i = 0; i < CELLS.length; i++) {
      cell = CELLS[i];
      if (!isCellDefined(cell)) continue;
      c = cell.corners;
      for (j = 0; j < 4; j++) {
        var next = (j + 1) % 4;
        key = edgeKey(c[j], c[next]);
        if (!edgeToCells[key]) edgeToCells[key] = [];
        if (edgeToCells[key].indexOf(cell.id) === -1) edgeToCells[key].push(cell.id);
      }
    }
    var nodes = [];
    var edges = [];
    var seen = {};
    for (key in edgeToCells) {
      ids = edgeToCells[key];
      for (i = 0; i < ids.length; i++) {
        for (j = i + 1; j < ids.length; j++) {
          idA = ids[i];
          idB = ids[j];
          if (!isBlackCell(idA) || !isBlackCell(idB)) continue;
          var edgeId = idA < idB ? idA + '-' + idB : idB + '-' + idA;
          if (!seen[edgeId]) {
            seen[edgeId] = true;
            edges.push([idA, idB]);
          }
        }
      }
    }
    for (i = 0; i < CELLS.length; i++) {
      cell = CELLS[i];
      if (!isBlackCell(cell.id) || !isCellDefined(cell)) continue;
      var center = getCellCenter(cell);
      if (center) nodes.push({ id: cell.id, x: center.x, y: center.y });
    }
    return { nodes: nodes, edges: edges };
  }

  var graphCache = null;
  function getBlackGraph() {
    if (!graphCache) graphCache = buildBlackGraph();
    return graphCache;
  }

  function invalidateGraph() {
    graphCache = null;
  }

  // соседи по доске 
  var MOVES = {};
  (function initMoves() {
    for (var i = 0; i < BLACK_CELL_IDS.length; i++) MOVES[BLACK_CELL_IDS[i]] = [];
  })();
  // левая треть
  MOVES[0] = [9];
  MOVES[2] = [9, 11];
  MOVES[4] = [11, 13];
  MOVES[6] = [13, 15];
  MOVES[9] = [0, 2, 16, 18];
  MOVES[11] = [2, 4, 18, 20];
  MOVES[13] = [4, 6, 20, 22];
  MOVES[15] = [6, 22];
  MOVES[16] = [9, 25];
  MOVES[18] = [9, 11, 25, 27];
  MOVES[20] = [11, 13, 27, 29];
  MOVES[22] = [13, 15, 29, 31];
  MOVES[25] = [18, 16, 63, 61];
  MOVES[27] = [18, 20, 59, 61, 91];
  MOVES[29] = [20, 22, 89, 91];
  MOVES[31] = [22, 89];
  //правая треть
  MOVES[32] = [41];
  MOVES[34] = [41, 43];
  MOVES[36] = [43, 45];
  MOVES[38] = [45, 47];
  MOVES[41] = [32, 34, 48, 50];
  MOVES[43] = [34, 36, 50, 52];
  MOVES[45] = [36, 38, 52, 54];
  MOVES[47] = [38, 54];
  MOVES[48] = [41, 57];
  MOVES[50] = [41, 43, 57, 59];
  MOVES[52] = [43, 45, 59, 61];
  MOVES[54] = [45, 47, 61, 63];
  MOVES[57] = [48, 50, 93, 95];
  MOVES[59] = [27, 50, 52, 91, 93];
  MOVES[61] = [25, 27, 52, 54];
  MOVES[63] = [25, 54];
  //нижняя треть
  MOVES[64] = [73];
  MOVES[66] = [73, 75];
  MOVES[68] = [75, 77];
  MOVES[70] = [77, 79];
  MOVES[73] = [64, 66, 80, 82];
  MOVES[75] = [66, 68, 82, 84];
  MOVES[77] = [68, 70, 84, 86];
  MOVES[79] = [86];
  MOVES[80] = [73, 89];
  MOVES[82] = [73, 75, 89, 91];
  MOVES[84] = [75, 77, 91, 93];
  MOVES[86] = [77, 79, 93, 95];
  MOVES[89] = [29, 31, 80, 82];
  MOVES[91] = [29, 27, 59, 82, 84];
  MOVES[93] = [57, 59, 84, 86];
  MOVES[95] = [57, 86];

  function getMovesFrom(cellId) {
    if (!isBlackCell(cellId)) return [];
    return MOVES[cellId] ? MOVES[cellId].slice() : [];
  }

  var Board = {
    isBlackCell: isBlackCell,
    isCellDefined: isCellDefined,
    getCellCenter: getCellCenter,
    getBlackGraph: getBlackGraph,
    buildBlackGraph: buildBlackGraph,
    invalidateGraph: invalidateGraph,
    MOVES: MOVES,
    getMovesFrom: getMovesFrom
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Board;
  } else {
    global.Board = Board;
  }
})(typeof window !== 'undefined' ? window : this);
