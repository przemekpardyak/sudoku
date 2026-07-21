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
  const difficultyLabel = document.getElementById('difficultyLabel');
  const progressLabel = document.getElementById('progressLabel');

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
  let hintsUsed = 0;
  const STORAGE_KEY = 'sudoku_current_game';
  const gamesOverlay = document.getElementById('gamesOverlay');
  const gamesTableBody = document.getElementById('gamesTableBody');
  const gamesEmpty = document.getElementById('gamesEmpty');

  const DIFF_NAMES = { 30: 'Easy', 40: 'Medium', 50: 'Hard', 58: 'Expert' };

  function updateDifficultyLabel() {
    difficultyLabel.textContent = DIFF_NAMES[difficulty] || 'Medium';
  }

  function updateProgress() {
    let total = 0;
    let filled = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (!given[r][c] && puzzle[r][c] === 0) {
          total++;
          if (board[r][c] !== 0) filled++;
        }
      }
    }
    const pct = total > 0 ? Math.round((filled / total) * 100) : 100;
    progressLabel.textContent = `${pct}%`;
    if (pct === 100) progressLabel.style.color = '#4ade80';
    else if (pct >= 50) progressLabel.style.color = '#fbbf24';
    else progressLabel.style.color = '';
  }

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
      const placed = countDigit(num);
      btn.disabled = placed >= 9;
      // Update remaining count badge
      let badge = btn.querySelector('.num-remaining');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'num-remaining';
        btn.appendChild(badge);
      }
      badge.textContent = 9 - placed;
      badge.style.opacity = (9 - placed) === 0 ? '0.3' : '1';
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
      cell.classList.remove('selected', 'highlight', 'same-num', 'conflict');
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

    // Conflict detection: highlight cells with duplicate numbers in same row/col/box
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        const v = board[i][j];
        if (v === 0) continue;
        const hasConflict =
          board[i].filter((x) => x === v).length > 1 ||
          board.filter((row) => row[j] === v).length > 1 ||
          (function () {
            const br = Math.floor(i / 3) * 3;
            const bc = Math.floor(j / 3) * 3;
            let count = 0;
            for (let r2 = br; r2 < br + 3; r2++)
              for (let c2 = bc; c2 < bc + 3; c2++)
                if (board[r2][c2] === v) count++;
            return count > 1;
          })();
        if (hasConflict) {
          getCell(i, j).classList.add('conflict');
        }
      }
    }

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
    updateProgress();
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
      mistakesEl.classList.remove('mistake-flash');
      void mistakesEl.offsetWidth; // trigger reflow
      mistakesEl.classList.add('mistake-flash');
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
    // Celebration: flash all cells green briefly
    document.querySelectorAll('.cell').forEach((cell) => {
      cell.classList.add('win-flash');
      setTimeout(() => cell.classList.remove('win-flash'), 1000);
    });
    modalTitle.textContent = '🎉 You solved it!';
    const diffName = DIFF_NAMES[difficulty] || 'Medium';
    modalBody.innerHTML = `
      <div class="win-stats">
        <div class="win-stat"><span>⏱ Time</span><strong>${formatTime(elapsed)}</strong></div>
        <div class="win-stat"><span>📊 Level</span><strong>${diffName}</strong></div>
        <div class="win-stat"><span>❌ Mistakes</span><strong>${mistakes}</strong></div>
        <div class="win-stat"><span>💡 Hints</span><strong>${hintsUsed}</strong></div>
      </div>
      <p class="win-rating" id="winRating"></p>
    `;
    overlay.classList.add('show');
    // Check if this is a new best time
    fetchBestTimes().then((bestTimes) => {
      const best = bestTimes[String(difficulty)];
      const ratingEl = document.getElementById('winRating');
      if (best && elapsed <= best) {
        if (ratingEl) ratingEl.textContent = '🏆 New best time!';
      } else if (best) {
        if (ratingEl) ratingEl.textContent = `Best: ${formatTime(best)}`;
      }
      // Performance rating based on mistakes and hints
      if (ratingEl) {
        let rating = '';
        if (mistakes === 0 && hintsUsed === 0) rating = '⭐⭐⭐ Perfect!';
        else if (mistakes <= 2 && hintsUsed <= 2) rating += ' ⭐⭐ Great!';
        else rating += ' ⭐ Good game!';
        if (ratingEl.textContent) ratingEl.textContent += ' · ' + rating.trim();
        else ratingEl.textContent = rating.trim();
      }
    });
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
    updateProgress();
    hintCell = null;
    hintsUsed = (hintsUsed || 0) + 1;
    flashHint(`Hint applied! (${hintsUsed} used)`);
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
    // Also check for structural conflicts via API
    fetch('/api/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ board }),
    }).then(r => r.json()).then(data => {
      let msg = wrong === 0 ? 'Looking great! No errors.' : `${wrong} cell(s) look off.`;
      if (data.conflicts && data.conflicts.length > 0) {
        msg += ` ${data.conflicts.length} conflict(s) found.`;
      }
      if (data.unique_solution === true) {
        msg += ' Solution is unique! 🎯';
      }
      flashHint(msg);
    }).catch(() => {
      flashHint(wrong === 0 ? 'Looking great! No errors.' : `${wrong} cell(s) look off.`);
    });
  }

  function autoNotes() {
    pushHistory();
    let count = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (board[r][c] !== 0 || given[r][c]) continue;
        for (let n = 1; n <= 9; n++) {
          let possible = true;
          // Check row
          for (let i = 0; i < 9; i++) {
            if (board[r][i] === n || board[i][c] === n) { possible = false; break; }
          }
          // Check box
          if (possible) {
            const br = Math.floor(r / 3) * 3;
            const bc = Math.floor(c / 3) * 3;
            for (let r2 = br; r2 < br + 3 && possible; r2++) {
              for (let c2 = bc; c2 < bc + 3 && possible; c2++) {
                if (board[r2][c2] === n) possible = false;
              }
            }
          }
          notes[r][c][n - 1] = possible;
          if (possible) count++;
        }
        renderCellContent(r, c, getCell(r, c));
      }
    }
    applyHighlights();
    scheduleAutoSave();
    flashHint(count > 0 ? `Filled ${count} pencil marks.` : 'No empty cells to fill.');
  }

  function solvePuzzle() {
    if (gameCompleted) return;
    if (!confirm('Show the solution? This will end the current game.')) return;
    pushHistory();
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (!given[r][c]) {
          board[r][c] = solution[r][c];
          notes[r][c] = [false, false, false, false, false, false, false, false, false];
          renderCellContent(r, c, getCell(r, c));
        }
      }
    }
    gameCompleted = true;
    stopTimer();
    saveGameToServer();
    applyHighlights();
    modalTitle.textContent = '🔍 Solution Revealed';
    modalBody.textContent = `Time: ${formatTime(elapsed)} · Mistakes: ${mistakes}`;
    overlay.classList.add('show');
    flashHint('Solution revealed.');
  }

  function clearNotes() {
    let count = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (notes[r][c].some((m) => m)) count++;
        notes[r][c] = [false, false, false, false, false, false, false, false, false];
        renderCellContent(r, c, getCell(r, c));
      }
    }
    applyHighlights();
    scheduleAutoSave();
    flashHint(count > 0 ? `Cleared pencil marks from ${count} cell(s).` : 'No pencil marks to clear.');
  }

  function resetBoard() {
    // Count cells to reset first
    let count = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (!given[r][c] && board[r][c] !== 0) count++;
      }
    }
    if (count === 0) {
      flashHint('Board is already at original state.');
      return;
    }
    if (!confirm(`Reset ${count} cell(s) back to the original puzzle? This cannot be undone.`)) {
      return;
    }
    let resetCount = 0;
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (!given[r][c] && board[r][c] !== 0) {
          board[r][c] = 0;
          resetCount++;
        }
        notes[r][c] = [false, false, false, false, false, false, false, false, false];
        renderCellContent(r, c, getCell(r, c));
      }
    }
    selected = null;
    applyHighlights();
    updateNumpad();
    updateProgress();
    scheduleAutoSave();
    flashHint(`Reset ${resetCount} cell(s) to original puzzle.`);
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
    hintsUsed = 0;
    currentGameId = null;
    isPaused = false;
    document.getElementById('pauseBtn').textContent = '⏸ Pause';
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
      updateDifficultyLabel();
      updateProgress();
      flashHint('New game started — saved!');
    } catch (err) {
      flashHint('Failed to load puzzle.');
    }
  }

  async function playDailyPuzzle() {
    overlay.classList.remove('show');
    gamesOverlay.classList.remove('show');
    mistakes = 0;
    mistakesEl.textContent = '0';
    undoStack = [];
    redoStack = [];
    gameCompleted = false;
    hintsUsed = 0;
    currentGameId = null;
    isPaused = false;
    document.getElementById('pauseBtn').textContent = '⏸ Pause';
    updateUndoRedoButtons();
    flashHint('Loading today\'s daily puzzle…');
    try {
      const res = await fetch('/api/daily-puzzle');
      const data = await res.json();
      puzzle = data.puzzle;
      solution = data.solution;
      difficulty = 40; // daily is always Medium
      board = puzzle.map((row) => [...row]);
      given = puzzle.map((row) => row.map((v) => v !== 0));
      notes = emptyNotes();
      selected = null;
      renderBoard();
      resetTimer();
      startTimer();
      await createGameOnServer();
      updateDifficultyLabel();
      updateProgress();
      flashHint(`📅 Daily puzzle for ${data.date} — saved!`);
    } catch (err) {
      flashHint('Failed to load daily puzzle.');
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
    startTimerInterval();
  }

  function resumeTimer() {
    timerEl.textContent = formatTime(elapsed);
    startTimerInterval();
  }

  function startTimerInterval() {
    timerInterval = setInterval(() => {
      elapsed++;
      timerEl.textContent = formatTime(elapsed);
      // Periodically save the elapsed time even without other changes
      if (elapsed % 30 === 0) {
        scheduleAutoSave();
      }
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

  let isPaused = false;

  function togglePause() {
    if (gameCompleted) return;
    isPaused = !isPaused;
    const pauseBtn = document.getElementById('pauseBtn');
    if (isPaused) {
      stopTimer();
      pauseBtn.textContent = '▶ Resume';
      flashHint('Game paused.');
    } else {
      resumeTimer();
      pauseBtn.textContent = '⏸ Pause';
      flashHint('Game resumed.');
    }
    scheduleAutoSave();
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
      paused: isPaused,
      hintsUsed,
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
    saveGameToServer(); // save immediately on every state change
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
      document.getElementById('gameIdDisplay').textContent = `#${currentGameId.substring(0, 8)}`;
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
      document.getElementById('gameIdDisplay').textContent = `#${gameId.substring(0, 8)}`;
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
    isPaused = state.paused || false;
    hintsUsed = state.hintsUsed || 0;
    document.getElementById('pauseBtn').textContent = isPaused ? '▶ Resume' : '⏸ Pause';
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
    updateDifficultyLabel();
    updateProgress();
    // Restore timer
    stopTimer();
    timerEl.textContent = formatTime(elapsed);
    if (!gameCompleted) resumeTimer();
  }

  let lastLoadedGames = [];

  async function loadGamesList() {
    try {
      const res = await fetch('/api/games?limit=50');
      const data = await res.json();
      lastLoadedGames = data.games || [];
      renderGamesList(lastLoadedGames);
      // Update button badge with count
      const btn = document.getElementById('loadGamesBtn');
      const count = lastLoadedGames.length;
      btn.textContent = count > 0 ? `📂 Load Games (${count})` : '📂 Load Games';
    } catch (err) {
      flashHint('Failed to load games list.');
    }
  }

  function renderGamesList(games) {
    // Filter by completion status
    const showCompleted = document.getElementById('filterCompleted')?.checked ?? true;
    const showInProgress = document.getElementById('filterInProgress')?.checked ?? true;
    const filtered = games.filter(g => {
      if (g.completed) return showCompleted;
      return showInProgress;
    });

    // Sort by selected criteria
    const sortBy = document.getElementById('gamesSort')?.value || 'updated';
    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === 'updated') {
        return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
      } else if (sortBy === 'progress') {
        const pa = (a.progress || '0/0').split('/').map(Number);
        const pb = (b.progress || '0/0').split('/').map(Number);
        const ra = pa[1] > 0 ? pa[0] / pa[1] : 0;
        const rb = pb[1] > 0 ? pb[0] / pb[1] : 0;
        return rb - ra;
      }
      return (b[sortBy] || 0) - (a[sortBy] || 0);
    });

    gamesTableBody.innerHTML = '';
    if (sorted.length === 0) {
      gamesEmpty.style.display = 'block';
      return;
    }
    gamesEmpty.style.display = 'none';

    const diffNames = { 30: 'Easy', 40: 'Medium', 50: 'Hard', 58: 'Expert' };
    const diffClasses = { 30: 'easy', 40: 'medium', 50: 'hard', 58: 'expert' };

    for (const game of sorted) {
      const row = document.createElement('tr');
      const diff = game.difficulty || 40;
      const diffName = diffNames[diff] || 'Medium';
      const diffClass = diffClasses[diff] || 'medium';
      const updated = game.updated_at ? new Date(game.updated_at).toLocaleString() : '—';
      const isCompleted = game.completed;
      const progress = game.progress || '—';
      const progressParts = progress.split('/');
      let progressPct = '';
      if (progressParts.length === 2 && progressParts[1] !== '0') {
        progressPct = ` (${Math.round(+progressParts[0] / +progressParts[1] * 100)}%)`;
      }

      row.innerHTML = `
        <td><span class="difficulty-badge ${diffClass}">${diffName}</span></td>
        <td>${progress}${progressPct}${isCompleted ? ' ✅' : ''}</td>
        <td>${game.mistakes || 0}</td>
        <td>${game.hintsUsed || 0}</td>
        <td>${formatTime(game.elapsed || 0)}</td>
        <td>${updated}</td>
        <td>
          <div class="game-actions">
            <button class="resume-btn" data-id="${game.game_id}">${isCompleted ? '👁 View' : '▶ Resume'}</button>
            <button class="share-btn" data-id="${game.game_id}">🔗 Share</button>
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
    gamesTableBody.querySelectorAll('.share-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          const res = await fetch(`/api/games/${btn.dataset.id}/export`);
          const data = await res.json();
          const url = `${window.location.origin}/?import=${data.share_code}`;
          await navigator.clipboard.writeText(url);
          flashHint('Share link copied to clipboard!');
        } catch (err) {
          flashHint('Failed to generate share link.');
        }
      });
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
    // Fetch and display stats summary
    fetch('/api/stats').then(r => r.json()).then(stats => {
      const el = document.getElementById('gamesStatsSummary');
      if (!el) return;
      if (stats.total_games === 0) {
        el.style.display = 'none';
        return;
      }
      el.style.display = 'flex';
      const diffNames = { easy: 'Easy', medium: 'Medium', hard: 'Hard', expert: 'Expert' };
      const bd = stats.by_difficulty || {};
      let html = `<span class="stat-item">Total: <strong>${stats.total_games}</strong></span>`;
      html += `<span class="stat-item">Completed: <strong>${stats.completed_games}</strong></span>`;
      html += `<span class="stat-item">Best: <strong>${stats.best_time || '—'}s</strong></span>`;
      for (const [key, name] of Object.entries(diffNames)) {
        const d = bd[key];
        if (d && d.total > 0) {
          html += `<span class="stat-item">${name}: <strong>${d.completed}/${d.total}</strong></span>`;
        }
      }
      el.innerHTML = html;
    }).catch(() => {});
  }

  function hideGamesModal() {
    gamesOverlay.classList.remove('show');
  }

  async function fetchBestTimes() {
    try {
      const res = await fetch('/api/best-times');
      return await res.json();
    } catch (e) {
      return {};
    }
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
      document.getElementById('gameIdDisplay').textContent = `#${game_id.substring(0, 8)}`;
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

  // Games sort
  document.getElementById('gamesSort')?.addEventListener('change', () => {
    if (lastLoadedGames.length > 0) renderGamesList(lastLoadedGames);
  });

  // Games filter
  document.getElementById('filterCompleted')?.addEventListener('change', () => {
    if (lastLoadedGames.length > 0) renderGamesList(lastLoadedGames);
  });
  document.getElementById('filterInProgress')?.addEventListener('change', () => {
    if (lastLoadedGames.length > 0) renderGamesList(lastLoadedGames);
  });

  // Help modal
  const helpOverlay = document.getElementById('helpOverlay');
  document.getElementById('helpBtn').addEventListener('click', () => {
    helpOverlay.classList.add('show');
  });
  document.getElementById('helpClose').addEventListener('click', () => {
    helpOverlay.classList.remove('show');
  });
  helpOverlay.addEventListener('click', (e) => {
    if (e.target === helpOverlay) helpOverlay.classList.remove('show');
  });

  // Theme toggle
  const themeToggle = document.getElementById('themeToggle');
  // Load saved theme
  if (localStorage.getItem('sudoku_theme') === 'light') {
    document.documentElement.classList.add('light');
    themeToggle.textContent = '☀️';
  }
  themeToggle.addEventListener('click', () => {
    const isLight = document.documentElement.classList.toggle('light');
    themeToggle.textContent = isLight ? '☀️' : '🌙';
    localStorage.setItem('sudoku_theme', isLight ? 'light' : 'dark');
  });

  document.getElementById('dailyBtn').addEventListener('click', playDailyPuzzle);
  document.getElementById('pauseBtn').addEventListener('click', togglePause);
  document.getElementById('checkBtn').addEventListener('click', checkBoard);
  document.getElementById('autoNotesBtn').addEventListener('click', autoNotes);
  document.getElementById('clearNotesBtn').addEventListener('click', clearNotes);
  document.getElementById('resetBoardBtn').addEventListener('click', resetBoard);
  document.getElementById('solveBtn').addEventListener('click', solvePuzzle);
  document.getElementById('modalNewGame').addEventListener('click', newGame);
  document.getElementById('loadGamesBtn').addEventListener('click', showGamesModal);
  document.getElementById('closeGamesBtn').addEventListener('click', hideGamesModal);
  document.getElementById('clearAllGamesBtn').addEventListener('click', async () => {
    if (!confirm('Delete ALL saved games? This cannot be undone.')) return;
    try {
      await fetch('/api/games', { method: 'DELETE' });
      currentGameId = null;
      localStorage.removeItem(STORAGE_KEY);
      loadGamesList();
      flashHint('All games deleted.');
    } catch (err) {
      flashHint('Failed to delete games.');
    }
  });

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
      updateDifficultyLabel();
      flashHint(`Difficulty set to ${DIFF_NAMES[difficulty]}. Click "New Game" to start.`);
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

    if (e.key === 'Escape') {
      if (hintCell) cancelHintPreview();
      if (gamesOverlay.classList.contains('show')) hideGamesModal();
      helpOverlay.classList.remove('show');
      return;
    }

    if (e.key >= '1' && e.key <= '9') {
      placeNumber(+e.key);
    } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
      placeNumber(0);
    } else if (e.key.toLowerCase() === 'n') {
      setMode(mode === 'final' ? 'notes' : 'final');
    } else if (e.key.toLowerCase() === 'l') {
      showGamesModal();
    } else if (e.key.toLowerCase() === 'a') {
      autoNotes();
    } else if (e.key.toLowerCase() === 'd') {
      playDailyPuzzle();
    } else if (e.key.toLowerCase() === 't') {
      document.getElementById('themeToggle').click();
    } else if (e.key === '?') {
      document.getElementById('helpOverlay').classList.toggle('show');
    } else if (e.key.toLowerCase() === 'r') {
      resetBoard();
    } else if (e.key === ' ') {
      e.preventDefault();
      togglePause();
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

  // Save game before page unload to prevent data loss
  window.addEventListener('beforeunload', () => {
    if (currentGameId && !gameCompleted) {
      // Use sendBeacon for reliable delivery during unload
      try {
        const state = serializeState();
        const blob = new Blob([JSON.stringify(state)], { type: 'application/json' });
        navigator.sendBeacon(`/api/games/${currentGameId}`, blob);
      } catch (e) {
        // Ignore — best effort
      }
    }
  });

  // Start: check for import URL param, try resuming last game, otherwise start new
  (async () => {
    // Check for shared game import via URL parameter
    const params = new URLSearchParams(window.location.search);
    const importCode = params.get('import');
    if (importCode) {
      try {
        const res = await fetch('/api/games/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ share_code: importCode }),
        });
        if (res.ok) {
          const data = await res.json();
          const game_id = data.game_id;
          const gameRes = await fetch(`/api/games/${game_id}`);
          if (gameRes.ok) {
            const state = await gameRes.json();
            restoreFromState(state);
            currentGameId = game_id;
            saveToLocalStorage();
            flashHint('Imported shared game!');
            // Clean up URL
            window.history.replaceState({}, '', window.location.pathname);
            return;
          }
        }
      } catch (e) {
        console.error('Import failed:', e);
      }
      flashHint('Failed to import shared game.');
    }

    const resumed = await tryResumeLastGame();
    if (!resumed) {
      await newGame();
    }
    // Update game count badge on startup
    fetch('/api/games?limit=1').then(r => r.json()).then(data => {
      const btn = document.getElementById('loadGamesBtn');
      const count = data.games?.length || 0;
      // Use limit=1 to check if any games exist, but get actual count from stats
      fetch('/api/stats').then(r => r.json()).then(stats => {
        const total = stats.total_games || 0;
        btn.textContent = total > 0 ? `📂 Load Games (${total})` : '📂 Load Games';
      });
    }).catch(() => {});
  })();
})();
