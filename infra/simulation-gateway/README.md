# Password-gated new simulations

The GitHub Pages Deck Lab remains publicly viewable. Only requesting a new
simulation requires a shared password. Password and GitHub credential live in
encrypted Cloudflare Worker secrets, not browser JavaScript or repository files.

## Setup, performed by the account owner

1. Merge and verify the new deep-simulations.yml workflow on main.
2. Create an expiring fine-grained GitHub token restricted to this one repo,
   with Actions: Read and write permission. Never put it in the website.
3. Adjust ALLOWED_ORIGIN in wrangler.toml to your actual Pages origin
   (scheme and host, not a whole page URL). The default is the standard
   project Pages hostname; update it if using a custom domain.
4. Deploy in an authorized Cloudflare environment:

       cd infra/simulation-gateway
       npx wrangler login
       npx wrangler secret put RUN_PASSWORD
       npx wrangler secret put GITHUB_TOKEN
       npx wrangler deploy

   Choose a unique random password of at least 16 characters. Enter the
   password and GitHub token only in the secret prompts, never in this chat.
5. Give the UI workstream the deployed Worker URL. Add a Run simulation
   button to Results. The browser prompts only at run time, submits JSON
   by POST to the Worker URL plus /run, then clears the password field.

   Example browser request body (illustration, no actual password):

       {
         "password": "<entered shared password>",
         "deck": "necron_dynasties",
         "scenario": "mixed",
         "seeds": 100,
         "rounds": 30,
         "start_seed": 0,
         "pilot_style": "adaptive",
         "provisional_mode": "safe"
       }

6. Test with 2 seeds and 3 rounds. HTTP 202 indicates a queued dispatch,
   not a completed job. The job saves an immutable downloadable artifact,
   checks the published UI schema, and launches the existing Pages rebuild.

## Safeguards

The Worker accepts only enumerated pinned deck keys, known opponent
scenarios, available pilot styles, and at most 200 seeds and 30 rounds
per request. It dispatches only the deep-simulations.yml workflow at main,
never arbitrary code or a user-provided GitHub ref.

Cloudflare rate-limit bindings reduce password guessing and accidental
repeat jobs. They are approximate and edge-local; configure a GitHub
billing/spending cap as an independent control.

The Python publisher reuses the repository's existing validated outcomes
format. Scenarios from identical engine source revisions can coexist.
Publishing after an engine revision change clears stale modeled results.
Re-requesting the same cohort replaces it rather than double-counting runs.

The existing Pages site and saved results remain public. A GitHub owner or
collaborator can still run Actions through their GitHub account. This simple
shared-password gate protects only the browser-triggered path.

This feature branch intentionally leaves the active UI untouched while its
separate workstream proceeds. The feature is not live until the owner sets
both Worker secrets and deploys it. Larger 1,000-4,000-game experiments
will require chunked jobs and matching UI library support.
