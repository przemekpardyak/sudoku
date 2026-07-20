# 🎯 Sudoku

A modern, interactive Sudoku web application built with **Python** and **Flask**.
Generate fresh puzzles, play in your browser, and track your time and mistakes.

![Tech](https://img.shields.io/badge/Python-3.11-blue) ![Tech](https://img.shields.io/badge/Flask-3.0.3-black)

---

## ✨ Features

### Core Gameplay
- **Procedural Puzzle Generation** — every game produces a unique, solvable Sudoku via a backtracking algorithm
- **4 Difficulty Levels** — Easy, Medium, Hard, Expert (30–58 empty cells)
- **Smart Highlighting** — selecting a cell highlights its row, column, 3×3 box, and all matching numbers
- **Real-time Validation** — incorrect entries are flagged instantly in red
- **Mistake Tracker** — keeps count of wrong placements
- **Check Button** — scan the entire board for errors at any time
- **3×3 Box Dividers** — clear visual grid lines separating the nine 3×3 boxes
- **Built-in Timer** — tracks elapsed time; win screen shows your final stats
- **Modern UI** — dark glassmorphism theme, gradient accents, smooth micro-animations

### Pencil Marks (Notes)
- Toggle between **Final** (✏️) and **Notes** (📝) mode using the buttons in the right panel, or press `N`
- In **Notes mode**, clicking a number (1–9) toggles a small pencil mark in the selected cell's 3×3 mini-grid
- In **Final mode**, clicking a number places the big number. This hides the cell's pencil marks and auto-removes that same digit from pencil marks in the same row, column, and 3×3 box
- Erasing a final number reveals the preserved pencil marks again

### Smart Numpad
- Number pad buttons **auto-disable** when all 9 instances of a digit have been placed on the board
- Disabled buttons are greyed out and non-interactive
- Buttons re-enable automatically when a digit is removed

### Undo / Redo
- Full **undo/redo** support for every action: placing numbers, toggling notes, erasing, and applying hints
- Up to **200 history snapshots** tracked (board state, notes, given cells, mistakes)
- Buttons in the panel auto-disable when the stack is empty
- Starting a new game clears both stacks

### Hint (Press to Preview)
- **Press the Hint button** — a random empty cell reveals its correct number in **amber/orange** with a glowing border
- **Release the button** — the preview stays; nothing is committed yet
- **Click the amber cell** to apply the hint (committed as a permanent given)
- **Click anywhere else** or **press Escape** to dismiss the preview without applying

---

## 🎮 How to Play

1. Click any empty cell to select it (or use arrow keys to navigate).
2. Toggle between **Final** and **Notes** mode using the buttons in the right panel (or press `N`).
3. Enter a number (1–9) by:
   - Clicking the on-screen number pad, **or**
   - Pressing the corresponding key on your keyboard.
4. To erase a number, press **Backspace/Delete** or click the **⌫** button.
5. The board flags incorrect numbers in red — try again!
6. Use the tools on the right panel when needed:
   - **Check** — highlights all current errors
   - **Hint** — press to preview a correct cell, then click it to apply (or dismiss)
   - **Undo / Redo** — revert or reapply your last actions
7. Fill every cell correctly to win. Your time and mistake count are shown on the win screen.

### Using Pencil Marks (Notes Mode)

- Toggle between **Final** (✏️) and **Notes** (📝) mode using the buttons in the right panel, or press `N` on your keyboard.
- In **Notes mode**, clicking a number (1–9) toggles a small pencil mark in the selected cell's 3×3 mini-grid.
- In **Final mode**, clicking a number places the big number. This hides the cell's pencil marks and auto-removes the same digit from pencil marks in the row, column, and 3×3 box.
- Press **Backspace** or click **⌫** to erase — if the cell has a final number, only the number is removed and preserved pencil marks reappear. Pressing erase again clears all pencil marks.

### Using the Hint

1. **Press** (click and hold) the Hint button — a random empty cell lights up in amber showing its correct number.
2. **Release** the button — the preview stays on screen.
3. **Click the amber cell** to commit the hint (it becomes a permanent given and is added to the undo history).
4. To **dismiss without applying**, click anywhere else on the board or press `Escape`.

### Using Undo / Redo

- Click the **↶ Undo** button to revert your last action (or press `Ctrl+Z`)
- Click the **↷ Redo** button to reapply a reverted action (or press `Ctrl+Y` / `Ctrl+Shift+Z`)
- Works for all actions: placing numbers, toggling notes, erasing, and applying hints
- Up to 200 steps are tracked

### Difficulty Levels

| Level   | Empty Cells | Description                          |
|---------|-------------|--------------------------------------|
| Easy    | 30          | Few blanks, great for beginners       |
| Medium  | 40          | Balanced challenge                   |
| Hard    | 50          | Tough logical deductions required    |
| Expert  | 58          | Minimal clues, for seasoned players |

---

## 📁 Project Structure

```
sudoku/
├── app.py              # Flask application and API endpoints
├── sudoku.py           # Puzzle generator & backtracking solver
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── static/
│   ├── styles.css      # Dark glassmorphism theme & animations
│   └── app.js          # Game logic: rendering, input, validation, undo/redo, hints
└── templates/
    └── index.html      # Main game UI
```

### File Responsibilities

| File               | Purpose                                                              |
|--------------------|----------------------------------------------------------------------|
| `app.py`           | Flask server exposing `/` (game page) and `/api/new-game` (puzzle)  |
| `sudoku.py`        | Core logic: `generate_puzzle()`, `generate_solved_board()`, `_solve()` |
| `templates/index.html` | HTML structure: board, numpad, mode toggle, undo/redo, hint, win modal |
| `static/styles.css`    | Visual design: layout, colors, animations, disabled states, hint preview |
| `static/app.js`        | Client logic: cell selection, number/notes placement, undo/redo, numpad disable, hint preview, timer, win detection |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (tested with 3.11)
- **pip** (Python package manager)

### Standard Installation & Running

```bash
# 1. Navigate to the project folder
cd /usr/local/google/home/ppardyak/Dogfood/sudoku

# 2. (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate     # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Flask server
python3 app.py
```

The app will be available at **[http://localhost:5000](http://localhost:5000)**.

### Alternative: Virtualenv Without `ensurepip` (Corporate Environments)

If `python3 -m venv` fails because `ensurepip` is not available (common in restricted corporate environments), you can bootstrap pip manually:

```bash
# 1. Navigate to the project folder
cd /usr/local/google/home/ppardyak/Dogfood/sudoku

# 2. Create a venv without pip
python3 -m venv --without-pip venv

# 3. Bootstrap pip via get-pip.py
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
venv/bin/python3 /tmp/get-pip.py --quiet

# 4. Install Flask into the venv
venv/bin/python3 -m pip install -r requirements.txt

# 5. Start the Flask server using the venv Python
venv/bin/python3 app.py
```

### Development Mode

The server runs in debug mode by default (`app.run(debug=True)`), so changes to
Python files will auto-reload the server. Static files (JS/CSS) are served as-is —
do a hard refresh in your browser (`Ctrl+Shift+R`) after editing them.

---

## ☁️ Deploy to Google Cloud (Cloud Run + Terraform)

This app ships with Terraform code that deploys it to **Google Cloud Run** — a fully managed, serverless container platform with built-in HTTPS, automatic scaling (including scale-to-zero), and per-request billing.

### Infrastructure architecture

```mermaid
flowchart LR
    subgraph "Your machine"
        Dev["Developer"]
        Proxy["gcloud run services proxy<br/>localhost:8080"]
    end

    subgraph "Google Cloud project"
        AR["Artifact Registry<br/>sudoku-repo"]
        CB["Cloud Build"]
        CR["Cloud Run service: sudoku<br/>(gunicorn on :8080)"]
        IAM["IAM: roles/run.invoker<br/>→ user:you@example.com"]
    end

    Dev -->|"deploy.sh"| CB
    CB -->|"push image"| AR
    AR -->|"pull image"| CR
    Dev -->|"local proxy (default)"| Proxy -->|"auth token"| CR
    Dev -.->|"direct URL (needs token)"| CR
    IAM -.->|"authorizes"| CR
```

**Request flow (default — local proxy):** Browser → `localhost:8080` → `gcloud run services proxy` injects your OAuth identity token → Cloud Run verifies against the IAM `roles/run.invoker` binding → Flask app responds.

**Optional IAP flow:** Browser → Global HTTPS Load Balancer → IAP (Google login redirect) → Backend Service → Serverless NEG → Cloud Run. See [Optional: IAP in front of Cloud Run](#optional-iap-in-front-of-cloud-run) below.

### What gets created

| Resource | Terraform file | Purpose |
|----------|----------------|---------|
| Enabled APIs | [providers.tf](terraform/providers.tf) | Cloud Run, Artifact Registry, Cloud Build, Compute, IAP, and others |
| Artifact Registry repo (`sudoku-repo`) | [artifact_registry.tf](terraform/artifact_registry.tf) | Stores the Docker image |
| Cloud Run service (`sudoku`) | [cloud_run.tf](terraform/cloud_run.tf) | Serves the Flask app via gunicorn on port 8080 |
| `roles/run.invoker` IAM binding | [cloud_run.tf](terraform/cloud_run.tf) | Grants the authenticated user permission to invoke the service |
| *(optional)* IAP brand, client, LB, NEG | [iap.tf](terraform/iap.tf) | Identity-Aware Proxy + global HTTPS Load Balancer (see below) |

### Prerequisites

- A **Google Cloud project** with billing enabled
- The following CLIs installed:
  - [`gcloud`](https://cloud.google.com/sdk/docs/install) (Google Cloud CLI)
  - [`terraform`](https://developer.hashicorp.com/terraform/downloads) ≥ 1.5
  - *Docker is **not** required* — the deploy script uses Google Cloud Build for image builds
- Authenticated credentials:
  ```bash
  gcloud auth login
  gcloud auth application-default login   # Terraform uses these creds
  ```

### Install Terraform (Linux / Debian / rodete)

```bash
# 1. Fetch the latest stable version
TF_VERSION=$(curl -sL https://api.releases.hashicorp.com/v1/releases/terraform/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")

# 2. Download the Linux amd64 binary
curl -sSL -o /tmp/terraform.zip \
  "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip"

# 3. Unzip and install to ~/.local/bin (no sudo required)
unzip -o /tmp/terraform.zip -d /tmp/terraform-bin
mkdir -p "$HOME/.local/bin"
mv /tmp/terraform-bin/terraform "$HOME/.local/bin/terraform"
chmod +x "$HOME/.local/bin/terraform"
rm -rf /tmp/terraform.zip /tmp/terraform-bin

# 4. Ensure ~/.local/bin is on PATH (one-time)
grep -q 'HOME/.local/bin' "$HOME/.bashrc" \
  || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
source "$HOME/.bashrc"

# 5. Verify
terraform version
```

### Deploy — Option A: One-command (recommended)

The included [deploy.sh](deploy.sh) script orchestrates the full deploy in three phases:

| Phase | What happens |
|-------|--------------|
| 1. Bootstrap | `terraform apply` (targeted) enables APIs and creates the Artifact Registry repo |
| 2. Build | `gcloud builds submit` builds the Docker image in Cloud Build and pushes it to Artifact Registry |
| 3. Deploy | `terraform apply` (full) creates the Cloud Run service + IAM, then `gcloud run deploy` rolls out a new revision |

```bash
cd /usr/local/google/home/ppardyak/Dogfood/sudoku
PROJECT_ID=your-gcp-project ./deploy.sh
```

Optional environment variables:

| Var          | Default       | Description                              |
|--------------|---------------|------------------------------------------|
| `PROJECT_ID` | *(required)*  | GCP project ID                           |
| `REGION`     | `us-central1` | GCP region                               |
| `APP_NAME`   | `sudoku`      | Service + repo name                      |
| `IMAGE_TAG`  | `latest`      | Container image tag                     |
| `TF_ARGS`    | *(empty)*     | Extra args to `terraform apply` (e.g. `-auto-approve`) |

On success, the script prints the Cloud Run service URL and the image path.

> [!NOTE]
> The deploy script uses **Cloud Build** (not local Docker) to build the image, so you don't need Docker installed or the `docker` group permission.

### Deploy — Option B: Manual step-by-step

```bash
# 1. Set your project
gcloud config set project your-gcp-project
gcloud config set compute/region us-central1

# 2. Apply Terraform — Phase 1: APIs + Artifact Registry repo
cd terraform
terraform init
terraform apply \
  -var="project_id=your-gcp-project" \
  -target=google_project_service.enabled_apis \
  -target=google_artifact_registry_repository.app_repo

# 3. Build & push the image via Cloud Build (no local Docker needed)
IMAGE="us-central1-docker.pkg.dev/your-gcp-project/sudoku-repo/sudoku:latest"
gcloud builds submit .. --tag="$IMAGE"

# 4. Apply Terraform — Phase 2: Cloud Run service + IAM
terraform apply -var="project_id=your-gcp-project"

# 5. Deploy a fresh revision pointing at the pushed image
gcloud run deploy sudoku \
  --image="$IMAGE" \
  --region=us-central1 \
  --port=8080 \
  --memory=512Mi --cpu=1 \
  --concurrency=80 --min-instances=0 --max-instances=10

# 6. Get the URL
gcloud run services describe sudoku --region=us-central1 --format='value(status.url)'
```

### Configuration variables

All variables are in [terraform/variables.tf](terraform/variables.tf). Override with `-var` flags or via a `terraform.tfvars` file (see [terraform.tfvars.example](terraform/terraform.tfvars.example)):

```bash
terraform apply \
  -var="project_id=your-gcp-project" \
  -var="region=europe-west1" \
  -var="min_instance_count=1" \
  -var="memory=1Gi"
```

| Variable                  | Default       | Description                                  |
|---------------------------|---------------|----------------------------------------------|
| `project_id`              | *(required)*  | GCP project ID                               |
| `region`                  | `us-central1` | GCP region for all resources                 |
| `app_name`                | `sudoku`      | Logical name prefix for resources            |
| `image_tag`               | `latest`      | Container image tag to deploy               |
| `service_account_email`   | `null`        | Custom SA for the Cloud Run revision         |
| `concurrency`             | `80`          | Max concurrent requests per instance         |
| `max_instance_count`      | `10`          | Max container instances                      |
| `min_instance_count`      | `0`           | Min instances (0 = scale to zero)            |
| `memory`                  | `512Mi`       | Memory limit per instance                    |
| `cpu`                     | `1`           | CPU limit per instance                       |
| `allow_unauthenticated`   | `true`        | If true, grants the current gcloud user `run.invoker` (public `allUsers` is blocked by most org policies) |
| `invoker_members`         | `[]`          | Explicit IAM members to grant `run.invoker`. Defaults to the current gcloud user. Use `["allUsers"]` for public access (if your org policy allows it). |
| `enable_iap`              | `false`       | If true, creates a global HTTPS Load Balancer with IAP in front of Cloud Run. See [Optional: IAP](#optional-iap-in-front-of-cloud-run). |
| `iap_lb_scheme`           | `EXTERNAL`    | LB scheme for IAP. Use `EXTERNAL` (classic) or `EXTERNAL_MANAGED` (newer). Must be allowed by your org policy. |
| `iap_allowed_users`       | `[]`          | IAM members allowed through IAP. Defaults to the current gcloud user. |
| `domain`                  | `null`        | Optional custom domain for the IAP Load Balancer frontend. |

### Outputs

After `terraform apply`, the following are printed:

| Output                    | Description                                |
|---------------------------|--------------------------------------------|
| `cloud_run_service_url`  | Direct HTTPS URL of the Cloud Run service (requires auth token — not browser-accessible) |
| `cloud_run_service_name` | Name of the Cloud Run service (`sudoku`)   |
| `artifact_registry_image`| Full image path Cloud Run pulls from       |
| `cloud_run_proxy_command`| The `gcloud run services proxy` command to start a local authenticated proxy |
| `load_balancer_ip`       | Global static IP of the IAP LB. `null` when IAP is disabled. |
| `iap_protected_url`      | HTTPS URL protected by IAP. `null` when IAP is disabled. |

### Accessing the app

The Cloud Run service requires authentication on every request. Your org policy likely blocks `allUsers` and `allAuthenticatedUsers`, so the service is **not directly accessible in a browser**. Use one of the methods below.

#### Method 1: Local proxy (default, no extra infra)

`gcloud run services proxy` starts a local server that injects your OAuth identity token into every request:

```bash
gcloud run services proxy sudoku \
  --region=us-central1 \
  --project=your-gcp-project \
  --port=8080
```

Then open [http://localhost:8080](http://localhost:8080) in your browser. Keep the terminal open while you play. Stop with `Ctrl+C`.

> [!TIP]
> If the proxy command is missing, install the component: `sudo apt-get install -y google-cloud-cli-cloud-run-proxy`

#### Method 2: Optional — IAP in front of Cloud Run

For a permanent, browser-friendly URL with a Google login flow, enable Identity-Aware Proxy (IAP). This creates a global HTTPS Load Balancer with IAP in front of Cloud Run.

```bash
terraform apply \
  -var="project_id=your-gcp-project" \
  -var="enable_iap=true" \
  -var="iap_lb_scheme=EXTERNAL"          # or EXTERNAL_MANAGED
```

> [!WARNING]
> IAP requires an external HTTP/HTTPS Application Load Balancer. If your org policy (`compute.restrictLoadBalancerCreationForTypes`) blocks `EXTERNAL_HTTP_HTTPS` and `EXTERNAL_MANAGED_HTTP_HTTPS`, IAP creation will fail. Check with:
> ```bash
> gcloud org-policies describe compute.restrictLoadBalancerCreationForTypes \
>   --project=your-gcp-project --effective
> ```
> If blocked, request an org policy exception or use the local proxy (Method 1).

### Finding deployment status

After deploying, use these commands to check the state of your infrastructure:

#### Cloud Run service status

```bash
# Service URL, region, and condition (Ready/Failed)
gcloud run services describe sudoku \
  --region=us-central1 \
  --project=your-gcp-project \
  --format='value(status.url, status.conditions[0].type, status.conditions[0].state)'

# List all revisions (deploy history)
gcloud run revisions list \
  --service=sudoku \
  --region=us-central1 \
  --project=your-gcp-project

# Current traffic split
gcloud run services describe sudoku \
  --region=us-central1 \
  --project=your-gcp-project \
  --format='value(status.traffic)'
```

#### IAM policy (who can invoke)

```bash
gcloud run services get-iam-policy sudoku \
  --region=us-central1 \
  --project=your-gcp-project \
  --format='table(bindings.role, bindings.members)'
```

#### Container image in Artifact Registry

```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/your-gcp-project/sudoku-repo \
  --format='table(name, version, update_time)'
```

#### Recent logs

```bash
# Last 50 log lines from the Cloud Run service
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=sudoku" \
  --limit=50 \
  --format='value(timestamp, textPayload)'

# Tail logs in real-time
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=sudoku"
```

#### Terraform state

```bash
cd terraform

# List all resources tracked by Terraform
terraform state list

# Show the current plan (what would change if you ran apply)
terraform plan -var="project_id=your-gcp-project"

# Show all output values
terraform output
```

#### Full deployment health check (one-liner)

```bash
gcloud run services describe sudoku --region=us-central1 --project=your-gcp-project \
  --format='value(status.url, status.conditions[0].type, status.conditions[0].state, status.conditions[0].message)'
```

### Teardown

To remove everything Terraform created (service, repo, IAM binding, and optionally the IAP LB):

```bash
cd terraform
terraform destroy -var="project_id=your-gcp-project"
```

> [!NOTE]
> Terraform state is stored locally by default. For production use, add a [GCS backend](https://developer.hashicorp.com/terraform/language/backend/gcs) to `terraform/providers.tf` so state is shared and versioned centrally.

---

## ⌨️ Keyboard Shortcuts

| Key               | Action                          |
|-------------------|---------------------------------|
| `1` – `9`         | Place the number in the selected cell (final or notes mode) |
| `Backspace` / `Delete` / `0` | Erase the selected cell       |
| `N`               | Toggle between Final and Notes mode |
| `Ctrl+Z`          | Undo last action                |
| `Ctrl+Y` or `Ctrl+Shift+Z` | Redo last undone action  |
| `Escape`          | Dismiss hint preview            |
| `↑` `↓` `←` `→`   | Move the selection between cells |

---

## 🔌 API Reference

### `GET /`

Returns the main HTML game page.

### `GET /api/new-game?difficulty=<int>`

Generates a new Sudoku puzzle and its solution.

| Parameter     | Type | Default | Description                                   |
|---------------|------|---------|-----------------------------------------------|
| `difficulty`  | int  | `40`    | Number of cells to remove (30–58 recommended) |

**Response:**

```json
{
  "puzzle": [[6, 0, 1, ...], ...],
  "solution": [[6, 9, 1, ...], ...]
}
```

- `puzzle`: 9×9 grid where `0` represents an empty cell
- `solution`: 9×9 grid with the complete, solved board

---

## 🧠 How Puzzle Generation Works

The generator in [`sudoku.py`](sudoku.py) uses a classic **backtracking algorithm**:

1. **Fill diagonal 3×3 boxes** with random permutations of 1–9.
   (Diagonal boxes don't share rows/columns, so they can be filled independently.)
2. **Solve the rest** via backtracking to produce a fully solved board.
3. **Remove cells** randomly up to the requested difficulty count.

This guarantees every generated puzzle has a valid unique solution.

---

## 🛠️ Troubleshooting

<details>
<summary><b>ModuleNotFoundError: No module named 'flask'</b></summary>

Flask isn't installed. Run:

```bash
pip install -r requirements.txt
```

If pip is unavailable, install pip first:

```bash
python3 -m ensurepip --upgrade
```

If `ensurepip` is not available, use the alternative venv method in [Getting Started](#alternative-virtualenv-without-ensurepip-corporate-environments).

</details>

<details>
<summary><b>"The virtual environment was not created successfully because ensurepip is not available"</b></summary>

On Debian/Ubuntu systems, either install the venv package:

```bash
apt install python3.11-venv
```

Or create the venv without pip and bootstrap it manually:

```bash
python3 -m venv --without-pip venv
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
venv/bin/python3 /tmp/get-pip.py --quiet
venv/bin/python3 -m pip install -r requirements.txt
```

</details>

<details>
<summary><b>Port 5000 already in use</b></summary>

Another process is using the port. Either stop it or change the port in `app.py`:

```python
app.run(debug=True, host="0.0.0.0", port=5001)
```

</details>

<details>
<summary><b>Corporate environment blocking pip installs</b></summary>

If you're behind a package install restriction (e.g., Corp Airlock), either:
- Use a pre-approved virtual environment image, or
- Request an exception at your organization's package governance portal.
- Alternatively, bootstrap pip via `get-pip.py` inside a `--without-pip` venv (see [Getting Started](#alternative-virtualenv-without-ensurepip-corporate-environments)).

</details>

<details>
<summary><b>Changes not showing in browser</b></summary>

Static files (JS/CSS) are cached by the browser. Do a **hard refresh**:
- **Windows/Linux**: `Ctrl+Shift+R`
- **Mac**: `Cmd+Shift+R`

</details>

---

## 📝 License

This project is provided as-is for educational and personal use.

---

<p align="center">Built with 🧡 using Flask</p>
