# CreatorReach: Automated Micro-Influencer Outreach System

CreatorReach is a working Python and Streamlit prototype for discovering real public YouTube fitness channels, enriching public profiles, filtering micro-influencers, writing personalized outreach, and tracking safe simulated email outreach.

**Live demo:** [creatorreach-nishant.streamlit.app](https://creatorreach-nishant.streamlit.app/) · **Submission guide:** [SUBMISSION.md](SUBMISSION.md)

Current public snapshot: **102 unique profiles**, **12 qualified creators**, **12 personalized email and DM draft pairs**. One qualified profile lists a public email; the other 11 are marked `Not Found`. The demo uses simulated outreach only.

## Technology stack

- Python 3.10+
- Streamlit for the interactive dashboard
- Pandas for UI data tables and downloads
- Standard library `urllib`, `csv`, and `sqlite3` for API requests, CSV datasets, and duplicate-safe tracking
- `unittest` for offline acceptance checks

## APIs and tools

- YouTube Data API v3: channel search, channel statistics, uploads playlists, and recent video statistics.
- Optional OpenAI Responses API for LLM-written email and DM drafts. The 12 included message pairs use the content-aware local fallback and public video titles; no OpenAI API key or request was used for these drafts. The optional OpenAI integration follows the official [OpenAI text-generation API guidance](https://developers.openai.com/api/docs/guides/text).
- No Gmail/SMTP or Instagram API is connected. Email sending is simulated, and DMs remain drafts.

## Data sources

The included live dataset was fetched from public YouTube Data API responses on 2026-10-01. Each record includes its YouTube profile URL, retrieval timestamp, search query, subscriber count, recent public video titles, available recent engagement metrics, and a public-channel-description email status. Email is recorded as `Not Found` when no public address appears. Audience age, gender, and geography are not returned by this public API and are explicitly marked unavailable; the India search region is not represented as audience location.

The submission does not include fabricated influencer rows. See [`data/run_summary.md`](data/run_summary.md) for actual run counts and [`data/workflow.md`](data/workflow.md) for the workflow diagram.

## Discovery methodology

The live discovery step searches six India-focused fitness phrases, interleaves results to avoid one query dominating the sample, deduplicates channel IDs within each run, and requests channel statistics plus up to ten recent uploads. New results merge into the saved dataset by profile URL; repeated profiles refresh in place. A future run may return a different set as YouTube search rankings and metrics change.

## Filtering and classification logic

All discovered profiles receive a transparent `Passed` or `Failed` status and a reason. A profile passes when it has at least two recent video titles with clear fitness signals, is not an obvious YouTube Topic or organization/institution channel, has 5,000-100,000 subscribers inclusive, has public engagement metrics, and does not report a channel country outside India. Missing engagement fails qualification instead of receiving an invented value.

Engagement rate is an observable proxy: average `(likes + comments)` per recent video divided by subscribers, expressed as a percentage. It is not reach-based engagement. The expanded snapshot has 102 unique records, 12 qualified creators, and 90 failures with reasons.

## Profile enrichment

For each channel, the pipeline stores name, platform, URL, subscribers, engagement proxy, fitness/content context, publicly listed email or `Not Found`, optional website URLs from the public channel description, channel country if supplied, source, timestamps, and the sample size behind the engagement calculation. Audience demographics are unavailable through this public endpoint.

## AI model and prompt

When `OPENAI_API_KEY` is present, the optional LLM path calls the OpenAI Responses API (default `OPENAI_MODEL=gpt-6-astra`). The prompt sends only creator name, niche, and up to five recent public video titles. It asks for JSON containing `email_pitch` and `instagram_dm`, prohibits invented audience facts or claims of personal interaction, and requires 60-90 and 15-30 words respectively. Generated lengths are checked; invalid responses fall back to the local generator. `personalization_method` records the actual method used per row. No OpenAI API call was made for the included dataset.

## Personalization logic

The local fallback uses the creator display name and an actual recent public video title, with a campaign-specific paid partnership proposal and disclosure/creative-control value proposition. It produces individualized drafts and checks the assignment's word limits. Review message claims and campaign details before use.

## Sending mechanism and tracker

The dashboard and CLI use a SQLite uniqueness constraint on profile URL to prevent duplicate outreach. Only qualified records with a public email can enter `SIMULATED_PENDING_REVIEW`; qualified profiles without one are logged as `SKIPPED_NO_PUBLIC_EMAIL`. No messages are sent. The Instagram DM remains a manual draft. The CSV tracker is `data/outreach.csv` and includes email, generated message, sent date, status, channel, and profile URL. The sent date remains blank for this simulation.

## Limitations

- A Google Cloud project with YouTube Data API v3 enabled and a valid API key is required for a fresh discovery run. Search results are not guaranteed to contain 50 qualified creators per search run.
- Public metrics can be rounded, disabled, or incomplete; comments/likes and subscriber counts do not capture reach, stories, or audience quality.
- Search region and channel country do not prove where an audience lives.
- No creator-provided demographics or private analytics are available.
- Only email addresses visible in channel descriptions are extracted. The expanded snapshot found one public email among 12 qualified creators; the other 11 are `Not Found`. The included tracker records the original five skips; no new outreach was sent during dataset expansion.
- The OpenAI pathway requires a separate OpenAI API key and can incur usage charges. The submitted messages were produced by the local fallback.
- Before production scale, add consent/suppression tracking, retries/backoff, campaign review, privacy retention controls, and lawful delivery integrations.

## Setup instructions

1. Install Python 3.10 or newer.
2. Install the dependencies: `python -m pip install -r requirements.txt`.
3. Create a Google Cloud project, enable YouTube Data API v3, create an API key restricted to that API, and set `YOUTUBE_API_KEY` in your environment. The workspace's private `.env` is not included in the ZIP. Never commit or share it.
4. Optional LLM drafts: set `OPENAI_API_KEY`; optionally set `OPENAI_MODEL`.
5. Start the UI: `streamlit run app.py`.
6. Or run the CLI from this project folder:
   - `python -m src.pipeline discover --target 50`
   - `python -m src.pipeline filter`
   - `python -m src.pipeline personalize`
   - `python -m src.pipeline simulate-send`
7. Run the offline acceptance checks: `python -m unittest discover -s tests -v`.

The deployed Streamlit demo is available at [creatorreach-nishant.streamlit.app](https://creatorreach-nishant.streamlit.app/). Locally, it runs at `http://localhost:8501`. The project package includes the expanded live dataset, personalized drafts, tracker, source modules, and tests. The API key remains outside the repository and submission ZIP.

## Deploy to Streamlit Community Cloud

The app is configured for Community Cloud and reads `YOUTUBE_API_KEY` and optional OpenAI settings from Streamlit secrets. The checked-in `.streamlit/secrets.toml.example` is a template only; never commit a real secrets file.

1. The app is already deployed from the [GitHub repository](https://github.com/nishantdubey-tech/creatorreach-micro-influencer-outreach).
2. To deploy a separate copy, sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and choose **Create app**.
3. Select the repository, branch, and `app.py` entrypoint, then choose an app URL.
4. In **Advanced settings → Secrets**, enter `YOUTUBE_API_KEY = "your-key"`. Keep `OPENAI_API_KEY` blank unless you want optional paid OpenAI API personalization.
5. Save and wait for the build to finish. The included dataset and drafts render without secrets; the YouTube key is needed only for new discovery runs.

Community Cloud deploys from GitHub and requires repository access. Its secrets manager keeps runtime credentials outside the repository. See the [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
