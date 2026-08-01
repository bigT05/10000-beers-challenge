import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
# from dateutil.relativedelta import relativedelta
# import math

# ----------------------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------------------
st.set_page_config(page_title="10,000 Beers Challenge", page_icon="🍻", layout="wide")

# Custom CSS for the Green Progress Bar, Podium, Page Padding, and Headers
st.markdown("""
    <style>
    /* UN-FIX THE MAIN HEADER AND MAKE IT TRANSPARENT */
    header[data-testid="stHeader"] {
        position: absolute !important;
        background-color: transparent !important;
        z-index: 99999 !important;
    }
    /* MAKE SIDEBAR HEADER TRANSPARENT BUT KEEP IT IN PLACE SO IT'S CLICKABLE */
    [data-testid="stSidebarHeader"] {
        background-color: transparent !important;
        padding-bottom: 0rem !important;
    }
    /* THIS REMOVES THE GAP AT THE TOP OF THE MAIN PAGE */
    .block-container {
        padding-top: 2rem !important;
    }
    /* THIS REMOVES THE GAP AT THE TOP OF THE SIDEBAR */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0rem !important; 
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }
    /* Existing green bar styling */
    .stProgress > div > div > div > div {
        background-color: #28a745; 
    }
    /* UPDATED PODIUM STYLING (No more h2/h3 tags) */
    .podium-box {
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background-color: #1e1e1e;
        border: 1px solid #333;
    }
    .first-place { border-top: 5px solid #FFD700; margin-top: 0px; }
    .second-place { border-top: 5px solid #C0C0C0; margin-top: 30px; }
    .third-place { border-top: 5px solid #CD7F32; margin-top: 50px; }
    /* New Custom Text Sizes to replace headers */
    .podium-title { font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .podium-name { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; }
    .podium-score { font-size: 1rem; color: #e0e0e0; margin: 0px; }
    /* HIDE STREAMLIT HEADER ANCHOR LINKS */
    a.header-anchor {
        display: none !important;
    }
    /* HIDE STREAMLIT HEADER ANCHOR LINKS (BRUTE FORCE) */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
        display: none !important;
    }

    /* Just in case Streamlit is using an SVG icon wrapper */
    .stMarkdown a svg {
        display: none !important;
    }
    /* REMOVES THE CURVED EDGES AND WHITE BORDER */
    .stApp {
        border: none !important;
        border-radius: 0px !important;
    }

    /* Ensures no background bleed from the embed wrapper */
    [data-testid="stAppViewContainer"] {
        border: none !important;
        border-radius: 0px !important;
    }

    #root > div:first-child,
    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stAppViewBlockContainer"] {
        border: none !important;
        border-radius: 0px !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* PODIUM REORDER - scoped ONLY to the podium container, desktop only */
    @media (min-width: 641px) {
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) { order: 2; }
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) { order: 1; }
        .st-key-podium_container div[data-testid="stHorizontalBlock"] > div:nth-of-type(3) { order: 3; }
        .st-key-podium_container div[data-testid="stHorizontalBlock"] { display: flex !important; }
    }
    
    /* PODIUM MOBILE COMPACT STYLING */
    @media (max-width: 640px) {
        /* Shrink the gap between stacked podium columns */
        .st-key-podium_container div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        .st-key-podium_container div[data-testid="column"] {
            gap: 0.5rem !important;
        }

        /* Force all three podium boxes to the same, smaller height on mobile */
        .st-key-podium_container .podium-box {
            height: 140px !important;
            padding: 12px !important;
            margin-top: 10px !important;
        }

        /* Shrink text sizes to fit better on small screens */
        .st-key-podium_container .podium-title {
            font-size: 1.3rem !important;
            margin-bottom: 4px !important;
        }
        .st-key-podium_container .podium-name {
            font-size: 1.1rem !important;
            margin-bottom: 4px !important;
        }
        .st-key-podium_container .podium-score {
            font-size: 0.85rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)
# ----------------------------------------------------------------------
# CONFIGURATION & DATA LOADING
# ----------------------------------------------------------------------
# This is your live Dropbox link with dl=1 at the end!
DROPBOX_DIRECT_URL = "https://www.dropbox.com/scl/fi/tpe7i2bigitq60e26azib/10000-Beers-Log.xlsx?rlkey=sjpkb7is0iqnvxgn67lemu93i&st=6l44nkqh&dl=1"
MACRO_GOAL = 10000

@st.cache_data(ttl=300,show_spinner="Fetching fresh beers...")  # Cache data for 5 mins to prevent constant reloading
def load_data():
    try:
        # Load Main Beers List directly from Dropbox
        df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Beers List", engine='openpyxl')

        # Drop rows where Beer Owner is blank (instead of dropping blank dates)
        df = df.dropna(subset=['Beer Owner'])

        # Load Metadata first so we know the last sync time for fallbacks
        try:
            meta_df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Metadata", header=None, engine='openpyxl')

            manual_date = str(meta_df.iloc[1, 1]).strip()
            manual_time = str(meta_df.iloc[1, 2]).strip()
            manual_sync_dt = pd.to_datetime(f"{manual_date} {manual_time}", dayfirst=True, errors='coerce')
            if pd.notna(manual_sync_dt):
                manual_sync_dt = manual_sync_dt.replace(tzinfo=timezone.utc)
            else:
                manual_sync_dt = pd.NaT

            sync_date = str(meta_df.iloc[2, 1]).strip()
            sync_time = str(meta_df.iloc[2, 2]).strip()
            last_sync_dt = pd.to_datetime(f"{sync_date} {sync_time}", dayfirst=True, errors='coerce')
            if pd.notna(last_sync_dt):
                last_sync_dt = last_sync_dt.replace(tzinfo=timezone.utc)
            else:
                last_sync_dt = pd.NaT

        except Exception:
            last_sync_dt = pd.NaT
            manual_sync_dt = pd.NaT

        # --- HANDLE MISSING DATES / TIMES ---
        # Mark which rows are missing timestamps
        df['Is_Fallback_Time'] = df['Date of Beer (UTC)'].isna() | df['Time of Beer (UTC)'].isna()

        # Fallback fallback: if metadata is missing, use current UTC time
        fallback_dt = manual_sync_dt if pd.notna(manual_sync_dt) else datetime.now(timezone.utc)
        fallback_date_str = fallback_dt.strftime('%d/%m/%Y')
        fallback_time_str = fallback_dt.strftime('%H:%M:%S')

        # Fill missing values
        df['Date of Beer (UTC)'] = df['Date of Beer (UTC)'].fillna(fallback_date_str)
        df['Time of Beer (UTC)'] = df['Time of Beer (UTC)'].fillna(fallback_time_str)

        # --- NORMALIZE MIXED FORMATS ---
        normalized_dates = pd.to_datetime(df['Date of Beer (UTC)'], dayfirst=True, errors='coerce')
        normalized_times = df['Time of Beer (UTC)'].astype(str)
        df['Datetime'] = pd.to_datetime(
            normalized_dates.dt.strftime('%Y-%m-%d') + " " + normalized_times,
            errors='coerce'
        )

        # Drop any failed conversions and sort chronologically
        df = df.dropna(subset=['Datetime']).sort_values(by="Datetime").reset_index(drop=True)

        # Ensure UTC timezone awareness
        df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')

        return df, last_sync_dt, manual_sync_dt

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.NaT, pd.NaT

df, last_sync_dt, manual_sync_dt = load_data()

# Stop execution if data is empty
if df.empty:
    st.warning("No data found. Please check your Excel file.")
    st.stop()

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def time_ago(timestamp):
    """Converts a datetime into a relative 'time ago' string."""
    if pd.isna(timestamp):
        return "Never"

    now = datetime.now(timezone.utc)
    diff = now - timestamp
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(max(0, seconds))} secs ago"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins} min{'s' if mins > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"


def format_custom_date(dt):
    """Converts a datetime object to '7th September 2029' format"""
    if pd.isna(dt):
        return "Unknown"

    day = dt.day
    # Figure out the st, nd, rd, th
    if 11 <= (day % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # %B gets the full capitalized month name (e.g., 'September')
    month = dt.strftime('%B')
    year = dt.year

    return f"{day}{suffix} {month} {year}"

# ----------------------------------------------------------------------
# SIDEBAR: FEED & STATUS
# ----------------------------------------------------------------------
with st.sidebar:
    # (Optional) If you still have your Breakfast Boys logo image code here, leave it at the top!

    st.image("profile.jpg", clamp=True)  # Placeholder logo

    st.divider()

    # --- 1. RECENT CHECK-INS ---
    st.subheader("Recent Beers* 🍺", anchor=False)
    recent_beers = df.sort_values(by="Datetime", ascending=False).head(10)
    for _, row in recent_beers.iterrows():
        # If the date/time was missing in Excel, display "recently"
        if row.get('Is_Fallback_Time', False):
            time_display = "recently"
        else:
            time_display = time_ago(row['Datetime'])

        st.markdown(f"**{row['Beer Owner']}** - *{time_display}*")

    st.divider()

    # --- 2. SYSTEM STATUS (Moved to bottom) ---
    st.subheader("System Status")
    st.info(f"***Last Spreadsheet Update:**\n\n*{time_ago(manual_sync_dt)}*")
    st.success(f"**Last Time Sync:**\n\n*{time_ago(last_sync_dt)}*")

    # REFRESH BUTTON
    if st.button("Force Data Refresh", use_container_width=True):
        st.cache_data.clear()  # This deletes the frozen 5-minute data
        st.rerun()  # This instantly reloads the page with fresh data

# ----------------------------------------------------------------------
# MAIN DASHBOARD
# ----------------------------------------------------------------------
st.markdown("<h1 style='text-align: center;'>🍻 10,000 Beers Challenge 🍻</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Summary", "Full Beer List"])

with tab1:

    # --- SECTION 1: BEER PROGRESS CHART ---

    total_beers = len(df)
    progress_pct = total_beers / MACRO_GOAL

    # Extrapolation Logic
    first_beer_time = df['Datetime'].min()
    now_time = datetime.now(timezone.utc)
    days_elapsed = (now_time - first_beer_time).total_seconds() / 86400

    if days_elapsed > 0:
        beers_per_day = total_beers / days_elapsed
        beers_left = MACRO_GOAL - total_beers
        days_left = beers_left / beers_per_day
        eta_date = now_time + pd.Timedelta(days=days_left)

        # Pass the raw date object into our new function here!
        eta_str = format_custom_date(eta_date)

        velocity_str = f"{beers_per_day:.1f} beers/day"
    else:
        eta_str = "TBD"
        velocity_str = "TBD"

    st.subheader("Beer Progress Bar")
    st.progress(min(progress_pct, 1.0))
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Beers So Far", f"{total_beers:,} / {MACRO_GOAL:,}")
    col2.metric("Current Flow of Beer", velocity_str)
    col3.metric("Estimated Finish Date", eta_str)

    st.divider()


    # --- SECTION 2: LEADERBOARD & PIE CHART ---

    # Quick helper function to generate 4th, 5th, etc. for the table
    def get_ordinal(n):
        if 11 <= (n % 100) <= 13:
            return str(n) + "th"
        return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


    # col_left is slightly wider to give the podium and table room to breathe
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.subheader("All-Time Leaderboard 🏆")

        # Calculate Leaderboard totals
        leaderboard = df['Beer Owner'].value_counts().reset_index()
        leaderboard.columns = ['Beer Owner', 'Number of Beers']

        # Calculate total days the challenge has been running
        total_days = max(1, (pd.Timestamp.now(tz='UTC') - df['Datetime'].min()).days)
        leaderboard['Beers / Day'] = (leaderboard['Number of Beers'] / total_days).round(1)

        # Extract Top 3 data safely
        top_3_names = leaderboard['Beer Owner'].head(3).tolist()
        top_3_scores = leaderboard['Number of Beers'].head(3).tolist()
        top_3_bpd = leaderboard['Beers / Day'].head(3).tolist()

        # Pad with blanks if fewer than 3 people have drank so far
        while len(top_3_names) < 3:
            top_3_names.append("N/A")
            top_3_scores.append(0)
            top_3_bpd.append(0.0)

        # -- THE TOP 3 PODIUM (HTML STYLE) --
        # vertical_alignment="bottom" ensures they all sit on the exact same baseline!
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

        # -- THE CONTENDERS (4th place onward) --
        #st.markdown("#### The Contenders")
        if len(leaderboard) > 3:
            rest_of_pack = leaderboard.iloc[3:].copy()

            # Apply the ordinal function to create a "Rank" column
            rest_of_pack['Rank'] = [get_ordinal(i + 4) for i in range(len(rest_of_pack))]

            # Reorder the dataframe columns so 'Rank' is first
            rest_of_pack = rest_of_pack[['Rank', 'Beer Owner', 'Number of Beers', 'Beers / Day']]

            st.dataframe(
                rest_of_pack,
                use_container_width=True,
                hide_index=True
            )

    with col_right:
        # -- PIE CHART --
        st.subheader("Percentage Contribution")
        fig_pie = px.pie(leaderboard, values='Number of Beers', names='Beer Owner', template="plotly_dark", hole=0.3)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # -- TOP 3 LAST 30 DAYS --
        st.subheader("Last 30 Days: Top 3")

        # Filter data for the last 30 days
        now = pd.Timestamp.now(tz='UTC')
        last_month_start = now - pd.DateOffset(days=30)
        last_month_df = df[df['Datetime'] >= last_month_start]

        if not last_month_df.empty:
            last_month_lb = last_month_df['Beer Owner'].value_counts().reset_index()
            last_month_lb.columns = ['Beer Owner', 'Number of Beers']

            # Isolate the top 3 and make a copy to edit safely
            top_3_lm = last_month_lb.head(3).copy()

            # Apply the ordinal function (1st, 2nd, 3rd)
            top_3_lm['Rank'] = [get_ordinal(i + 1) for i in range(len(top_3_lm))]

            # Reorder columns so Rank is first
            top_3_lm = top_3_lm[['Rank', 'Beer Owner', 'Number of Beers']]

            st.dataframe(top_3_lm, use_container_width=True, hide_index=True)
        else:
            st.info("No beers logged in the last 30 days.")

    st.divider()
    # --- SECTION 3: LINE CHART + DAILY VOLUME CALENDAR ---

    col_line, col_cal = st.columns([3, 2], gap="large")

    with col_line:
        # Cumulative Line Chart
        st.subheader("Cumulative Beers Over Time")
        df_daily = df.set_index('Datetime').resample('D').size().cumsum().reset_index()
        df_daily.columns = ['Date', 'Total Beers']
        fig_line = px.line(df_daily, x='Date', y='Total Beers', template="plotly_dark")
        fig_line.update_traces(line_color='#28a745', line_width=3)
        fig_line.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", yaxis_title="", height=320)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_cal:
        st.subheader("Daily Volume")

        def build_calendar_data(df):
            """Builds a Mon-Sun x Week grid of daily beer counts."""
            daily_counts = df.groupby(df['Datetime'].dt.date).size()

            today = datetime.now(timezone.utc).date()
            start_date = daily_counts.index.min()

            pad_start = start_date - pd.Timedelta(days=start_date.weekday())
            pad_end = today + pd.Timedelta(days=(6 - today.weekday()))
            full_range = pd.date_range(pad_start, pad_end, freq='D')

            n_weeks = len(full_range) // 7
            z = [[None] * n_weeks for _ in range(7)]
            hover = [[""] * n_weeks for _ in range(7)]
            month_labels = {}

            last_month = None
            for i, d in enumerate(full_range):
                week_idx = i // 7
                day_idx = d.weekday()
                date_only = d.date()

                if date_only > today or date_only < start_date:
                    val = None  # future OR before the challenge started -> hidden
                else:
                    val = int(daily_counts.get(date_only, 0))

                z[day_idx][week_idx] = val
                beer_word = "beer" if val == 1 else "beers"
                hover[day_idx][week_idx] = (
                    f"{d.strftime('%a %d %b %Y')}<br>"
                    f"{'No data yet' if val is None else f'{val} {beer_word}'}"
                )

                if d.day == 1 or i == 0:
                    if d.strftime('%b') != last_month:
                        month_labels[week_idx] = d.strftime('%b')
                        last_month = d.strftime('%b')

            today_pos = None
            for i, d in enumerate(full_range):
                if d.date() == today:
                    today_pos = (i % 7, i // 7)
                    break

            return z, hover, month_labels, n_weeks, today_pos, daily_counts


        z, hover, month_labels, n_weeks, today_pos, daily_counts = build_calendar_data(df)
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        max_count = max(1, daily_counts.max())
        epsilon = 0.001

        colorscale = [
            [0.0, "#161b22"],
            [epsilon, "#161b22"],
            [epsilon, "#0e4429"],
            [0.35, "#006d32"],
            [0.6, "#26a641"],
            [0.8, "#39d353"],
            [1.0, "#57eb6a"],
        ]

        fig_cal = go.Figure(data=go.Heatmap(
            z=z,
            x=list(range(n_weeks)),
            y=day_labels,
            text=hover,
            hoverinfo='text',
            colorscale=colorscale,
            zmin=0,
            zmax=max_count,
            xgap=3,
            ygap=3,
            showscale=True,
            colorbar=dict(
                title="Beers",
                thickness=10,
                len=0.5,
                tickmode='array',
            ),
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

        if today_pos:
            day_idx, week_idx = today_pos
            fig_cal.add_shape(
                type="rect",
                x0=week_idx - 0.5, x1=week_idx + 0.5,
                y0=day_idx - 0.5, y1=day_idx + 0.5,
                line=dict(color="white", width=2),
            )

        st.plotly_chart(fig_cal, use_container_width=True)

    st.divider()

    # --- SECTION 4: LAST MONTH ---

    #
    # # Last Month's Top 3 Podium
    # st.subheader("Last Month's Top 3 Beer Drinkers")
    # last_month = datetime.now(timezone.utc) - relativedelta(months=1)
    # lm_df = df[(df['Datetime'].dt.month == last_month.month) & (df['Datetime'].dt.year == last_month.year)]
    #
    # if not lm_df.empty:
    #     lm_leaderboard = lm_df['Beer Owner'].value_counts()
    #     top_3 = lm_leaderboard.head(3).index.tolist()
    #     counts = lm_leaderboard.head(3).tolist()
    #
    #     # Pad with blanks if fewer than 3 people drank last month
    #     while len(top_3) < 3:
    #         top_3.append("N/A")
    #         counts.append(0)
    #
    #     pod1, pod2, pod3 = st.columns(3)
    #     with pod1:
    #         st.markdown(f"<div class='podium-box second-place'><div class='podium-title'>2nd 🥈</div><div class='podium-name'>{top_3[1]}</div><div class='podium-score'>{counts[1]} beers</div></div>", unsafe_allow_html=True)
    #     with pod2:
    #         st.markdown(f"<div class='podium-box first-place'><div class='podium-title'>1st 🥇</div><div class='podium-name'>{top_3[0]}</div><div class='podium-score'>{counts[0]} beers</div></div>", unsafe_allow_html=True)
    #     with pod3:
    #         st.markdown(f"<div class='podium-box third-place'><div class='podium-title'>3rd 🥉</div><div class='podium-name'>{top_3[2]}</div><div class='podium-score'>{counts[2]} beers</div></div>", unsafe_allow_html=True)
    # else:
    #     st.info("No beers were logged last month to calculate a podium.")
    #
    # st.divider()

    # --- SECTION 5: TEMPORAL ANALYTICS ---
    col_time1, col_time2 = st.columns(2)

    with col_time1:
        # --- PEAK BEER TIMES CHART ---
        st.subheader("Peak Beer Times (UTC)")

        # 1. Define the exact order you want the x-axis to follow (5 AM to 4 AM)
        custom_hour_order = [
            "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM",
            "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM",
            "9 PM", "10 PM", "11 PM", "12 AM", "1 AM", "2 AM", "3 AM", "4 AM"
        ]

        # 2. Create a mapping dictionary to convert the 0-23 military time to our labels
        hour_mapping = {
            5: "5 AM", 6: "6 AM", 7: "7 AM", 8: "8 AM", 9: "9 AM", 10: "10 AM", 11: "11 AM",
            12: "12 PM", 13: "1 PM", 14: "2 PM", 15: "3 PM", 16: "4 PM", 17: "5 PM", 18: "6 PM",
            19: "7 PM", 20: "8 PM", 21: "9 PM", 22: "10 PM", 23: "11 PM", 0: "12 AM",
            1: "1 AM", 2: "2 AM", 3: "3 AM", 4: "4 AM"
        }

        # 3. Extract the hour from your Datetime and map it to the friendly labels
        df['Hour_Num'] = df['Datetime'].dt.hour
        df['Hour_Label'] = df['Hour_Num'].map(hour_mapping)

        # 4. Count the beers per hour
        hourly_counts = df['Hour_Label'].value_counts().reset_index()
        hourly_counts.columns = ['Time', 'Beers']

        # 5. Build the chart, forcing the x-axis to use our custom_hour_order
        fig_hours = px.bar(
            hourly_counts,
            x='Time',
            y='Beers',
            category_orders={"Time": custom_hour_order}  # THIS IS THE MAGIC LINE
        )

        # Optional: Make it look clean and green to match the rest of your app
        fig_hours.update_traces(marker_color='#28a745')
        fig_hours.update_layout(xaxis_title="Hour of Day", yaxis_title="Total Beers")

        st.plotly_chart(fig_hours, use_container_width=True)

    with col_time2:
        st.subheader("Peak Beer Days (UTC)")
        # Group by Day of Week and enforce order Mon-Sun
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['Day'] = df['Datetime'].dt.day_name()
        day_counts = df['Day'].value_counts().reindex(days_order, fill_value=0).reset_index()
        day_counts.columns = ['Day', 'Count']

        fig_days = px.bar(day_counts, x='Day', y='Count', template="plotly_dark")
        fig_days.update_traces(marker_color='#17a2b8')
        fig_days.update_layout(xaxis_title="Day of Week", yaxis_title="Total Beers")
        st.plotly_chart(fig_days, use_container_width=True)


with tab2:
    st.subheader("Beer List")

    full_list = df.sort_values(by="Datetime", ascending=False).copy()
    full_list = full_list.reset_index(drop=True)

    # Assign directly (overwrites if it somehow already exists, never raises)
    full_list["Beer #"] = range(len(full_list), 0, -1)

    full_list['Date'] = full_list['Datetime'].dt.strftime('%d %b %Y')
    full_list['Time (UTC)'] = full_list['Datetime'].dt.strftime('%H:%M')

    display_df = full_list[['Beer #', 'Beer Owner', 'Date', 'Time (UTC)']]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=700
    )

    st.caption(f"Showing {len(display_df):,} of {len(full_list):,} total beers")