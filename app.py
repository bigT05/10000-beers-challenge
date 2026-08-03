import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import math

# ----------------------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------------------

GLOBAL_COLOUR = "#EE7846"

st.set_page_config(page_title="10,000 Beers Challenge", page_icon="🍻", layout="wide")

# custom css
st.markdown(f"""
    <style>
    /* 1. HIDE DEFAULT STREAMLIT ELEMENTS & LINKS */
    header[data-testid="stHeader"] {{ background-color: transparent !important; }}
    [data-testid="stSidebarHeader"] {{ padding-bottom: 0rem !important; }}
    .block-container {{ padding-top: 2rem !important; }}
    #root > div:first-child, .stApp {{ border: none !important; }}

    /* Nukes the link icons next to headers across all Streamlit versions */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, h3 svg, h2 svg, h1 svg, a.header-anchor, .stMarkdown a svg {{ 
        display: none !important; 
    }}

/* 2. STYLE THE TABS */
[data-testid="stTab"][aria-selected="true"] {{
    color: {GLOBAL_COLOUR} !important;
}}
[data-testid="stTab"][aria-selected="true"] p {{
    color: {GLOBAL_COLOUR} !important;
    font-weight: 800 !important;
    font-size: 1.15rem !important;
}}
[data-testid="stTab"]:not([aria-selected="true"]) p {{
    font-size: 1rem !important;
    opacity: 0.75;
}}
.stTabs div[data-baseweb="tab-highlight"] {{
    background-color: {GLOBAL_COLOUR} !important;
    height: 3px !important;
    border-radius: 3px;
}}
[data-testid="stTab"] .react-aria-SelectionIndicator {{
    background-color: {GLOBAL_COLOUR} !important;
}}

    /* 3. MAKE METRIC NUMBERS POP & PREVENT TRUNCATION */
    [data-testid="stMetricValue"] > div, 
    [data-testid="stMetricValue"] {{
        color: {GLOBAL_COLOUR} !important;
        font-weight: 900 !important;
        font-size: 1.6rem !important; 
        white-space: normal !important; 
        line-height: 1.2 !important;
    }}

    /* 4. COLOR & ACCENT HEADERS */
    h1 {{
        color: {GLOBAL_COLOUR} !important; 
    }}
    h3 {{
        color: #FFFFFF !important; 
        border-left: 5px solid {GLOBAL_COLOUR}; 
        padding-left: 12px !important;
        margin-top: 15px !important;
        margin-bottom: 15px !important;
    }}
    
    /* 5. FIX THE PROGRESS BAR COLOR */
    .stProgress > div > div:has(div[style*="translateX"]) {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        height: 18px !important;
        overflow: hidden !important;
    }}
    .stProgress div[style*="translateX"] {{
        background-color: {GLOBAL_COLOUR} !important;
        height: 18px !important;
        border-radius: 10px !important;
    }}
    

    /* 6. SUBTLE SIDEBAR ACCENTS */
    [data-testid="stSidebar"] hr {{
        border-bottom-color: {GLOBAL_COLOUR} !important;
        opacity: 0.2; 
    }}

    /* 7. DESKTOP PODIUM STYLING */
    .podium-box {{
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background-color: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .first-place {{ border-top: 5px solid #FFD700; margin-top: 0px; }}
    .second-place {{ border-top: 5px solid #C0C0C0; margin-top: 30px; }}
    .third-place {{ border-top: 5px solid #CD7F32; margin-top: 50px; }}
    .podium-title {{ font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; color: #FFFFFF !important; }}
    .podium-name {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; color: #FFFFFF !important; }}
    .podium-score {{ font-size: 1rem; opacity: 0.8; margin: 0px; color: #FFFFFF !important; }}

    /* 8. RESPONSIVE PODIUM LAYOUTS */
    @media (min-width: 641px) {{
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) {{ order: 2; }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {{ order: 1; }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(3) {{ order: 3; }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] {{ display: flex !important; }}
    }}

    @media (max-width: 640px) {{
        .st-key-podium_container div[data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: column !important; 
            gap: 15px !important;
        }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) {{ order: 1; }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {{ order: 2; }}
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(3) {{ order: 3; }}
        .st-key-podium_container .podium-box {{
            height: auto !important;
            margin-top: 0px !important; 
            padding: 15px !important;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# CONFIGURATION & DATA LOADING
# ----------------------------------------------------------------------

# live Dropbox link
DROPBOX_DIRECT_URL = "https://www.dropbox.com/scl/fi/m69ohs691eb8zbkdzsg9z/10000-beers-log.xlsx?rlkey=n7buk0hfmsubo7ivkz6qyf97s&st=2v1r6dop&dl=1"
# beer goal
BEER_GOAL = 10000


@st.cache_data(ttl=300, show_spinner="Fetching fresh beers...")  # cache data for 5 mins to prevent constant reloading
def load_data():
    try:
        # load main beers list directly from dropbox
        beers_df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Beers List", engine='openpyxl')

        # drop rows where beer owner is blank
        beers_df = beers_df.dropna(subset=['Beer Owner'])

        parsed_last_sync = pd.NaT
        parsed_manual_sync = pd.NaT

        # --- PARSE METADATA DATES ---
        try:
            meta_df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Metadata", header=None, engine='openpyxl')

            # unified helper to catch excel serial dates, native datetimes, and nans
            def format_date_str(val):
                if pd.isna(val):
                    return ""
                if isinstance(val, (int, float)):
                    return (pd.to_datetime('1899-12-30') + pd.Timedelta(days=val)).strftime('%d/%m/%Y')
                if isinstance(val, (pd.Timestamp, datetime)):
                    return val.strftime('%d/%m/%Y')
                return str(val).strip()

            # parse manual timestamp (AppSheet)
            manual_date = format_date_str(meta_df.iloc[1, 1])
            manual_time = str(meta_df.iloc[1, 2]).strip()
            parsed_manual_sync = pd.to_datetime(f"{manual_date} {manual_time}", dayfirst=True, errors='coerce')

            if pd.notna(parsed_manual_sync):
                parsed_manual_sync = parsed_manual_sync.replace(tzinfo=timezone.utc)

            # parse snapchat/sync timestamp
            sync_date = format_date_str(meta_df.iloc[2, 1])
            sync_time = str(meta_df.iloc[2, 2]).strip()
            parsed_last_sync = pd.to_datetime(f"{sync_date} {sync_time}", dayfirst=True, errors='coerce')

            if pd.notna(parsed_last_sync):
                parsed_last_sync = parsed_last_sync.replace(tzinfo=timezone.utc)

        except Exception:
            pass  # metadata parsing failed, fallbacks will trigger below

        # --- HANDLE MISSING DATES AND TIMES ---

        # mark which rows are missing timestamps
        beers_df['Is_Fallback_Time'] = beers_df['Date of Beer (UTC)'].isna() | beers_df['Time of Beer (UTC)'].isna()

        # fallback: if metadata is missing, use current UTC time
        fallback_dt = parsed_manual_sync if pd.notna(parsed_manual_sync) else datetime.now(timezone.utc)

        # fill missing values
        beers_df['Date of Beer (UTC)'] = beers_df['Date of Beer (UTC)'].fillna(fallback_dt.strftime('%d/%m/%Y'))
        beers_df['Time of Beer (UTC)'] = beers_df['Time of Beer (UTC)'].fillna(fallback_dt.strftime('%H:%M:%S'))

        # --- NORMALIZE MIXED FORMATS ---

        # apply the unified date format helper to the main dataframe
        beers_df['Date of Beer (UTC)'] = beers_df['Date of Beer (UTC)'].apply(format_date_str)

        normalized_dates = pd.to_datetime(beers_df['Date of Beer (UTC)'], dayfirst=True, errors='coerce')
        normalized_times = beers_df['Time of Beer (UTC)'].astype(str)

        beers_df['Datetime'] = pd.to_datetime(
            normalized_dates.dt.strftime('%Y-%m-%d') + " " + normalized_times,
            errors='coerce'
        )

        # drop any failed conversions, sort chronologically, and apply UTC timezone
        beers_df = beers_df.dropna(subset=['Datetime']).sort_values(by="Datetime").reset_index(drop=True)
        beers_df['Datetime'] = beers_df['Datetime'].dt.tz_localize('UTC')

        return beers_df, parsed_last_sync, parsed_manual_sync

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.NaT, pd.NaT


df, last_sync_dt, manual_sync_dt = load_data()

# stop execution if data is empty
if df.empty:
    st.warning("No data found. Please check your Excel file.")
    st.stop()


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------

def time_ago(timestamp):
    """converts a datetime into a relative 'time ago' string."""
    if pd.isna(timestamp):
        return "Never"

    current_utc = datetime.now(timezone.utc)
    time_diff = current_utc - timestamp
    total_secs = time_diff.total_seconds()

    if total_secs < 60:
        return f"{int(max(0, total_secs))} secs ago"
    elif total_secs < 3600:
        mins = int(total_secs // 60)
        return f"{mins} min{'s' if mins > 1 else ''} ago"
    elif total_secs < 86400:
        hours = int(total_secs // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(total_secs // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"


def format_custom_date(input_dt):
    """converts a datetime object to a '7th September 2029' format."""
    if pd.isna(input_dt):
        return "Unknown"

    dt_day = input_dt.day

    # figure out the st, nd, rd, th suffix
    if 11 <= (dt_day % 100) <= 13:
        day_suffix = "th"
    else:
        day_suffix = {1: "st", 2: "nd", 3: "rd"}.get(dt_day % 10, "th")

    # %B gets the full capitalized month name (e.g., 'September')
    dt_month = input_dt.strftime('%B')
    dt_year = input_dt.year

    return f"{dt_day}{day_suffix} {dt_month} {dt_year}"


# ----------------------------------------------------------------------
# SIDEBAR: FEED & STATUS
# ----------------------------------------------------------------------

with st.sidebar:
    # profile logo header
    st.image("profile.jpg", clamp=True)

    st.divider()

    # --- RECENT CHECK-INS ---
    st.subheader("Recent Beers* 🍺", anchor=False)

    recent_beers_df = df.sort_values(by="Datetime", ascending=False).head(10)

    for _, beer_row in recent_beers_df.iterrows():
        # if the date/time was missing in Excel, display "recently"
        if beer_row.get('Is_Fallback_Time', False):
            display_time = "recently"
        else:
            display_time = time_ago(beer_row['Datetime'])

        st.markdown(f"**{beer_row['Beer Owner']}** - *{display_time}*")

    st.divider()

    # --- SYSTEM STATUS ---
    st.subheader("System Status")

    # Custom HTML Status Cards to replace st.info and st.success
    st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {GLOBAL_COLOUR}; border-radius: 5px; padding: 12px; margin-bottom: 10px;">
                <div style="font-size: 0.85rem; color: #FFFFFF; opacity: 0.7; margin-bottom: 5px;">Last Spreadsheet Update</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {GLOBAL_COLOUR};">{time_ago(manual_sync_dt)}</div>
            </div>
            <div style="background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {GLOBAL_COLOUR}; border-radius: 5px; padding: 12px; margin-bottom: 15px;">
                <div style="font-size: 0.85rem; color: #FFFFFF; opacity: 0.7; margin-bottom: 5px;">Last Time Sync</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {GLOBAL_COLOUR};">{time_ago(last_sync_dt)}</div>
            </div>
        """, unsafe_allow_html=True)

    # database refresh button
    if st.button("Reload Database", use_container_width=True):
        st.cache_data.clear()  # clears cached database call
        st.rerun()  # reloads the streamlit app state

# ----------------------------------------------------------------------
# MAIN DASHBOARD
# ----------------------------------------------------------------------
st.markdown("<h1 style='text-align: center;'>🍻 10,000 Beers Challenge 🍻</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Summary", "Full Beer List"])

with tab1:
    # --- SECTION 1: BEER PROGRESS CHART ---

    total_beers = len(df)
    progress_pct = total_beers / BEER_GOAL

    # extrapolation logic
    first_beer_time = df['Datetime'].min()
    current_time = datetime.now(timezone.utc)
    days_elapsed = (current_time - first_beer_time).total_seconds() / 86400

    if days_elapsed > 0:
        beers_per_day = total_beers / days_elapsed
        beers_left = BEER_GOAL - total_beers
        days_left = beers_left / beers_per_day
        eta_date = current_time + pd.Timedelta(days=days_left)

        # pass the raw date object into the custom formatting function
        eta_str = format_custom_date(eta_date)
        velocity_str = f"{beers_per_day:.1f} beers/day"
    else:
        eta_str = "TBD"
        velocity_str = "TBD"

    st.subheader("Beer Progress Bar")

    display_pct = math.floor(progress_pct * 100)  # floors, so 99.99% shows as 99%, not 100%
    bar_width = min(progress_pct * 100, 100)  # visual fill width, capped at 100%

    st.markdown(f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 24px;
            width: 100%;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                background-color: {GLOBAL_COLOUR};
                height: 100%;
                width: {bar_width}%;
                border-radius: 10px;
            "></div>
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                padding-left: 12px;
                font-size: 0.8rem;
                font-weight: 700;
                color: #FFFFFF;
                text-shadow: 0 1px 2px rgba(0,0,0,0.6);
            ">{display_pct}%</div>
        </div>
    """, unsafe_allow_html=True)

    # Add some space
    st.write("")

    col1, col2, col3 = st.columns(3)

    # Wrapping them in st.container(border=True) creates a sleek outline card!
    with col1:
        with st.container(border=True):
            st.metric("Total Beers So Far", f"{total_beers:,} / {BEER_GOAL:,}")
    with col2:
        with st.container(border=True):
            st.metric("Current Flow of Beer", velocity_str)
    with col3:
        with st.container(border=True):
            st.metric("Estimated Finish Date", eta_str)

    st.divider()

    # --- SECTION 2: LEADERBOARD & PIE CHART ---

    # quick helper function to generate 4th, 5th, etc. for the table
    def get_ordinal(rank_num):
        if 11 <= (rank_num % 100) <= 13:
            return str(rank_num) + "th"
        return str(rank_num) + {1: "st", 2: "nd", 3: "rd"}.get(rank_num % 10, "th")


    # left column is slightly wider to give the podium and table room to breathe
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.subheader("All-Time Leaderboard 🏆")

        # calculate leaderboard totals
        leaderboard_df = df['Beer Owner'].value_counts().reset_index()
        leaderboard_df.columns = ['Beer Owner', 'Number of Beers']

        # calculate total days the challenge has been running
        total_running_days = max(1, (pd.Timestamp.now(tz='UTC') - df['Datetime'].min()).days)
        leaderboard_df['Beers / Day'] = (leaderboard_df['Number of Beers'] / total_running_days).round(1)

        # extract top 3 data safely
        top_3_names = leaderboard_df['Beer Owner'].head(3).tolist()
        top_3_scores = leaderboard_df['Number of Beers'].head(3).tolist()
        top_3_bpd = leaderboard_df['Beers / Day'].head(3).tolist()

        # pad with blanks if fewer than 3 people have drank so far
        while len(top_3_names) < 3:
            top_3_names.append("N/A")
            top_3_scores.append(0)
            top_3_bpd.append(0.0)

        # vertical_alignment="bottom" ensures they all sit on the exact same baseline
        with st.container(key="podium_container"):
            pod1, pod2, pod3 = st.columns(3, vertical_alignment="bottom")

            with pod1:
                st.markdown(
                    f"<div class='podium-box first-place' style='height: 310px; display: flex; flex-direction: column; justify-content: center;'>"
                    f"<div class='podium-title'>1st 🥇</div>"
                    f"<div class='podium-name'><b>{top_3_names[0]}</b></div>"
                    f"<div class='podium-score'>🍺 {top_3_scores[0]} beers</div>"
                    f"<div style='font-size: 0.8em; opacity: 0.7;'>~{top_3_bpd[0]} beers/day</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with pod2:
                st.markdown(
                    f"<div class='podium-box second-place' style='height: 250px; display: flex; flex-direction: column; justify-content: center;'>"
                    f"<div class='podium-title'>2nd 🥈</div>"
                    f"<div class='podium-name'><b>{top_3_names[1]}</b></div>"
                    f"<div class='podium-score'>🍺 {top_3_scores[1]} beers</div>"
                    f"<div style='font-size: 0.8em; opacity: 0.7;'>~{top_3_bpd[1]} beers/day</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with pod3:
                st.markdown(
                    f"<div class='podium-box third-place' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>"
                    f"<div class='podium-title'>3rd 🥉</div>"
                    f"<div class='podium-name'><b>{top_3_names[2]}</b></div>"
                    f"<div class='podium-score'>🍺 {top_3_scores[2]} beers</div>"
                    f"<div style='font-size: 0.8em; opacity: 0.7;'>~{top_3_bpd[2]} beers/day</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- THE CONTENDERS (4TH PLACE ONWARD) ---
        if len(leaderboard_df) > 3:
            rest_of_pack = leaderboard_df.iloc[3:].copy()

            # apply the ordinal function to create a rank column
            rest_of_pack['Rank'] = [get_ordinal(i + 4) for i in range(len(rest_of_pack))]

            # reorder the dataframe columns
            rest_of_pack = rest_of_pack[['Rank', 'Beer Owner', 'Number of Beers', 'Beers / Day']]

            st.dataframe(rest_of_pack, use_container_width=True, hide_index=True)

    with col_right:
        # --- PIE CHART ---
        st.subheader("Percentage Contribution")

        # map each person's name to a specific hex color
        custom_pie_colors = {
            "Tom": "#FFBA00",
            "Logan": "#D80030",
            "Archie": "#FF8A00",
            "Mills": "#00D5A0",
            "JJ": "#3461EF",
            "Moo": "#6DCFBA",
            "KSI": "#8936B6",
            "Ashton": "#A871FF",
            "Sam": "#E50184",
        }

        fig_pie = px.pie(
            leaderboard_df,
            values='Number of Beers',
            names='Beer Owner',
            template="plotly_dark",
            hole=0.3,
            color='Beer Owner',
            color_discrete_map=custom_pie_colors
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # --- TOP 3 LAST 30 DAYS ---
        st.subheader("Last 30 Days: Top 3")

        thirty_days_ago = pd.Timestamp.now(tz='UTC') - pd.DateOffset(days=30)
        last_month_df = df[df['Datetime'] >= thirty_days_ago]

        if not last_month_df.empty:
            last_month_lb = last_month_df['Beer Owner'].value_counts().reset_index()
            last_month_lb.columns = ['Beer Owner', 'Number of Beers']

            # isolate the top 3 safely
            top_3_lm = last_month_lb.head(3).copy()
            top_3_lm['Rank'] = [get_ordinal(i + 1) for i in range(len(top_3_lm))]
            top_3_lm = top_3_lm[['Rank', 'Beer Owner', 'Number of Beers']]

            st.dataframe(top_3_lm, use_container_width=True, hide_index=True)
        else:
            st.info("No beers logged in the last 30 days.")

    st.divider()

    # --- SECTION 3: LINE CHART & DAILY VOLUME CALENDAR ---

    col_line, col_cal = st.columns([3, 2], gap="large")

    with col_line:
        # cumulative line chart
        st.subheader("Cumulative Beers Over Time")
        daily_counts_df = df.set_index('Datetime').resample('D').size().cumsum().reset_index()
        daily_counts_df.columns = ['Date', 'Total Beers']

        fig_line = px.line(daily_counts_df, x='Date', y='Total Beers', template="plotly_dark")
        fig_line.update_traces(line_color=GLOBAL_COLOUR, line_width=3)
        fig_line.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", yaxis_title="", height=320)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_cal:
        st.subheader("Daily Volume")


        def build_calendar_data(input_df):
            """builds a mon-sun x week grid of daily beer counts."""
            daily_series = input_df.groupby(input_df['Datetime'].dt.date).size()

            today_date = datetime.now(timezone.utc).date()
            start_dt = daily_series.index.min()

            pad_start_dt = start_dt - pd.Timedelta(days=start_dt.weekday())
            pad_end_dt = today_date + pd.Timedelta(days=(6 - today_date.weekday()))
            full_date_range = pd.date_range(pad_start_dt, pad_end_dt, freq='D')

            total_weeks = len(full_date_range) // 7
            z_grid = [[None] * total_weeks for _ in range(7)]
            hover_text = [[""] * total_weeks for _ in range(7)]
            months_dict = {}

            last_month_str = None
            for idx, d_obj in enumerate(full_date_range):
                w_idx = idx // 7
                d_idx = d_obj.weekday()
                d_only = d_obj.date()

                # hide future dates or dates before the challenge started
                if d_only > today_date or d_only < start_dt:
                    val = None
                else:
                    val = int(daily_series.get(d_only, 0))

                z_grid[d_idx][w_idx] = val
                beer_label = "beer" if val == 1 else "beers"
                hover_text[d_idx][w_idx] = (
                    f"{d_obj.strftime('%a %d %b %Y')}<br>"
                    f"{'No data yet' if val is None else f'{val} {beer_label}'}"
                )

                if d_obj.day == 1 or idx == 0:
                    if d_obj.strftime('%b') != last_month_str:
                        months_dict[w_idx] = d_obj.strftime('%b')
                        last_month_str = d_obj.strftime('%b')

            current_today_pos = None
            for idx, d_obj in enumerate(full_date_range):
                if d_obj.date() == today_date:
                    current_today_pos = (idx % 7, idx // 7)
                    break

            return z_grid, hover_text, months_dict, total_weeks, current_today_pos, daily_series


        # generate calendar data
        z_data, hover_data, month_labels, num_weeks, today_position, raw_daily_counts = build_calendar_data(df)
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        max_daily_count = max(1, raw_daily_counts.max())
        eps = 0.001

        # 1. Convert your GLOBAL_COLOUR hex into RGB numbers
        hex_color = GLOBAL_COLOUR.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        # 2. Build the color scale using Plotly's supported rgba() format
        heatmap_colors = [
            [0.0, "#161b22"],  # 0 beers: Dark grey background
            [eps, "#161b22"],  # Threshold anchor
            [eps, f"rgba({r}, {g}, {b}, 0.25)"],  # Low beers: 25% opacity
            [0.5, f"rgba({r}, {g}, {b}, 0.60)"],  # Mid beers: 60% opacity
            [1.0, f"rgb({r}, {g}, {b})"]  # Max beers: 100% solid global color
        ]

        fig_cal = go.Figure(data=go.Heatmap(
            z=z_data,
            x=list(range(num_weeks)),
            y=day_labels,
            text=hover_data,
            hoverinfo='text',
            colorscale=heatmap_colors,
            zmin=0,
            zmax=max_daily_count,
            xgap=3,
            ygap=3,
            showscale=True,
            colorbar=dict(title="Beers", thickness=10, len=0.5, tickmode='array'),
        ))

        fig_cal.update_layout(
            template="plotly_dark",
            margin=dict(l=0, r=0, t=40, b=0),
            height=280,
            xaxis=dict(
                showgrid=False,
                tickmode='array',
                tickvals=list(month_labels.keys()),
                ticktext=list(month_labels.values()),
                side='top',
                tickfont=dict(size=11),
            ),
            yaxis=dict(showgrid=False, autorange='reversed', tickfont=dict(size=10)),
        )

        # outline the current day
        if today_position:
            day_coord, week_coord = today_position
            fig_cal.add_shape(
                type="rect",
                x0=week_coord - 0.5, x1=week_coord + 0.5,
                y0=day_coord - 0.5, y1=day_coord + 0.5,
                line=dict(color="white", width=2),
            )

        st.plotly_chart(fig_cal, use_container_width=True)

    st.divider()

    # --- SECTION 4: TEMPORAL ANALYTICS ---

    col_time1, col_time2 = st.columns(2)

    # create a localized copy of df to prevent adding temporary columns to the main dataset
    temporal_df = df.copy()

    with col_time1:
        st.subheader("Peak Beer Times (UTC)")

        # define the exact order for the x-axis (5 AM to 4 AM)
        custom_hour_order = [
            "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM",
            "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM",
            "9 PM", "10 PM", "11 PM", "12 AM", "1 AM", "2 AM", "3 AM", "4 AM"
        ]

        # create a mapping dictionary to convert 24h time to friendly labels
        hour_mapping = {
            5: "5 AM", 6: "6 AM", 7: "7 AM", 8: "8 AM", 9: "9 AM", 10: "10 AM", 11: "11 AM",
            12: "12 PM", 13: "1 PM", 14: "2 PM", 15: "3 PM", 16: "4 PM", 17: "5 PM", 18: "6 PM",
            19: "7 PM", 20: "8 PM", 21: "9 PM", 22: "10 PM", 23: "11 PM", 0: "12 AM",
            1: "1 AM", 2: "2 AM", 3: "3 AM", 4: "4 AM"
        }

        # extract the hour and map it
        temporal_df['Hour_Label'] = temporal_df['Datetime'].dt.hour.map(hour_mapping)

        # count beers per hour
        hourly_counts_df = temporal_df['Hour_Label'].value_counts().reset_index()
        hourly_counts_df.columns = ['Time', 'Beers']

        # build the chart forcing the custom x-axis order
        fig_hours = px.bar(
            hourly_counts_df,
            x='Time',
            y='Beers',
            category_orders={"Time": custom_hour_order}
        )

        fig_hours.update_traces(marker_color=GLOBAL_COLOUR)
        fig_hours.update_layout(xaxis_title="Hour of Day", yaxis_title="Total Beers")

        st.plotly_chart(fig_hours, use_container_width=True)

    with col_time2:
        st.subheader("Peak Beer Days (UTC)")

        # group by day of week and enforce monday-sunday order
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        temporal_df['Day'] = temporal_df['Datetime'].dt.day_name()

        day_counts_df = temporal_df['Day'].value_counts().reindex(days_order, fill_value=0).reset_index()
        day_counts_df.columns = ['Day', 'Count']

        fig_days = px.bar(day_counts_df, x='Day', y='Count', template="plotly_dark")
        fig_days.update_traces(marker_color=GLOBAL_COLOUR)
        fig_days.update_layout(xaxis_title="Day of Week", yaxis_title="Total Beers")
        st.plotly_chart(fig_days, use_container_width=True)

with tab2:
    # --- SECTION 5: FULL BEER LIST ---

    # 1. get the list of owners sorted by who has the most beers (descending)
    owner_counts = df['Beer Owner'].value_counts()
    sorted_owners = owner_counts.index.tolist()

    # using unicode bold characters so it renders properly in the dropdown
    filter_options = ["𝗔𝗹𝗹"] + sorted_owners

    # 2. create two columns with the [2, 1] scale
    col_title, col_filter = st.columns([2, 1], vertical_alignment="bottom")

    with col_title:
        st.subheader("Beer List")

    with col_filter:
        # css to make the popover look like a standard left-aligned dropdown
        # AND successfully target the first <label> to create the divider gap
        st.markdown("""
            <style>
            /* Left-align the popover button text */
            div[data-testid="stPopover"] button {
                justify-content: flex-start !important;
            }
            div[data-testid="stPopover"] button p {
                text-align: left !important;
            }
            /* Add gap and line under the first radio option ("All") */
            div[role="radiogroup"] > label:first-of-type {
                margin-bottom: 12px !important;
                padding-bottom: 12px !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # replace selectbox with a popover + radio to prevent the mobile keyboard
        with st.popover("Filter by Beer Owner", use_container_width=True):
            selected_owner = st.radio(
                "Filter by Person:",
                filter_options,
                label_visibility="collapsed"
            )

    # 3. add a small gap between the title row and the table
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 4. establish the base chronological list to lock in the correct overall 'beer #'
    full_beers_list = df.sort_values(by="Datetime", ascending=False).copy()
    full_beers_list = full_beers_list.reset_index(drop=True)
    full_beers_list["Beer #"] = range(len(full_beers_list), 0, -1)

    # 5. apply the filter if a specific person is selected (checking against the unicode string)
    if selected_owner != "𝗔𝗹𝗹":
        full_beers_list = full_beers_list[full_beers_list['Beer Owner'] == selected_owner]

    # 6. format dates and times for display
    full_beers_list['Date'] = full_beers_list['Datetime'].dt.strftime('%d %b %Y')
    full_beers_list['Time (UTC)'] = full_beers_list['Datetime'].dt.strftime('%H:%M')

    # 7. lock in the final columns
    final_display_df = full_beers_list[['Beer #', 'Beer Owner', 'Date', 'Time (UTC)']]

    st.dataframe(
        final_display_df,
        use_container_width=True,
        hide_index=True,
        height=700
    )

    # dynamically update the caption to show how many beers are visible vs the overall total
    st.caption(f"Showing {len(final_display_df):,} of {len(df):,} total beers")

