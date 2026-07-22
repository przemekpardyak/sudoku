# Sudoku Tutorial System — Product Specification

> **Version:** 0.1 — initial framework
> **Last Updated:** 2026-07-22

---

## 1. Overview

The Tutorial System is a comprehensive learning platform integrated into the Sudoku web app. It teaches players of all skill levels — from complete beginners to expert solvers — through interactive lessons, guided practice on real boards, and a reference library of techniques.

### Design Principles
1. **Learn by doing** — every lesson includes interactive practice on a real Sudoku board
2. **Progressive disclosure** — techniques build on each other, complexity revealed gradually
3. **Contextual help** — in-game hints can offer tutorial-style explanations
4. **Immediate feedback** — correct mistakes instantly during learning
5. **Achievement-based progression** — unlock harder content as skills improve

### User Modes
- **Pure Play**: Standard game, no tutorial interference
- **Tutorial Mode**: Guided lessons with step-by-step instructions and practice puzzles
- **Blended**: In-game contextual help — when stuck, user can access relevant technique tips

---

## 2. Tutorial Content Structure

### 2.1 Skill Levels

| Level | Target Audience | Techniques |
|-------|----------------|------------|
| **Beginner** | Never played Sudoku | Rules, Scanning, Naked Singles, Hidden Singles |
| **Intermediate** | Knows basics, wants to improve | Naked Pairs/Triples, Hidden Pairs, Pointing Pairs, Box-Line |
| **Advanced** | Comfortable with intermediates | X-Wing, Swordfish, XY-Wing, Unique Rectangle |
| **Expert** | Wants mastery | ALS, Death Blossom, Pattern Overlay, BUG, Maximum |

### 2.2 Lesson Structure

Each lesson follows this pattern:
1. **Introduction** — what the technique is, why it's useful
2. **Visual demonstration** — show the pattern on a practice board
3. **Guided practice** — user finds the pattern with hints
4. **Independent practice** — user solves without hints
5. **Completion** — lesson marked complete, progress saved

---

## 3. Architecture

*Detailed architecture will be documented as batches are implemented.*

### 3.1 Content Storage
- Tutorial content stored as structured JSON files
- Each lesson has: metadata, instructions, practice puzzles, validation rules

### 3.2 Progress Tracking
- Server-side storage (Firestore) — requires login
- Tracks: lessons completed, practice attempts, technique mastery level

### 3.3 Delivery
- Tutorial overlay on existing game board
- Reference library as separate section/modal

---

## 4. Implementation Status

| Batch | Feature | Status |
|-------|---------|--------|
| 1 | Tutorial framework + Rules lesson | ✅ Done |
| 2 | E2E tests + Intermediate lessons | ✅ Done |
| 3 | Advanced + Expert lessons | ✅ Done |
| 4 | Technique tips + Stats + In-game help | ✅ Done |
| 5 | Progress dashboard in sidebar | ✅ Done |
| 6 | Reference library with tabs | ✅ Done |
| 7 | Achievements system | ✅ Done |
| 8 | Practice puzzles for advanced techniques | 🚧 Next |
| 9 | Tutorial-to-game integration | ⏳ Pending |
| 10 | Streak tracking + daily challenges | ⏳ Pending |
