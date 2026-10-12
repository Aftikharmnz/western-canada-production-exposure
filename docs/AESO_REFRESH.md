# AESO power refresh

The 30-minute `refresh-aeso-power.yml` schedule validates the public AESO Current
Supply Demand CSV, atomically replaces the power snapshot, checks the existing
alert transitions, and publishes only the power snapshot and alert state.
Deployment is a dependent reusable job from `deploy-pages.yml`. There is no
separate workflow-dispatch HTTP request; the refresh run includes the actual
website deployment result.

## Failure investigated on 2026-10-12

[Run 1611](https://github.com/Aftikharmnz/western-canada-production-exposure/actions/runs/38282856650)
fetched, checked alerts, and pushed the data successfully. GitHub returned HTTP
500 when the final step requested a separate Pages workflow. The next scheduled
refresh, run 1612, and its Pages deployment succeeded. This was a deployment
request failure, not an AESO source failure.

## Publication safeguards

- Downloads have a 60-second timeout, a 512 KiB size limit, strict UTF-8 decoding,
  and at most three attempts with two- and four-second delays. Temporary HTTP
  errors, connection failures, and invalid or stale reports are retried; HTTP
  403 and 404 fail immediately.
- All five displayed system metrics and the fuel summary must be present. Unit
  codes must be unique. Unit maximum capabilities must reconcile to the report
  total within 1 MW, protecting against truncated responses.
- Source observations must be at most 90 minutes old and no more than five
  minutes ahead. An older observation cannot overwrite a newer published one.
- The pinned `tzdata` package supplies Alberta's time rules independently of
  the runner's system database. Alberta remains on UTC-6 from November 2026:
  [Government of Alberta](https://www.alberta.ca/albertas-new-time-system-abt).
- Missing generation remains unknown; a reported zero remains zero. Missing
  site units make that site's aggregate unknown. Fuel headings are not carried
  across unlabelled CSV blocks.
- Invalid reports and failed writes preserve the previous snapshot. The app's
  existing observation-age checks label old data stale rather than current.
- AESO refreshes and Pages deployments are serialized without cancelling an
  active run. Refresh jobs have a ten-minute timeout and full Git history for
  the existing safe rebase/publication checks. Source or parser changes that
  overlap a running candidate still require a new run; no force push is used.
- Reusable deployment checks out `main` after publication, including the new
  snapshot rather than the refresh's older triggering commit. Existing Pages
  validation and protected-site artifact checks remain enabled.
- Alert checking remains independent of data publication. Existing tests cover
  repeated/stale observations, missing readings, failed fire feeds and recovery
  transitions. Alert delivery failures retain unacknowledged state for retry
  and remain visible in the alert step's logs and annotations.

## Verification without notifications

Manual runs default to the existing production refresh behavior. `test_email`
remains false by default.

`check_only=true` runs the offline safety tests and a real AESO download without
publishing, deploying, checking alerts or sending email. This is allowed on a
repair branch; ordinary publication is restricted to `main`.

`skip_alerts=true` on `main` verifies the complete download, publication and
Pages deployment path while skipping alert checks for that one manual run.
Scheduled runs continue to check alerts normally.

Local verification, after installing the AESO requirements:

```text
python -m unittest discover -s scripts -p 'test_aeso*.py'
python -m unittest discover -s scripts -p 'test_api_safety.py'
python scripts/build_aeso_power_status.py --output data/processed/aeso-check.json
```

GitHub or AESO outages can still prevent a run from completing. These safeguards
remove the observed dispatch failure path and protect the last valid data; they
do not conceal persistent source, permission or deployment failures.
