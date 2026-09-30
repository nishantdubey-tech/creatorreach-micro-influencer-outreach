"""Streamlit dashboard for the micro-influencer outreach workflow."""
from __future__ import annotations
import csv, os
from pathlib import Path
import pandas as pd
import streamlit as st
from src.pipeline import DATA, discover_and_prepare, read_records, refresh_filter, refresh_messages
from src.outreach import simulate_send

ROOT=Path(__file__).resolve().parent


def load_local_env() -> None:
    # Streamlit Community Cloud injects credentials through st.secrets, while
    # local runs may use the ignored .env file. Normalize both to environment
    # variables so the discovery/personalization modules share one interface.
    try:
        for name in ('YOUTUBE_API_KEY', 'OPENAI_API_KEY', 'OPENAI_MODEL'):
            if name in st.secrets and st.secrets[name]:
                os.environ.setdefault(name, str(st.secrets[name]))
    except Exception:
        # Accessing st.secrets without a local secrets.toml raises an exception.
        pass
    env_path=ROOT/'.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                name,value=line.split('=',1)
                os.environ.setdefault(name.strip(),value.strip().strip('"\''))


def records_df(filename='influencers.csv') -> pd.DataFrame:
    path=DATA/filename
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path,keep_default_na=False)


def show() -> None:
    load_local_env()
    st.set_page_config(page_title='CreatorReach | Fitness discovery',page_icon='🎯',layout='wide')
    st.title('CreatorReach')
    st.caption('Fitness micro-influencer discovery and compliant outreach workflow')
    pages=['Dashboard','Discover & Enrich','Filter','Generate Messages','Review & Simulate','Outreach Tracker']
    page=st.sidebar.radio('Workflow',pages,index=0)
    st.sidebar.markdown('**Niche:** Fitness  ·  **Platform:** YouTube  ·  **Region:** India search')
    st.sidebar.caption('Emails and audience demographics are never guessed. Email delivery is simulated only.')
    df=records_df()
    qualified=df[df.get('filter_status',pd.Series(dtype=str))=='Passed'] if not df.empty else pd.DataFrame()

    if page=='Dashboard':
        total=len(df); passed=len(qualified)
        sent_df=records_df('outreach.csv')
        skipped=int((sent_df.get('Status',pd.Series(dtype=str))=='SKIPPED_NO_PUBLIC_EMAIL').sum()) if not sent_df.empty else 0
        c1,c2,c3,c4=st.columns(4)
        c1.metric('Profiles discovered',total); c2.metric('Qualified creators',passed)
        c3.metric('Public emails found',int((qualified.get('contact_email',pd.Series(dtype=str))!='Not Found').sum()) if not qualified.empty else 0)
        c4.metric('Outreach skipped',skipped)
        st.subheader('Workflow')
        st.code('Discover → Enrich → Filter → Personalize → Review → Simulate → Track',language='text')
        if total:
            st.subheader('Latest live dataset')
            st.dataframe(df[['name','followers','engagement_rate_pct','filter_status','filter_reason']].head(12),width='stretch',hide_index=True)
            st.download_button('Download influencers.csv',df.to_csv(index=False).encode(),file_name='influencers.csv',mime='text/csv')
        else: st.info('No dataset yet. Open “Discover & Enrich” to start a live YouTube API run.')

    elif page=='Discover & Enrich':
        st.subheader('Discover public creator profiles')
        target=st.number_input('Unique profiles to fetch',min_value=50,max_value=200,step=10,value=50)
        st.info('Uses the YouTube Data API v3. The run collects public profile statistics, recent videos, public description emails, and content themes. Data is refreshed when you click the button.')
        if st.button('Discover and enrich profiles',type='primary'):
            try:
                with st.spinner('Searching channels and loading recent public metrics…'):
                    result=discover_and_prepare(int(target))
                st.success(f"Saved {len(result)} profiles; {sum(r['filter_status']=='Passed' for r in result)} qualified.")
                st.rerun()
            except Exception as exc: st.error(str(exc))
        st.caption('YouTube subscriber counts are public profile metrics. Engagement is an average recent-video likes+comments divided by subscribers; unavailable values are flagged.')

    elif page=='Filter':
        st.subheader('Explainable qualification filters')
        st.markdown('Fitness content in at least two recent titles · individual creator channel · India focus if country is public · 5,000–100,000 subscribers · engagement metrics available.')
        if st.button('Apply filters to current dataset',type='primary'):
            try:
                result=refresh_filter(); st.success(f"{sum(r['filter_status']=='Passed' for r in result)} passed from {len(result)} profiles."); st.rerun()
            except Exception as exc: st.error(str(exc))
        if not df.empty:
            st.dataframe(df[['name','followers','engagement_rate_pct','filter_status','filter_reason']],width='stretch',hide_index=True)

    elif page=='Generate Messages':
        st.subheader('Personalized email and Instagram DM drafts')
        st.info('Optional OpenAI Responses API generation is used when OPENAI_API_KEY is configured. Otherwise, a content-aware local fallback creates drafts from each creator’s recent public video titles. Review before use.')
        if st.button('Generate messages for qualified creators',type='primary'):
            try:
                result=refresh_messages(); st.success(f"Generated drafts for {sum(r['filter_status']=='Passed' for r in result)} qualified creators."); st.rerun()
            except Exception as exc: st.error(str(exc))
        if not qualified.empty:
            st.dataframe(qualified[['name','content_themes','personalization_method','email_pitch','instagram_dm']],width='stretch',hide_index=True)
            st.download_button('Download personalized messages',qualified.to_csv(index=False).encode(),file_name='shortlisted_messages.csv',mime='text/csv')

    elif page=='Review & Simulate':
        st.subheader('Human review and safe send simulation')
        st.warning('Simulation only: this prototype never sends email or Instagram DMs. Only qualified creators with a public email enter the simulated pending-review queue.')
        if not qualified.empty:
            st.dataframe(qualified[['name','contact_email','followers','engagement_rate_pct','content_themes','email_pitch','instagram_dm']],width='stretch',hide_index=True)
            if st.button('Simulate email sending',type='primary'):
                result=simulate_send(DATA)
                st.success(f"Queued {result['queued']}; skipped for missing public email {result['skipped']}; duplicate profiles skipped {result['duplicates']}. No messages were sent.")
                st.rerun()
        else: st.info('No qualified profiles available. Run discovery first.')

    else:
        st.subheader('Outreach tracker')
        tracker=records_df('outreach.csv')
        if tracker.empty: st.info('No outreach actions recorded yet.')
        else:
            st.dataframe(tracker,width='stretch',hide_index=True)
            st.download_button('Download outreach.csv',tracker.to_csv(index=False).encode(),file_name='outreach.csv',mime='text/csv')

    st.divider()
    st.caption('Prototype · Public YouTube Data API data · No automated social messaging · Review outputs before outreach')

if __name__=='__main__': show()
