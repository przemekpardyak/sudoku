# Load Testing Proposal — Sudoku Web App

> **Status:** Proposed — awaiting review before implementation

---

## 1. Goals

- Validate the app handles real-world concurrent user load
- Identify performance bottlenecks (CPU, memory, Firestore latency)
- Determine Cloud Run scaling limits and optimal configuration
- Establish baseline metrics for regression detection

---

## 2. Representative Workload

The workload should mimic real user behavior. Based on the app's API surface, here's the user journey:

### 2.1 User Journey (per simulated user)

| Step | API Call | Method | Notes |
|------|----------|--------|-------|
| 1. Login | `/api/login` | POST | testuser/password |
| 2. Load page | `/` | GET | HTML render |
| 3. New game | `/api/new-game` | GET | Generates puzzle (CPU-heavy) |
| 4. Save game | `/api/games/{id}` | PUT | Initial save |
| 5. Place numbers | `/api/games/{id}` | PUT | 5-10 saves over 30s |
| 6. Get hint | `/api/hint` | POST | Solver runs (CPU-heavy) |
| 7. Validate | `/api/validate` | POST | Board validation |
| 8. Check stats | `/api/stats` | GET | Firestore read |
| 9. List games | `/api/games` | GET | Firestore read |

### 2.2 Load Profile

| Scenario | Users | Duration | Description |
|----------|-------|----------|-------------|
| Smoke | 1 | 1 min | Basic health check |
| Light | 10 | 5 min | Normal traffic |
| Moderate | 50 | 10 min | Peak hours |
| Stress | 200 | 5 min | Find breaking point |
| Spike | 0→100→0 | 5 min | Sudden traffic burst |

### 2.3 Key Metrics to Gather

| Metric | Source | Target |
|--------|--------|--------|
| Response time (p50, p95, p99) | Locust | < 200ms p95 |
| Error rate | Locust | < 1% |
| Requests/sec | Locust | Track max sustained |
| CPU utilization | Cloud Run metrics | < 80% |
| Memory utilization | Cloud Run metrics | < 70% |
| Instance count | Cloud Run metrics | Track scaling behavior |
| Firestore read/write ops | Firestore dashboard | Track cost |
| Cold start frequency | Cloud Run logs | Track impact |

---

## 3. Proposed Tool: Locust

### Why Locust?
- Python-based (matches our stack, easy to extend)
- Supports realistic user journeys with think time
- Distributed for high-concurrency tests
- Web UI for real-time monitoring
- Can run from inside GCP (Cloud Run or GCE)

### Alternatives Considered

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **Locust** | Python, flexible, web UI | Needs setup | ✅ Recommended |
| k6 | JS-based, good CLI | JS not in our stack | Skip |
| Cloud Run load testing | No setup | Limited scenarios | For basic smoke |
| Artillery | YAML config, easy | Less flexible | Backup option |
| JMeter | Mature, GUI | Java, heavy | Overkill |

---

## 4. Architecture

```
┌─────────────────────────────────────────────────┐
│  GCP Project: ppardyak-new-project               │
│                                                   │
│  ┌─────────────┐     ┌─────────────────────────┐ │
│  │  Locust     │────▶│  Cloud Run (sudoku)     │ │
│  │  Master     │     │  https://sudoku-...     │ │
│  │  (GCE/Cloud │     │  ↕ Firestore            │ │
│  │   Run)      │     │                         │ │
│  └─────────────┘     └─────────────────────────┘ │
│         │                                         │
│         ▼                                         │
│  ┌─────────────┐                                  │
│  │  Locust     │  (optional: distributed workers)│
│  │  Workers    │                                  │
│  └─────────────┘                                  │
└─────────────────────────────────────────────────┘
```

### 4.1 Execution Environment

**Option A: Cloud Run (Recommended)**
- Deploy Locust as a Cloud Run service
- No infrastructure to manage
- Can scale workers for high load
- Access to internal Cloud Run networking

**Option B: GCE VM**
- More control, can install monitoring agents
- Persistent between runs
- Good for long-running tests

**Option A is recommended** — simpler, matches our Cloud Run deployment model.

---

## 5. Implementation Plan

### Phase 1: Create Locust Load Test (Day 1)

1. Create `loadtest/locustfile.py` — simulated user journey
2. Create `loadtest/Dockerfile` — Locust container
3. Create `loadtest/deploy.sh` — deploy Locust to Cloud Run
4. Test smoke scenario locally

### Phase 2: Run Baseline Tests (Day 1)

1. Deploy Locust to `ppardyak-new-project`
2. Run smoke + light scenarios
3. Collect metrics (Locust stats + Cloud Run dashboard)
4. Document baseline performance

### Phase 3: Stress Test (Day 2)

1. Run moderate + stress + spike scenarios
2. Identify bottlenecks
3. Tune Cloud Run config (max instances, concurrency, CPU/memory)
4. Document findings and recommendations

---

## 6. Locust User Journey (Draft)

```python
from locust import HttpUser, task, between
import random

class SudokuUser(HttpUser):
    wait_time = between(1, 5)  # Think time between requests

    def on_start(self):
        """Login at the start of each simulated user session."""
        self.client.post("/api/login", json={
            "username": "testuser",
            "password": "password"
        })
        self.game_id = None

    @task(1)
    def new_game(self):
        """Start a new game."""
        with self.client.get("/api/new-game") as resp:
            data = resp.json()
            self.puzzle = data["puzzle"]
            self.solution = data["solution"]

    @task(5)
    def save_game(self):
        """Save game state."""
        if not self.game_id:
            # Create game first
            resp = self.client.post("/api/games", json={
                "puzzle": self.puzzle,
                "solution": self.solution,
                "board": self.puzzle,
                "difficulty": 30,
            })
            self.game_id = resp.json().get("game_id")
            return

        # Save progress
        board = [row[:] for row in self.puzzle]
        # Simulate placing a number
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    board[r][c] = random.randint(1, 9)
                    break
            break

        self.client.put(f"/api/games/{self.game_id}", json={
            "board": board,
        })

    @task(2)
    def get_hint(self):
        """Request a hint (CPU-heavy)."""
        if hasattr(self, "puzzle"):
            self.client.post("/api/hint", json={"board": self.puzzle})

    @task(2)
    def validate(self):
        """Validate the board."""
        if hasattr(self, "puzzle"):
            self.client.post("/api/validate", json={"board": self.puzzle})

    @task(1)
    def view_stats(self):
        """View player stats."""
        self.client.get("/api/stats")

    @task(1)
    def list_games(self):
        """List saved games."""
        self.client.get("/api/games")
```

---

## 7. Metrics Collection

### 7.1 Locust Built-in
- Response times (p50, p95, p99)
- RPS (requests per second)
- Failure rate
- Per-endpoint breakdown

### 7.2 Cloud Run Metrics
```bash
# Get Cloud Run metrics
gcloud run services describe sudoku \
  --project=ppardyak-new-project \
  --region=us-central1 \
  --format="value(status)"
```

### 7.3 Cloud Monitoring (optional)
- Enable Cloud Monitoring on the project
- Create dashboards for:
  - Request latency
  - CPU/Memory utilization
  - Instance count over time
  - Firestore operation count

---

## 8. Expected Output

After each load test run:

1. **Locust stats summary** — CSV/JSON with per-endpoint metrics
2. **Screenshot of Locust web UI** — charts over time
3. **Cloud Run scaling log** — instance count during test
4. **Recommendations** — config changes (max instances, CPU, memory)

---

## 9. Files to Create

```
loadtest/
├── locustfile.py      # User journey definition
├── Dockerfile         # Locust container image
├── deploy.sh          # Deploy Locust to Cloud Run
├── run_local.sh       # Run Locust locally for smoke test
└── README.md          # How to run load tests
```

---

## 10. Cost Considerations

- Locust on Cloud Run: ~$0 (minimal compute, short runs)
- Target app scaling: max 10 instances for stress test
- Firestore: ~100K reads/writes per moderate test run
- Estimated cost per test run: < $1

---

## Next Steps

1. Review this proposal
2. Approve approach (Locust on Cloud Run)
3. Implement Phase 1 (locustfile + Dockerfile)
4. Deploy and run smoke test
5. Iterate on scenarios based on results
