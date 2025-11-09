# Streamlit Deployment with Lightweight Data

## 🎯 Problem Solved
Your kilter.db is 182MB, too large for GitHub. This solution creates a lightweight package (~5-15MB) with only the data needed for visualization.

## 📋 Step-by-Step Guide

### Step 1: Prepare Lightweight Data (In Colab)

1. **Upload `prepare_streamlit_data.py` to your Colab**

2. **Run it:**
```python
# This will create streamlit_data.zip
from prepare_streamlit_data import prepare_streamlit_data

prepare_streamlit_data(
    zip_path='/content/drive/MyDrive/climbs/gnn_results.zip',
    db_path='/content/drive/MyDrive/climbs/kilter.db',
    output_path='/content/streamlit_data.zip'
)
```

3. **Download the output:**
   - You'll get `streamlit_data.zip` (~5-15MB depending on your data)
   - This contains everything Streamlit needs!

### Step 2: Create GitHub Repository

1. Go to github.com → "New repository"
2. Name it (e.g., `climbing-routes-app`)
3. Make it **Public**
4. Create repository

### Step 3: Upload Files to GitHub

Upload these 3 files:
- ✅ `streamlit_app.py`
- ✅ `requirements.txt`
- ✅ `streamlit_data.zip` (the one you just created!)

That's it! No more database file needed!

### Step 4: Deploy to Streamlit

1. Go to https://share.streamlit.io
2. Click "New app"
3. Sign in with GitHub
4. Select your repository
5. Main file: `streamlit_app.py`
6. Click "Deploy"

Wait 2-3 minutes and you're live! 🎉

## 📦 What's in streamlit_data.zip?

The lightweight package contains:
- **routes.pkl**: Route metadata (names, grades, embeddings, etc.)
- **holds.pkl**: Hold positions for each route
- **board_geometry.pkl**: Board layout for visualization

## 📊 Size Comparison

| File | Original | Lightweight | Savings |
|------|----------|-------------|---------|
| Database | 182 MB | - | - |
| GNN Results | ~50 MB | - | - |
| **Final Package** | **232 MB** | **~10 MB** | **95%+** |

## 🚀 Updating Your App

If you change your data:
1. Re-run `prepare_streamlit_data.py` in Colab
2. Download new `streamlit_data.zip`
3. Upload to GitHub (replacing old file)
4. Streamlit auto-deploys!

## 💡 Benefits of This Approach

✅ **Small file size** - Fits easily in GitHub (under 100MB limit)
✅ **Fast loading** - Pre-processed data loads instantly
✅ **No database** - No SQL queries needed in Streamlit
✅ **Mobile friendly** - Optimized data structure
✅ **Easy updates** - Just regenerate and upload

## ⚙️ Technical Details

### What prepare_streamlit_data.py Does:

1. Loads your full GNN results
2. Filters to routes with difficulty >= 15
3. Computes 2D embeddings with PaCMAP
4. Extracts ONLY the board geometry needed (not entire DB)
5. Packages everything efficiently

### Data Optimization:

- Routes: Only keeps columns needed for display
- Holds: Only x, y, role (no extra metadata)
- Board: Only layouts actually used by routes
- Format: Pickle for fast loading

## 🐛 Troubleshooting

**prepare_streamlit_data.py fails?**
- Check file paths to gnn_results.zip and kilter.db
- Make sure you have enough RAM in Colab

**streamlit_data.zip still too large?**
- Increase difficulty filter (line 29 in prepare script)
- Reduce number of routes included

**Streamlit app won't load data?**
- Verify streamlit_data.zip is in repo root
- Check Streamlit logs for error messages

## 🎨 File Structure

Your GitHub repo should look like:
```
your-repo/
├── streamlit_app.py          ← Main app
├── requirements.txt          ← Dependencies  
└── streamlit_data.zip        ← Lightweight data package
```

That's only 3 files! Simple and clean! 🎯
