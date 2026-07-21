// Sudoku game controller
(function () {
  const boardEl = document.getElementById('board');
  const timerEl = document.getElementById('timer');
  const mistakesEl = document.getElementById('mistakes');
  const hintText = document.getElementById('hintText');
  const overlay = document.getElementById('overlay');
  const modalTitle = document.getElementById('modalTitle');
  const modalBody = document.getElementById('modalBody');
  const undoBtn = document.getElementById('undoBtn');
  const redoBtn = document.getElementById('redoBtn');
  const hintBtn = document.getElementById('hintBtn');

  let puzzle = [];
  let solution = [];
  let board = [];
  let given = [];
  // notes[r][c] = array of 9 booleans (index 0 = digit 1)
  let notes = [];
  let selected = null;
  let mistakes = 0;
  let timerInterval = null;
  let elapsed = 0;
  let difficulty = 40;
  let mode = 'final'; // 'final' | 'notes'
  let currentGameId = null;
  let saveTimer = null;
  let gameCompleted = false;
  const STORAGE_KEY = 'sudoku_current_game';
  const gamesOverlay = document.getElementById('gamesOverlay');
  const gamesTableBody = document.getElementById('gamesTableBody');
  const gamesEmpty = document.getElementById('gamesEmpty');

  // ----- Undo/Redo -----
  // Each snapshot captures board, notes, given, mistakes
  let undoStack = [];
  let redoStack = [];
  const MAX_HISTORY = 200;

  function snapshot() {
    return {
      board: board.map((row) => [...row]),
      notes: notes.map((row) => row.map((n) => [...n])),
      given: given.map((row) => [...row]),
      mistakes,
    };
  }

  function restore(snap) {
    board = snap.board.map((row) => [...row]);
    notes = snap.notes.map((row) => row.map((n) => [...n]));
    given = snap.given.map((row) => [...row]);
    mistakes = snap.mistakes;
    mistakesEl.textContent = mistakes;
    renderBoard();
  }

  function pushHistory() {
    undoStack.push(snapshot());
    if (undoStack.length > MAX_HISTORY) undoStack.shift();
    redoStack = [];
    updateUndoRedoButtons();
  }

  function undo() {
    if (undoStack.length === 0) return;
    redoStack.push(snapshot());
    restore(undoStack.pop());
    updateUndoRedoButtons();
    flashHint('Undo');
    scheduleAutoSave();
  }

  function redo() {
    if (redoStack.length === 0) return;
    undoStack.push(snapshot());
    restore(redoStack.pop());
    updateUndoRedoButtons();
    flashHint('Redo');
    scheduleAutoSave();
  }

  function updateUndoRedoButtons() {
    undoBtn.disabled = undoStack.length === 0;
    redoBtn.disabled = redoStack.length === 0;
  }

  // ----- Helpers -----
  function emptyNotes() {
    const n = [];
    for (let r = 0; r < 9; r++) {
      const row = [];
      for (let c = 0; c < 9; c++) row.push(new Array(9).fill(false));
      n.push(row);
    }
    return n;
  }

  function sameBox(r1, c1, r2, c2) {
    return (
      Math.floor(r1 / 3) === Math.floor(r2 / 3) &&
      Math.floor(c1 / 3) === Math.floor(c2 / 3)
    );
  }

  function countDigit(num) {
    let count = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (board[r][c] === num) count++;
      }
    }
    return count;
  }

  function updateNumpad() {
    document.querySelectorAll('.num-btn').forEach((btn) => {
      const num = +btn.dataset.num;
      if (num === 0) return; // erase button always enabled
      btn.disabled = countDigit(num) >= 9;
    });
  }

  // ----- Board rendering -----
  function renderBoard() {
    boardEl.innerHTML = '';
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        const cell = document.createElement('div');
        cell.className = 'cell';
        cell.dataset.row = r;
        cell.dataset.col = c;
        renderCellContent(r, c, cell);
        cell.addEventListener('click', () => selectCell(r, c));
        boardEl.appendChild(cell);
      }
    }
    applyHighlights();
    updateNumpad();
  }

  function renderCellContent(r, c, cell) {
    const val = board[r][c];
    cell.classList.remove('given', 'user');
    cell.innerHTML = '';

    if (val !== 0) {
      cell.textContent = val;
      if (given[r][c]) cell.classList.add('given');
      else cell.classList.add('user');
    } else {
      // Show pencil marks only when no final value
      const marks = notes[r][c];
      const has = marks.some((m) => m);
      if (has) {
        const grid = document.createElement('div');
        grid.className = 'pencil-marks';
        for (let i = 0; i < 9; i++) {
          const span = document.createElement('span');
          span.textContent = i + 1;
          if (marks[i]) span.classList.add('on');
          grid.appendChild(span);
        }
        cell.appendChild(grid);
      }
    }
  }

  function getCell(r, c) {
    return boardEl.children[r * 9 + c];
  }

  function selectCell(r, c) {
    // If a hint is previewing, clicking its cell commits; clicking elsewhere dismisses
    if (hintCell) {
      if (hintCell.r === r && hintCell.c === c) {
        commitHint();
        return;
      }
      cancelHintPreview();
    }
    selected = { r, c };
    applyHighlights();
  }

  function applyHighlights() {
    const cells = boardEl.querySelectorAll('.cell');
    cells.forEach((cell) => {
      cell.classList.remove('selected', 'highlight', 'same-num');
    });
    if (!selected) return;

    const { r, c } = selected;
    const selVal = board[r][c];
    cells.forEach((cell) => {
      const cr = +cell.dataset.row;
      const cc = +cell.dataset.col;
      const inRow = cr === r;
      const inCol = cc === c;
      const inBox = sameBox(r, c, cr, cc);
      if (inRow || inCol || inBox) cell.classList.add('highlight');
      if (selVal !== 0 && board[cr][cc] === selVal) cell.classList.add('same-num');
    });
    getCell(r, c).classList.add('selected');
  }

  // ----- Input -----
  function placeNumber(num) {
    if (!selected) {
      flashHint('Select a cell first.');
      return;
    }
    const { r, c } = selected;
    if (given[r][c]) {
      flashHint('That cell is pre-filled.');
      return;
    }

    const cell = getCell(r, c);
    cell.classList.remove('error', 'hint-flash');

    // Erase
    if (num === 0) {
      if (board[r][c] !== 0) {
        // Has a final number — remove it; preserved pencil marks reappear
        pushHistory();
        board[r][c] = 0;
      } else {
        // No final number — clear all pencil marks
        const hadNotes = notes[r][c].some((m) => m);
        if (!hadNotes) return; // nothing to erase
        pushHistory();
        notes[r][c] = new Array(9).fill(false);
      }
      renderCellContent(r, c, cell);
      updateNumpad();
      applyHighlights();
      scheduleAutoSave();
      return;
    }

    if (mode === 'notes') {
      pushHistory();
      toggleNote(r, c, num);
    } else {
      pushHistory();
      placeFinal(r, c, num);
    }

    updateNumpad();
    applyHighlights();
    scheduleAutoSave();
    checkWin();
  }

  function toggleNote(r, c, num) {
    const idx = num - 1;
    notes[r][c][idx] = !notes[r][c][idx];
    renderCellContent(r, c, getCell(r, c));
  }

  function placeFinal(r, c, num) {
    board[r][c] = num;
    // Pencil marks are preserved (hidden) — they reappear if this number is erased
    renderCellContent(r, c, getCell(r, c));

    // Auto-remove this number from pencil marks in row/col/box
    for (let i = 0; i < 9; i++) {
      if (notes[r][i][num - 1]) {
        notes[r][i][num - 1] = false;
        if (board[r][i] === 0) renderCellContent(r, i, getCell(r, i));
      }
      if (notes[i][c][num - 1]) {
        notes[i][c][num - 1] = false;
        if (board[i][c] === 0) renderCellContent(i, c, getCell(i, c));
      }
    }
    for (let br = Math.floor(r / 3) * 3; br < Math.floor(r / 3) * 3 + 3; br++) {
      for (let bc = Math.floor(c / 3) * 3; bc < Math.floor(c / 3) * 3 + 3; bc++) {
        if (notes[br][bc][num - 1]) {
          notes[br][bc][num - 1] = false;
          if (board[br][bc] === 0) renderCellContent(br, bc, getCell(br, bc));
        }
      }
    }

    if (num !== solution[r][c]) {
      getCell(r, c).classList.add('error');
      mistakes++;
      mistakesEl.textContent = mistakes;
      flashHint('Not quite — try again.');
    } else {
      flashHint('');
    }
  }

  // ----- Game actions -----
  function checkWin() {
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (board[r][c] !== solution[r][c]) return false;
      }
    }
    stopTimer();
    gameCompleted = true;
    saveGameToServer(); // save final state
    modalTitle.textContent = '🎉 You solved it!';
    modalBody.textContent = `Time: ${formatTime(elapsed)} · Mistakes: ${mistakes}`;
    overlay.classList.add('show');
    return true;
  }

  // ----- Hint (press to preview, click cell to apply) -----
  // Press the hint button: shows a preview (amber) of a correct cell with its number.
  // Release: the preview stays. User clicks the cell to apply, or clicks elsewhere / Escape to dismiss.
  let hintCell = null;

  function startHintPreview() {
    // Clear any existing preview first
    if (hintCell) cancelHintPreview();

    const empty = [];
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (board[r][c] !== solution[r][c]) empty.push({ r, c });
      }
    }
    if (empty.length === 0) {
      flashHint('Nothing left to hint!');
      return;
    }
    const { r, c } = empty[Math.floor(Math.random() * empty.length)];
    hintCell = { r, c, val: solution[r][c] };
    const cell = getCell(r, c);
    cell.textContent = solution[r][c];
    cell.classList.add('hint-preview');
    selected = { r, c };
    applyHighlights();
    cell.classList.add('hint-preview');
    flashHint('Click the cell to apply, or press Escape to dismiss.');
  }

  function commitHint() {
    if (!hintCell) return;
    const { r, c, val } = hintCell;
    const cell = getCell(r, c);
    cell.classList.remove('hint-preview');
    pushHistory();
    board[r][c] = val;
    given[r][c] = true;
    notes[r][c] = new Array(9).fill(false);
    renderCellContent(r, c, cell);
    cell.classList.add('given', 'hint-flash');
    cell.classList.remove('user', 'error');
    applyHighlights();
    setTimeout(() => cell.classList.remove('hint-flash'), 600);
    updateNumpad();
    hintCell = null;
    flashHint('Hint applied!');
    scheduleAutoSave();
    checkWin();
  }

  function cancelHintPreview() {
    if (!hintCell) return;
    const { r, c } = hintCell;
    const cell = getCell(r, c);
    cell.classList.remove('hint-preview');
    hintCell = null;
    renderCellContent(r, c, cell);
    applyHighlights();
    flashHint('');
  }

  function checkBoard() {
    let wrong = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (board[r][c] !== 0 && board[r][c] !== solution[r][c]) {
          wrong++;
          getCell(r, c).classList.add('error');
        }
      }
    }
    flashHint(wrong === 0 ? 'Looking great! No errors.' : `${wrong} cell(s) look off.`);
  }

  // ----- New game -----
  async function newGame() {
    overlay.classList.remove('show');
    gamesOverlay.classList.remove('show');
    mistakes = 0;
    mistakesEl.textContent = '0';
    undoStack = [];
    redoStack = [];
    gameCompleted = false;
    currentGameId = null;
    updateUndoRedoButtons();
    flashHint('Generating new puzzle…');
    try {
      const res = await fetch(`/api/new-game?difficulty=${difficulty}`);
      const data = await res.json();
      puzzle = data.puzzle;
      solution = data.solution;
      board = puzzle.map((row) => [...row]);
      given = puzzle.map((row) => row.map((v) => v !== 0));
      notes = emptyNotes();
      selected = null;
      renderBoard();
      resetTimer();
      startTimer();
      // Create game record on server immediately (not debounced)
      await createGameOnServer();
      flashHint('New game started — saved!');
    } catch (err) {
      flashHint('Failed to load puzzle.');
    }
  }

  // ----- Mode toggle -----
  function setMode(newMode) {
    mode = newMode;
    document.querySelectorAll('.mode-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.mode === newMode);
    });
  }

  // ----- Timer -----
  function formatTime(s) {
    const m = String(Math.floor(s / 60)).padStart(2, '0');
    const sec = String(s % 60).padStart(2, '0');
    return `${m}:${sec}`;
  }

  function startTimer() {
    elapsed = 0;
    timerEl.textContent = '00:00';
    timerInterval = setInterval(() => {
      elapsed++;
      timerEl.textContent = formatTime(elapsed);
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
  }

  function resetTimer() {
    stopTimer();
    elapsed = 0;
    timerEl.textContent = '00:00';
  }

  // ----- Hint text -----
  let hintTimeout = null;
  function flashHint(msg) {
    hintText.textContent = msg;
    if (hintTimeout) clearTimeout(hintTimeout);
    if (msg) {
      hintTimeout = setTimeout(() => (hintText.textContent = ''), 2500);
    }
  }

  // ----- Game persistence -----
  function serializeState() {
    return {
      puzzle: puzzle.map((row) => [...row]),
      solution: solution.map((row) => [...row]),
      board: board.map((row) => [...row]),
      given: given.map((row) => [...row]),
      notes: notes.map((row) => row.map((n) => [...n])),
      undoStack: undoStack.map((snap) => ({
        board: snap.board.map((r) => [...r]),
        notes: snap.notes.map((r) => r.map((n) => [...n])),
        given: snap.given.map((r) => [...r]),
        mistakes: snap.mistakes,
      })),
      redoStack: redoStack.map((snap) => ({
        board: snap.board.map((r) => [...r]),
        notes: snap.notes.map((r) => r.map((n) => [...n])),
        given: snap.given.map((r) => [...r]),
        mistakes: snap.mistakes,
      })),
      mistakes,
      elapsed,
      difficulty,
      completed: gameCompleted,
    };
  }

  function saveToLocalStorage() {
    if (currentGameId) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ game_id: currentGameId }));
      } catch (e) { /* localStorage may be unavailable */ }
    }
  }

  function scheduleAutoSave() {
    if (gameCompleted) return;
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(saveGameToServer, 2000); // debounce 2s
  }

  async function createGameOnServer() {
    const state = serializeState();
    try {
      const res = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      });
      if (!res.ok) {
        console.error('Failed to create game on server:', res.status);
        return;
      }
      const data = await res.json();
      currentGameId = data.game_id;
      saveToLocalStorage();
    } catch (err) {
      console.error('createGameOnServer error:', err);
    }
  }

  async function saveGameToServer() {
    if (!currentGameId || gameCompleted) return;
    const state = serializeState();
    try {
      await fetch(`/api/games/${currentGameId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      });
    } catch (err) {
      // Silently fail — game continues locally
    }
  }

  async function loadGame(gameId) {
    try {
      const res = await fetch(`/api/games/${gameId}`);
      if (!res.ok) {
        flashHint('Game not found.');
        return;
      }
      const state = await res.json();
      restoreFromState(state);
      currentGameId = gameId;
      saveToLocalStorage();
      gamesOverlay.classList.remove('show');
      flashHint('Game loaded!');
    } catch (err) {
      flashHint('Failed to load game.');
    }
  }

  function restoreFromState(state) {
    puzzle = state.puzzle;
    solution = state.solution;
    board = state.board;
    given = state.given;
    notes = state.notes;
    mistakes = state.mistakes || 0;
    elapsed = state.elapsed || 0;
    difficulty = state.difficulty || 40;
    gameCompleted = state.completed || false;
    undoStack = state.undoStack || [];
    redoStack = state.redoStack || [];
    selected = null;
    mistakesEl.textContent = mistakes;
    // Update difficulty buttons
    document.querySelectorAll('.diff-btn').forEach((b) => {
      b.classList.toggle('active', +b.dataset.difficulty === difficulty);
    });
    renderBoard();
    updateUndoRedoButtons();
    // Restore timer
    stopTimer();
    timerEl.textContent = formatTime(elapsed);
    if (!gameCompleted) startTimer();
  }

  async function loadGamesList() {
    try {
      const res = await fetch('/api/games?limit=50');
      const data = await res.json();
      renderGamesList(data.games || []);
    } catch (err) {
      flashHint('Failed to load games list.');
    }
  }

  function renderGamesList(games) {
    gamesTableBody.innerHTML = '';
    if (games.length === 0) {
      gamesEmpty.style.display = 'block';
      return;
    }
    gamesEmpty.style.display = 'none';

    const diffNames = { 30: 'Easy', 40: 'Medium', 50: 'Hard', 58: 'Expert' };
    const diffClasses = { 30: 'easy', 40: 'medium', 50: 'hard', 58: 'expert' };

    for (const game of games) {
      const row = document.createElement('tr');
      const diff = game.difficulty || 40;
      const diffName = diffNames[diff] || 'Medium';
      const diffClass = diffClasses[diff] || 'medium';
      const updated = game.updated_at ? new Date(game.updated_at).toLocaleString() : '—';

      row.innerHTML = `
        <td><span class="difficulty-badge ${diffClass}">${diffName}</span></td>
        <td>${game.progress || '—'}</td>
        <td>${game.mistakes || 0}</td>
        <td>${formatTime(game.elapsed || 0)}</td>
        <td>${updated}</td>
        <td>
          <div class="game-actions">
            <button class="resume-btn" data-id="${game.game_id}">▶ Resume</button>
            <button class="delete-btn" data-id="${game.game_id}">🗑 Delete</button>
          </div>
        </td>
      `;
      gamesTableBody.appendChild(row);
    }

    // Attach event listeners
    gamesTableBody.querySelectorAll('.resume-btn').forEach((btn) => {
      btn.addEventListener('click', () => loadGame(btn.dataset.id));
    });
    gamesTableBody.querySelectorAll('.delete-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await fetch(`/api/games/${btn.dataset.id}`, { method: 'DELETE' });
          if (btn.dataset.id === currentGameId) {
            currentGameId = null;
            localStorage.removeItem(STORAGE_KEY);
          }
          loadGamesList(); // refresh
          flashHint('Game deleted.');
        } catch (err) {
          flashHint('Failed to delete game.');
        }
      });
    });
  }

  function showGamesModal() {
    gamesOverlay.classList.add('show');
    loadGamesList();
  }

  function hideGamesModal() {
    gamesOverlay.classList.remove('show');
  }

  // Try to resume the last game from localStorage on page load
  async function tryResumeLastGame() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return false;
      const { game_id } = JSON.parse(saved);
      if (!game_id) return false;
      const res = await fetch(`/api/games/${game_id}`);
      if (!res.ok) {
        localStorage.removeItem(STORAGE_KEY);
        return false;
      }
      const state = await res.json();
      restoreFromState(state);
      currentGameId = game_id;
      flashHint('Resumed your last game!');
      return true;
    } catch (e) {
      return false;
    }
  }

  // ----- Event listeners -----
  document.getElementById('numpad').addEventListener('click', (e) => {
    const btn = e.target.closest('.num-btn');
    if (!btn || btn.disabled) return;
    placeNumber(+btn.dataset.num);
  });

  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.addEventListener('click', () => setMode(btn.dataset.mode));
  });

  document.getElementById('newGameBtn').addEventListener('click', newGame);
  document.getElementById('checkBtn').addEventListener('click', checkBoard);
  document.getElementById('modalNewGame').addEventListener('click', newGame);
  document.getElementById('loadGamesBtn').addEventListener('click', showGamesModal);
  document.getElementById('closeGamesBtn').addEventListener('click', hideGamesModal);

  undoBtn.addEventListener('click', undo);
  redoBtn.addEventListener('click', redo);

  // Hint: press to preview, click cell to apply
  hintBtn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    startHintPreview();
  });
  hintBtn.addEventListener('mouseleave', () => {
    if (hintCell) cancelHintPreview();
  });
  hintBtn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startHintPreview();
  }, { passive: false });

  document.querySelectorAll('.diff-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.diff-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      difficulty = +btn.dataset.difficulty;
      newGame();
    });
  });

  // Keyboard input
  document.addEventListener('keydown', (e) => {
    // Undo/Redo
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
      e.preventDefault();
      undo();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) {
      e.preventDefault();
      redo();
      return;
    }

    if (e.key === 'Escape' && hintCell) {
      cancelHintPreview();
      return;
    }

    if (e.key >= '1' && e.key <= '9') {
      placeNumber(+e.key);
    } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
      placeNumber(0);
    } else if (e.key.toLowerCase() === 'n') {
      setMode(mode === 'final' ? 'notes' : 'final');
    } else if (e.key === 'ArrowUp' && selected) {
      selectCell(Math.max(0, selected.r - 1), selected.c);
    } else if (e.key === 'ArrowDown' && selected) {
      selectCell(Math.min(8, selected.r + 1), selected.c);
    } else if (e.key === 'ArrowLeft' && selected) {
      selectCell(selected.r, Math.max(0, selected.c - 1));
    } else if (e.key === 'ArrowRight' && selected) {
      selectCell(selected.r, Math.min(8, selected.c + 1));
    }
  });

  // Start: try resuming last game, otherwise start new
  (async () => {
    const resumed = await tryResumeLastGame();
    if (!resumed) {
      await newGame();
    }
  })();
})();
