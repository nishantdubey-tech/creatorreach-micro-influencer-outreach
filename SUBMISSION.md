# CreatorReach assignment submission

## Live deliverable

- **Working Streamlit demo:** [creatorreach-nishant.streamlit.app](https://creatorreach-nishant.streamlit.app/)
- **GitHub source repository:** [nishantdubey-tech/creatorreach-micro-influencer-outreach](https://github.com/nishantdubey-tech/creatorreach-micro-influencer-outreach)
- **Dataset snapshot:** 102 unique public YouTube creator profiles, 12 qualified by the documented filter, and 90 failures with reasons.
- **Outreach safety:** 12 personalized email/DM draft pairs; 1 qualified profile has a publicly listed email and 11 are `Not Found`. No email or DM was sent.

## Assignment materials

- [`app.py`](app.py): six-page Streamlit workflow and dashboard.
- [`src/discovery.py`](src/discovery.py), [`src/enrichment.py`](src/enrichment.py), [`src/filtering.py`](src/filtering.py), [`src/personalization.py`](src/personalization.py), [`src/outreach.py`](src/outreach.py), [`src/pipeline.py`](src/pipeline.py): discovery, enrichment, classification, message generation, duplicate-safe tracking, and orchestration.
- [`data/influencers.csv`](data/influencers.csv): all 102 discovered profiles, metrics, filter results, reasons, and drafts.
- [`data/shortlisted_messages.csv`](data/shortlisted_messages.csv): the 12 qualified creators and personalized message drafts.
- [`data/outreach.csv`](data/outreach.csv) and [`data/outreach_tracker.csv`](data/outreach_tracker.csv): simulated outreach history and statuses.
- [`data/workflow.md`](data/workflow.md): workflow diagram.
- [`data/run_summary.md`](data/run_summary.md): source, counts, enrichment, and outreach summary.
- [`requirements.txt`](requirements.txt): Python dependencies.
- [`tests/test_workflow.py`](tests/test_workflow.py): offline workflow acceptance checks.
- [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example): safe deployment secret template; it contains no real credentials.

## Demo and screenshots

The live Streamlit app is the working demo deliverable. It opens on the 102-profile dashboard and includes **Dashboard**, **Discover & Enrich**, **Filter**, **Generate Messages**, **Review & Simulate**, and **Outreach Tracker** pages. The [`screenshots/`](screenshots/) folder links to the live demo; no static screenshot is included.

## Reproduce locally

See [`README.md`](README.md) for setup, API/tool details, filtering logic, enrichment limits, personalization prompts, deployment steps, and limitations. Never commit `.env` or `.streamlit/secrets.toml`; the project `.gitignore` excludes both.
