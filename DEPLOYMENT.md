# Deployment Guide - Eulerswap Rehypothecation Profitability Simulator

## Why Vercel Doesn't Work

**Vercel is for JavaScript/Node.js apps only** - it doesn't support Python applications.

Your simulator is:
- ✅ Python-based
- ✅ CLI tool + Web app (Streamlit)
- ❌ NOT compatible with Vercel

## Recommended Deployment Options

### Option 1: Streamlit Cloud (FREE & EASIEST) ⭐

**Best for:** Quick deployment, no configuration needed

**Steps:**
1. Push code to GitHub (already done ✅)
2. Go to https://streamlit.io/cloud
3. Sign in with GitHub
4. Click "New app"
5. Select repository: `Figu3/eulerswap-simulator`
6. Main file: `app.py`
7. Click "Deploy"

**Done!** Your app will be live at `https://[yourapp].streamlit.app`

**Pros:**
- ✅ Free tier available
- ✅ Zero configuration
- ✅ Auto-deploys on git push
- ✅ Python native support

**Cons:**
- ⚠️ Public by default (can upgrade for private)
- ⚠️ Resource limits on free tier

---

### Option 2: Railway (FREE Tier Available)

**Best for:** More control, private apps

**Steps:**
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `eulerswap-simulator`
5. Railway auto-detects Python

**Configuration:**
Create `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

**Pros:**
- ✅ $5/month free credit
- ✅ Private by default
- ✅ Database support
- ✅ Easy scaling

---

### Option 3: Render (FREE Tier)

**Best for:** Production deployments

**Steps:**
1. Go to https://render.com
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Connect `eulerswap-simulator`
5. Configure:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements-web.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

**Pros:**
- ✅ Free tier (750 hours/month)
- ✅ Auto SSL
- ✅ Good performance

**Cons:**
- ⚠️ Spins down after inactivity (30s wake-up)

---

### Option 4: Local Deployment

**Best for:** Testing, internal use

```bash
# Install web dependencies
pip install -r requirements-web.txt

# Run web app
streamlit run app.py

# Access at http://localhost:8501
```

---

## Files for Web Deployment

### Required Files (✅ Already Created)

1. **`app.py`** - Streamlit web interface
2. **`requirements-web.txt`** - Web dependencies
3. **`.streamlit/config.toml`** - Streamlit theme config
4. **`sim/`** - Core simulation engine (unchanged)

### Optional Files for Railway/Render

Create `Procfile`:
```bash
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
```

Create `runtime.txt` (optional):
```bash
echo "python-3.12" > runtime.txt
```

---

## Deployment Comparison

| Platform | Free Tier | Python | Auto Deploy | Private | Best For |
|----------|-----------|--------|-------------|---------|----------|
| **Streamlit Cloud** | ✅ Yes | ✅ Native | ✅ Yes | ⚠️ Upgrade | Quick demos |
| **Railway** | ✅ $5/mo | ✅ Yes | ✅ Yes | ✅ Yes | Production |
| **Render** | ✅ 750h | ✅ Yes | ✅ Yes | ✅ Yes | Production |
| **Vercel** | ❌ N/A | ❌ NO | - | - | NOT COMPATIBLE |
| **Heroku** | ❌ Paid only | ✅ Yes | ✅ Yes | ✅ Yes | Enterprise |

---

## Testing Web App Locally

```bash
# Install dependencies
pip install -r requirements-web.txt

# Run app
streamlit run app.py

# Open browser to http://localhost:8501
```

**Expected behavior:**
- Interactive web dashboard
- Parameter sliders in sidebar
- Real-time simulation results
- Interactive Plotly charts
- CSV download button

---

## Environment Variables (if needed)

For production deployments, you can set:

```bash
# On Railway/Render dashboard
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

---

## Troubleshooting

### Issue: "App not starting"
**Solution:** Check logs for missing dependencies
```bash
pip install -r requirements-web.txt
```

### Issue: "Port already in use"
**Solution:** Change port
```bash
streamlit run app.py --server.port=8502
```

### Issue: "Module not found"
**Solution:** Ensure `sim/` directory is in same folder as `app.py`

---

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] Sidebar parameters work
- [ ] "Run Simulation" button works
- [ ] Charts render properly
- [ ] CSV download works
- [ ] Try all 4 preset scenarios
- [ ] Share URL with team

---

## Recommended: Streamlit Cloud Deployment

**Quick Start (2 minutes):**

1. **Visit:** https://streamlit.io/cloud
2. **Sign in** with GitHub
3. **New app** → Select `eulerswap-simulator`
4. **Main file:** `app.py`
5. **Advanced:** Requirements file = `requirements-web.txt`
6. **Deploy!**

Your app will be live at:
```
https://eulerswap-simulator-[hash].streamlit.app
```

---

## Custom Domain (Optional)

### Streamlit Cloud
- Not available on free tier
- Upgrade to team plan for custom domains

### Railway/Render
- ✅ Free custom domains
- Add in dashboard settings
- Update DNS CNAME record

---

## Monitoring & Logs

### Streamlit Cloud
- View logs in dashboard
- Check app status
- Resource usage

### Railway/Render
- Built-in logging
- Metrics dashboard
- Alert notifications

---

## Cost Estimates

### Free Tier (Sufficient for demo/testing)
- **Streamlit Cloud:** Free (1 app)
- **Railway:** $5/month credit
- **Render:** 750 hours/month

### Paid Tier (For production)
- **Streamlit Cloud:** $20/month (team plan)
- **Railway:** Pay-as-you-go (~$5-15/month)
- **Render:** $7/month (always-on)

---

## Security Notes

For production:
- [ ] Enable authentication (Streamlit auth or custom)
- [ ] Use HTTPS (auto on all platforms)
- [ ] Set CORS policies
- [ ] Monitor usage/abuse
- [ ] Rate limit API calls (if exposing endpoints)

---

## Next Steps

1. **Deploy to Streamlit Cloud** (easiest, 2 minutes)
2. **Test** with all scenarios
3. **Share URL** with stakeholders
4. **Monitor** usage and performance
5. **Iterate** based on feedback

---

**Ready to deploy? Start with Streamlit Cloud - it's the fastest way to get your Python app online!**

GitHub Repo: https://github.com/Figu3/eulerswap-simulator
