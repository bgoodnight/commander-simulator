# Legacy Python historical archive: R2 verification checkpoint

This is an immutable migration record for old, bounded **Python** simulation
archives only. It does not describe or supersede any native Gorge recordings,
R2 Parquet warehouse tables, active research/regression query datasets, or the
Gorge UI replay catalog.

- Original source: `web/pages/data/simulation-archive/`
- Original source index SHA-256:
  `61ce8dc8d8b59b77ba3e3a5bed3cf15dee12d24a4dff360483017f97f3120271`
- Original collection: **53 releases / 617 files / 117,383,795 source bytes**
- Independent Cloudflare R2 bucket: `gorge-simulations`
- Immutable R2 object:
  `legacy-python/v1/61ce8dc8d8b59b77/a202b1b0fcbba4b8c023c7760736b4292510d3730da02e7764b210a44c763f89.tar.gz`
- Compressed archive SHA-256:
  `a202b1b0fcbba4b8c023c7760736b4292510d3730da02e7764b210a44c763f89`
- Compressed archive size: **5,497,884 bytes**
- Corresponding inventory file: same R2 prefix and SHA basename,
  ending in `.inventory.json`.
- Verification: full R2 upload, download, SHA-256 archive check and
  **every archived file member** rehashed successfully.
- Verified GitHub Actions run:
  https://github.com/bgoodnight/commander-simulator/actions/runs/42027665399

## Retention and restoration

Retain this complete R2 archive indefinitely until a separately approved
retention review. It must not inherit temporary GitHub Actions artifact expiry
or any automatically expiring pilot experiment policy.

To restore, fetch the private R2 tarball using authorized credentials and
verify its SHA-256; unpack to a clean directory, then use
`python -m tools.publish_simulation_archive`'s `validate_index` function
to verify all original manifest and run hashes. Do not publish the full archive
to Pages automatically.

The compact public legacy catalog retains exactly the first compatible
historical release per active deck identity. The original UI can still load
those actual source-backed bounded runs. Other historical releases are
recoverable from this R2 archive and Git history, rather than GitHub Pages.

If current deck identities change, investigate and deliberately restore an
appropriate immutable release from R2 before changing UI publication.
