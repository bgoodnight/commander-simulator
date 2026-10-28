# GitHub publishing steps

This checkpoint is Git-ready. Prefer a new private GitHub repository named `commander-simulator` (it can be made public later).

After creating the repository in GitHub and connecting/granting access to the ChatGPT GitHub app, extract this archive, then from the snapshot root:

```bash
git init
git add .
git commit -m "Initial Commander Simulator checkpoint — v5 and prior history"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/commander-simulator.git
git push -u origin main
```

Never commit GitHub tokens, passwords or API keys. Validate that tests pass before pushing. GitHub tracks source changes in commits; the Google Drive dated ZIP is the independent recovery snapshot.
