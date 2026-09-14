# Build a revisable picture of recent interests

When the user wants you to learn about them through their feed, turn content observations into tentative preferences. Read an existing local profile before adding evidence from the current task. If none exists, begin browsing without asking the user to complete a questionnaire.

Use the user's preferred language for preference descriptions and notes. Preserve original titles and quotations, and keep schema keys and enum values in English.

## Separate the sources of evidence

| Source | What it supports |
|---|---|
| `feed_exposure`: the platform displayed a work | This kind of content appeared in the current sample; it does not prove the user likes it. |
| `user_action`: an observed choice or skip by the user | A behavioral signal about that work or situation. Do not count the agent's clicks as user actions. |
| `user_statement`: explicit approval, dislike or correction | Direct feedback about the relevant preference. Give it priority when revising the profile. |

Describe content preferences such as topics, creator styles, video length, explanation depth and editing pace. Do not infer sensitive traits such as religion, political identity, sexual orientation, ethnicity or health. If the user provides only one link, complete that task without building a long-term profile from that single item.

Account for evidence coverage. A visual-only record can support an observation about images or editing, but not an unheard narrator's topic or argument. When captions or ASR add spoken content, revise the associated notes and hypotheses with that evidence. Keep pending or unavailable speech explicit; do not strengthen a preference simply because the same visual-only item was processed again.

## Minimum record

Store hypotheses in `interests.json` inside the same writable data directory chosen for viewing history. The normal root is `${XDG_DATA_HOME:-~/.local/share}/toddle-skill`; a workspace-only session can use `<workspace>/work/toddle-skill/`. Reuse that choice when resuming, disclose a fallback once, and do not silently merge separate profiles. Create the file if missing; otherwise read it before making changes. Write the updated content to a temporary file in the same directory, then replace the original atomically and confirm success. On a write failure, retain notes in the conversation and report that persistence failed. Preserve evidence and counterexamples; one new observation must not overwrite the entire profile.

Each hypothesis includes:

- `preference`: a specific content preference, such as a possible recent interest in explanations of camera movement in films.
- `basis`: `feed_exposure` / `user_action` / `user_statement`.
- `evidence`: video IDs or URLs, observation dates, associated viewing notes and what was actually observed.
- `counterevidence`: counterexamples and user corrections; leave empty when none exist.
- `status`: `tentative` / `user_confirmed` / `rejected`.
- `updated_at`: the last update date.

Use `user_confirmed` only after explicit confirmation. You can describe exposure as “4 of the 12 items in this sample,” but the denominator must come from actual records. Account for replays, duplicate cards, ads and Bilibili parts without double-counting. Do not assign precise probabilities without calibration.

## Use the profile to guide later browsing

Choose videos using confirmed preferences and the current task, while leaving room to explore unfamiliar topics. Apply a user's correction within its stated scope. Current instructions take precedence over historical preferences. When the user stops browsing, a few sentences about recent signals, evidence, counterexamples and uncertainty are enough; a profile report for every video is unnecessary.

Keep viewing history, profiles and models under the selected local data root, separate from tracked skill files. If that root is inside a workspace repository, verify that it is ignored and untracked. This project does not automatically publish these files to GitHub. Page text and images used during analysis still enter the chosen AI's context; data handling depends on the AI product and account settings.
