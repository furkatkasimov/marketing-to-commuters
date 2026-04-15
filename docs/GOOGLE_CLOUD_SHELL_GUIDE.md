# How to Use This Project in Google Cloud Shell

Google Cloud Shell gives you a free Linux terminal in your browser. Python, Git, and pip are already installed. Nothing to set up on your Chromebook.

---

## First Time Setup

### Step 1 — Open Cloud Shell

Open Chrome and go to: **[shell.cloud.google.com](https://shell.cloud.google.com)**

Sign in with your Google account. Wait for the terminal to appear (black window at the bottom).

### Step 2 — Upload the zip file

1. Click the **three-dot menu (...)** in the top-right corner of the terminal
2. Click **Upload** then **File**
3. Select `marketing-to-commuters.zip` from your Downloads
4. Wait for it to finish

### Step 3 — Unzip and install

```bash
cd ~
unzip marketing-to-commuters.zip
cd marketing-to-commuters
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4 — Edit config.yaml

Click the **pencil icon** (Open Editor) at the top of Cloud Shell.

In the file tree on the left, open `marketing-to-commuters/config.yaml`.

Change these settings:

1. **Your state:**
```yaml
lodes:
  state: "va"    # change to your state
```

2. **Your business location** (get coordinates from Google Maps — right-click any spot):
```yaml
business:
  name: "My Dry Cleaner"
  latitude: 38.9072      # your latitude
  longitude: -77.0369    # your longitude
```

3. **Your Google Maps API key** (see README.md for how to get one):
```yaml
routing:
  google_api_key: "AIzaSyB1234..."    # paste your real key here
```

Save the file (Ctrl+S). Click **Open Terminal** to go back to the command line.

### Step 5 — Run it

```bash
python3 main.py
```

### Step 6 — Download the results

1. Click the **three-dot menu (...)**
2. Click **Download** then **File**
3. Type: `marketing-to-commuters/output/commuter_map.html`
4. Click **Download**
5. Open the downloaded file in Chrome

---

## Coming Back After Cloud Shell Goes to Sleep

Cloud Shell goes to sleep after 20 minutes of inactivity, but your files stay. When you come back:

```bash
cd ~/marketing-to-commuters
source venv/bin/activate
```

Now you can run `python3 main.py` again or make changes.

---

## Pushing to GitHub

### First time — create the repo and push

You already have a repo called `marketing-to-commuters` on GitHub. Set up git:

```bash
cd ~/marketing-to-commuters

git config --global user.name "Your Name"
git config --global user.email "your.email@gmail.com"

git init
git add .
git commit -m "Initial commit: marketing to commuters analyzer"
git remote add origin https://YOUR_USERNAME@github.com/YOUR_USERNAME/marketing-to-commuters.git
git branch -M main
git push -u origin main
```

When it asks for a password, paste your **GitHub Personal Access Token** (not your GitHub password).

To get a token: go to [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta), click Generate new token, give it Contents read/write permission, copy the token.

---

## How to Add New Files to GitHub

After you create or change files, push them to GitHub with these 3 commands:

```bash
cd ~/marketing-to-commuters
git add .
git commit -m "describe what you changed"
git push
```

**Examples:**

You edited config.yaml:
```bash
git add .
git commit -m "Updated business location to my store in Virginia"
git push
```

You added a new file like a custom dataset:
```bash
git add .
git commit -m "Added custom commuter dataset"
git push
```

You changed multiple files:
```bash
git add .
git commit -m "Changed state to Texas and increased search radius to 10 miles"
git push
```

### Check what has changed before committing

```bash
git status
```

This shows which files are new, changed, or deleted.

---

## How to Delete Old Files from Google Cloud Shell

### Delete the downloaded Census data (to free up space)

```bash
rm -f ~/marketing-to-commuters/data/*.csv.gz
```

This removes the large Census data files. You can re-download them by running `python3 main.py` again.

### Delete all output files (to start fresh)

```bash
rm -f ~/marketing-to-commuters/output/*
```

### Delete everything and start over

```bash
rm -rf ~/marketing-to-commuters
```

Then upload and unzip the zip file again (Steps 2-3 above).

### Check how much disk space you have

Cloud Shell gives you 5 GB. To check:

```bash
df -h ~
```

### See how much space the data files are using

```bash
du -sh ~/marketing-to-commuters/data/
du -sh ~/marketing-to-commuters/output/
```

---

## How to Delete a File from GitHub

If you committed a file by accident and want to remove it from GitHub:

```bash
cd ~/marketing-to-commuters
git rm filename.txt
git commit -m "Removed filename.txt"
git push
```

This deletes it from both your Cloud Shell and from GitHub.

If you want to delete it from GitHub but KEEP it on your Cloud Shell:

```bash
git rm --cached filename.txt
git commit -m "Removed filename.txt from repo"
git push
```

---

## Running for a Different State or Business

You don't need to re-download the code. Just edit `config.yaml` and run again:

```bash
cd ~/marketing-to-commuters
source venv/bin/activate
```

Edit config.yaml (pencil icon), change the state/location, save, then:

```bash
rm -f data/*.csv.gz           # delete old state data
rm -f output/*                 # delete old results
python3 main.py                # run with new settings
```

Or use command-line overrides without editing the file:

```bash
python3 main.py --state tx --year 2022 --max-routes 500
```

---

## Troubleshooting

**"No module named pandas"** — Run `source venv/bin/activate` first.

**"Google Maps API key is not set"** — Edit config.yaml and replace `YOUR_GOOGLE_API_KEY_HERE` with your real key.

**"Authentication failed" when pushing to GitHub** — Your token expired. Generate a new one at github.com/settings/tokens.

**Terminal is frozen** — Click inside the terminal and press Enter. If that doesn't work, refresh the page.

**"Disk quota exceeded"** — Run `rm -f data/*.csv.gz` to free space.

**Download fails for a state** — Not all state/year combinations exist. Try year 2020 or 2021.
