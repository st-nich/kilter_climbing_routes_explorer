# Deploying Climbing Route Explorer to Streamlit

## 📦 What You Need to Upload

Your GitHub repository should contain:
1. `streamlit_app.py` (the main app)
2. `requirements.txt` (Python dependencies)
3. `gnn_results.zip` (your data - 13MB is fine!)
4. `kilter.db` (your database file)

## 🚀 Deployment Steps

### Option 1: Deploy via Streamlit Community Cloud (Free & Easy)

1. **Create a GitHub Repository**
   - Go to github.com
   - Click "New repository"
   - Name it (e.g., `climbing-routes-app`)
   - Make it **Public**
   - Create repository

2. **Upload Your Files**
   - Click "Add file" → "Upload files"
   - Upload all 4 files listed above
   - Commit changes

3. **Deploy to Streamlit**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Sign in with GitHub
   - Select your repository
   - Main file path: `streamlit_app.py`
   - Click "Deploy"!

4. **Access Your App**
   - Wait 2-3 minutes for deployment
   - You'll get a URL like: `https://username-climbing-routes-app.streamlit.app`
   - Open it on your iPhone Safari!

### Option 2: Test Locally First

```bash
# Install Streamlit
pip install streamlit plotly pandas numpy pacmap

# Run locally
streamlit run streamlit_app.py
```

## 📱 Mobile Features

The Streamlit version:
- ✅ Automatically mobile-responsive
- ✅ Works perfectly on iPhone Safari
- ✅ Sidebar filters collapse on mobile
- ✅ Touch-friendly interactions
- ✅ Free hosting forever
- ✅ Easy to update (just push to GitHub)

## 💾 File Size Limits

Streamlit Community Cloud:
- ✅ App size: Up to 1GB (your 13MB is perfect!)
- ✅ Memory: 1GB RAM
- ✅ Free tier includes everything you need

## 🔄 Updating Your App

Just push changes to GitHub - Streamlit auto-deploys!

```bash
# Make changes to streamlit_app.py
# Then commit and push
git add .
git commit -m "Updated app"
git push
```

## 🎨 Customization Tips

In `streamlit_app.py`, you can easily:
- Change colors in the CSS section (line 22)
- Adjust plot heights (line 25)
- Modify filter defaults (lines 123-145)
- Add more features!

## ⚠️ Important Notes

1. **File paths**: Make sure your data files (`gnn_results.zip` and `kilter.db`) are in the same directory as `streamlit_app.py`

2. **Data loading**: The `@st.cache_data` decorator ensures data only loads once (fast!)

3. **Click interactions**: Streamlit uses `on_select` for plot clicks (works great on mobile)

## 🆘 Troubleshooting

**App won't deploy?**
- Check that all 4 files are in your repo
- Verify `requirements.txt` is correct
- Check Streamlit logs for errors

**Slow loading?**
- The first load takes ~10-20 seconds (data processing)
- After that, it's cached and instant

**Not mobile-friendly?**
- Make sure you're using the latest version from this file
- The CSS should auto-adjust for mobile

## 🎁 Bonus Features

Once deployed, you can:
- Share the URL with anyone
- Access from any device
- Update anytime via GitHub
- Monitor usage in Streamlit dashboard
