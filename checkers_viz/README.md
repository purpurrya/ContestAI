# Визуализация шашек

Открой `index.html` в браузере, выбери JSON с игрой — отображается доска и ползунок ходов.

**Файлы:**
- `game.json`, `game_manual.json` — снимки состояния партии (экспорт из `scripts/export_checkers_json.py`). Для просмотра удобнее использовать файлы из `test_games/` (полные партии с `initial_board` + `move_history`).
- `viz.js` — сетка и номера клеток на canvas.
- `viz_checkers.js` — загрузка JSON, вычисление доски на шаге N, отрисовка шашек. `normBoard` — ключи клеток в число; `buildStateAtStep` — от `initial_board` вперёд по ходам; `buildStateByReversing` — от финальной доски назад (если нет `initial_board`).
- `board-graph.js` — граф чёрных клеток (MOVES = соседи), нужен для отрисовки графа и центров клеток. Данные MOVES дублируют `HAND_NEIGHBORS` в `game_engine/checkers/board_graph.py`: там — логика игры (Python), здесь — визуализация (JS). При смене топологии доски править оба места.

Тестовые партии: `test_games/full_game_1.json` и т.д. Генерация: `python3 scripts/generate_test_jsons.py`.
