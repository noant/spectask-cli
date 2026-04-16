# Step 2: README and HLA

## Goal
Align user-facing documentation and the architecture blurb with the new `--update` semantics.

## Approach
- In `README.md`: in the `--update` table row, state the shorthand covers `--skip-example` and `--skip-hla-file`, but **not** `--skip-navigation-file`; optionally add one sentence that explicit `--skip-navigation-file` restores the old “do not copy registry” behavior.
- In `spec/design/hla.md`: fix the sentence about `--update` so it does not claim `--skip-navigation-file` is implied.

## Affected files
- `README.md`
- `spec/design/hla.md`

## Notes
- Run after step 1 and as part of the normal review cycle; per `spec/main.md`, HLA is finalized in Step 7 after code review, but the prose can be prepared in the same change set as step 1 if that matches repo practice.
