# Troubleshooting Guide

## Quick Diagnostic

Run this first:
```bash
python3 test_deployment.py
```

This checks if everything is working locally.

---

## Common Issues

### Issue 1: "Still doesn't work" - What platform are you using?

#### ❌ If you're using **Vercel**:
**VERCEL WILL NEVER WORK** - It only supports JavaScript/TypeScript, not Python.

**Solution:** Use one of these instead:
- Streamlit Cloud (easiest)
- Railway
- Render

---

#### ✅ If you're using **Streamlit Cloud**:

**Symptom:** App fails to deploy

**Common causes:**

1. **Wrong Python version**
   ```
   Error: "No module named 'streamlit'"
   ```
   **Fix:** In deployment settings:
   - Python version: 3.9 or higher
   - Requirements file: `requirements-web.txt`

2. **Missing dependencies**
   ```
   Error: "ModuleNotFoundError: No module named 'plotly'"
   ```
   **Fix:** Ensure `requirements-web.txt` is specified in Advanced settings

3. **Wrong main file**
   ```
   Error: "Could not find app.py"
   ```
   **Fix:** Main file path should be: `app.py` (not `./app.py` or `/app.py`)

4. **Import errors**
   ```
   Error: "No module named 'sim'"
   ```
   **Fix:** Ensure entire repo is connected, not just app.py file

---

### Issue 2: Local Streamlit Won't Start

**Symptom:**
```bash
streamlit run app.py
# command not found: streamlit
```

**Solution:**
```bash
# Install dependencies
pip install -r requirements-web.txt

# OR install individually
pip install streamlit plotly pandas numpy pyyaml

# Then run
python3 -m streamlit run app.py
```

---

### Issue 3: Import Errors When Running

**Symptom:**
```
ModuleNotFoundError: No module named 'sim'
```

**Solution:**
```bash
# Make sure you're in the project root directory
cd /path/to/eulerswap-simulator

# Check directory structure
ls -la
# Should see: app.py, sim/, tests/, etc.

# Run from project root
python3 -m streamlit run app.py
```

---

### Issue 4: Simulation Fails in Web Interface

**Symptom:** Click "Run Simulation" button, but nothing happens or error appears

**Debug steps:**

1. **Check browser console** (F12)
   - Look for JavaScript errors

2. **Check Streamlit terminal output**
   - Errors will appear in terminal where you ran `streamlit run app.py`

3. **Test simulation directly:**
   ```bash
   python3 -m sim.run --config sim/config.yaml --quiet
   ```

4. **Common fix:** Parameter values out of range
   - Ensure all inputs are positive
   - Ensure fractions are between 0 and 1

---

### Issue 5: Charts Not Displaying

**Symptom:** Simulation runs but no plots appear

**Solution:**
```bash
# Install plotly
pip install plotly

# Restart Streamlit
# Ctrl+C to stop
python3 -m streamlit run app.py
```

---

### Issue 6: "This app is taking forever to load"

**Symptom:** Streamlit Cloud shows loading spinner indefinitely

**Common causes:**

1. **Build timeout**
   - Check build logs in Streamlit Cloud dashboard
   - Look for error messages

2. **Memory limit exceeded**
   - Reduce `horizon_days` in default config
   - Reduce `steps_per_day`

3. **Dependency installation failing**
   - Check if `requirements-web.txt` has correct versions
   - Remove version constraints if needed:
   ```txt
   streamlit
   plotly
   pandas
   numpy
   pyyaml
   ```

---

## Platform-Specific Instructions

### Deploying to Streamlit Cloud (Step-by-Step)

1. **Push to GitHub** (already done ✅)
   ```bash
   git push origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Click "Sign in" (top right)
   - Use your GitHub account

3. **Create New App**
   - Click "New app" button
   - Repository: `Figu3/eulerswap-simulator`
   - Branch: `main`
   - Main file path: `app.py`

4. **Advanced Settings** (click dropdown)
   - Python version: `3.9`
   - Requirements file: `requirements-web.txt`

5. **Deploy!**
   - Click "Deploy" button
   - Wait 2-5 minutes
   - App will be live at: `https://[your-app-name].streamlit.app`

**If it fails:**
- Click "Manage app" → "Logs"
- Read error messages
- Common fixes:
  - Add missing dependency to `requirements-web.txt`
  - Check Python version compatibility
  - Ensure all files are committed to GitHub

---

### Deploying to Railway

1. **Go to Railway**
   - Visit: https://railway.app
   - Sign in with GitHub

2. **New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `eulerswap-simulator`

3. **Railway auto-detects Python**
   - It finds `requirements-web.txt` and `Procfile`
   - Automatically configures deployment

4. **Add Environment Variables** (if needed)
   ```
   STREAMLIT_SERVER_PORT=8501
   ```

5. **Deploy**
   - Railway builds and deploys automatically
   - Get public URL from dashboard

---

### Deploying to Render

1. **Go to Render**
   - Visit: https://render.com
   - Sign in with GitHub

2. **New Web Service**
   - Click "New +" → "Web Service"
   - Connect `eulerswap-simulator` repo

3. **Configure**
   - Name: `eulerswap-simulator`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements-web.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

4. **Deploy**
   - Click "Create Web Service"
   - Wait 3-5 minutes
   - App will be live

---

## Still Not Working?

### Checklist

- [ ] Are you using Vercel? **→ Switch to Streamlit Cloud**
- [ ] Did you run `python3 test_deployment.py`? **→ Check output**
- [ ] Are you in the project root directory? **→ `ls` should show `app.py`**
- [ ] Did you install dependencies? **→ `pip install -r requirements-web.txt`**
- [ ] Can you run the CLI version? **→ `python3 -m sim.run --config sim/config.yaml`**
- [ ] Is GitHub repo up to date? **→ `git push origin main`**

### Get More Help

**Provide this information:**

1. **Platform:** Vercel / Streamlit Cloud / Railway / Render / Local
2. **Error message:** Copy-paste exact error
3. **Deployment logs:** If deploying to cloud platform
4. **Output of:** `python3 test_deployment.py`
5. **Python version:** `python3 --version`

**Where to ask:**
- Create GitHub issue: https://github.com/Figu3/eulerswap-simulator/issues
- Include all information above

---

## Testing Locally First

**Always test locally before deploying:**

```bash
# 1. Install dependencies
pip install -r requirements-web.txt

# 2. Test CLI version
python3 -m sim.run --config sim/config.yaml --quiet

# 3. Test web version
python3 -m streamlit run app.py

# 4. Open browser to http://localhost:8501

# 5. Try running a simulation

# 6. If all works locally → safe to deploy
```

---

## Quick Fixes

### Reset Everything

```bash
# Clean install
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-web.txt
python3 -m streamlit run app.py
```

### Force Reinstall Dependencies

```bash
pip install --force-reinstall -r requirements-web.txt
```

### Clear Streamlit Cache

```bash
streamlit cache clear
```

---

## Success Checklist

When it's working, you should see:

- ✅ Web interface loads at http://localhost:8501
- ✅ Sidebar shows parameters
- ✅ Can select preset scenarios
- ✅ "Run Simulation" button works
- ✅ Charts appear after clicking button
- ✅ Metrics show numbers
- ✅ CSV download works

If you see all of these → **deployment will work!**

---

## Platform Decision Tree

```
Are you deploying Python code?
│
├─ YES → Use Streamlit Cloud, Railway, or Render
│         ✅ These support Python
│
└─ NO (JavaScript) → Use Vercel, Netlify, or Cloudflare Pages
                      ⚠️ NOT compatible with this project
```

**This project is Python → Vercel is NOT an option**

---

## Emergency: Just Show Me The Commands

```bash
# Local testing
pip install -r requirements-web.txt
python3 -m streamlit run app.py

# Deploy to Streamlit Cloud
# → https://streamlit.io/cloud
# → New app
# → Select repo: eulerswap-simulator
# → Main file: app.py
# → Deploy

# That's it!
```
