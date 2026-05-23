# Hugging Face Space deployment

This directory contains the assets to deploy the Replacement Scout backend
to a [Hugging Face Space](https://huggingface.co/spaces).

Two files live here; both need to be **copied to the root of your HF Space
repo** (a separate repo from this one):

- `Dockerfile` — copies `backend/`, `src/`, and `models/` into the image
  and runs `uvicorn` on port 7860.
- `.dockerignore` — leaves `models/gp2/` *in* the build context (the Space
  image is self-contained, unlike the local docker-compose stack which
  mounts models as a volume).

## One-time setup

1. **Create the Space** at <https://huggingface.co/new-space>. Pick:
   - SDK: **Docker**
   - Template: **Blank**
   - Hardware: **CPU Basic** is enough (measured warm-engine RSS is
     ~600 MB; the 16 GB / 2 vCPU free tier has plenty of headroom). The
     free tier may sleep after inactivity — upgrade to CPU Upgrade if
     reliability matters for your demo.

2. **Clone the Space repo locally** (use the HTTPS URL the Space page
   shows):

   ```powershell
   git clone https://huggingface.co/spaces/<your-username>/<your-space-name>
   cd <your-space-name>
   ```

3. **Copy the deploy assets and code** from this repo into the Space repo
   root. Replace `<this-repo>` with the path to this repo on your
   machine:

   ```powershell
   # The Dockerfile and .dockerignore go to the Space root
   Copy-Item <this-repo>\hf-space\Dockerfile     .\Dockerfile
   Copy-Item <this-repo>\hf-space\.dockerignore  .\.dockerignore

   # The application code and model artifacts
   Copy-Item <this-repo>\backend  .\backend  -Recurse
   Copy-Item <this-repo>\src      .\src      -Recurse
   Copy-Item <this-repo>\models   .\models   -Recurse
   ```

4. **Set up Git LFS** for the model files (~152 MB of runtime artifacts)
   AND the static photos/logos (~150 MB if fully populated). Pure-`git`
   would push these as ordinary blobs and blow up the Space's storage
   quota:

   ```powershell
   git lfs install
   # Model artifacts
   git lfs track "models/**"
   git lfs track "*.model"
   git lfs track "*.npz"
   git lfs track "*.jsonl"
   # Static photos and team logos (so deployed UI shows real photos,
   # not just the initials fallback)
   git lfs track "backend/app/static/players/*.jpg"
   git lfs track "backend/app/static/teams/*.png"
   git add .gitattributes
   ```

5. **Commit and push** to deploy:

   ```powershell
   git add .
   git commit -m "Initial Space deployment"
   git push
   ```

The Space builds automatically; the first build takes 5–10 min. Once
ready, the public URL (`https://<your-username>-<your-space-name>.hf.space`)
is what you'll set as `NEXT_PUBLIC_API_URL` in Vercel.

## Sanity check

After build completes:

```
curl https://<your-username>-<your-space-name>.hf.space/api/health
```

Expected: `{"status":"ok","engine_loaded":true,"engine_state":"ready",...}`.
First call may be slow (5–15 s) if the Space was sleeping.

## Updates

To push new backend code, just re-copy `backend/` + `src/` and `git push`.
You only re-copy `models/` if the model artifacts themselves changed.
