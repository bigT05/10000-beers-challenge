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

st.set_page_config(page_title="10,000 Beers Challenge", page_icon="🍻", layout="wide", initial_sidebar_state="expanded")

# custom css for SaaS, No-Scroll layout (Light/Dark Mode Compatible)
st.markdown(f"""
    <style>
    /* 1. HIDE DEFAULT STREAMLIT ELEMENTS & LINKS BUT KEEP BUTTONS */
    header[data-testid="stHeader"] {{ background-color: transparent !important; }}
    [data-testid="stSidebarHeader"] {{ padding-bottom: 0rem !important; padding-top: 1rem !important; }}
    .block-container {{ padding: 1rem 1rem 0rem 1rem !important; max-width: 100% !important; }}
    #root > div:first-child, .stApp {{ border: none !important; }}

    /* Nukes the link icons */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, h3 svg, h2 svg, h1 svg, a.header-anchor, .stMarkdown a svg {{ display: none !important; }}

    /* 2. COMPACT TABS */
    [data-testid="stTabs"] button {{ padding-top: 0rem !important; padding-bottom: 0rem !important; }}
    [data-testid="stTab"][aria-selected="true"] {{ color: {GLOBAL_COLOUR} !important; }}
    [data-testid="stTab"][aria-selected="true"] p {{ color: {GLOBAL_COLOUR} !important; font-weight: 700 !important; font-size: 1rem !important; }}
    [data-testid="stTab"]:not([aria-selected="true"]) p {{ font-size: 0.9rem !important; opacity: 0.7; }}
    .stTabs div[data-baseweb="tab-highlight"] {{ background-color: {GLOBAL_COLOUR} !important; height: 2px !important; }}

    /* 3. METRICS POP - SaaS STYLE */
    [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] {{
        color: {GLOBAL_COLOUR} !important; font-weight: 800 !important; font-size: 1.25rem !important; line-height: 1.1 !important;
    }}
    [data-testid="stMetricLabel"] {{ font-size: 0.8rem !important; opacity: 0.8 !important; margin-bottom: -5px !important; }}

    /* 4. REDUCE WHITE SPACE & HEADERS */
    h2 {{ color: {GLOBAL_COLOUR} !important; font-size: 1.6rem !important; margin: 0 !important; padding: 0 !important; }}
    h6 {{ font-size: 0.9rem !important; font-weight: 600 !important; margin: 0 0 5px 0 !important; padding: 0 !important; opacity: 0.9; }}
    .element-container {{ margin-bottom: 0px !important; }}
    .stMarkdown {{ margin-bottom: 0px !important; }}

    /* 5. FIX THE PROGRESS BAR COLOR (Restored old background style) */
    .stProgress > div > div:has(div[style*="translateX"]) {{ background-color: rgba(128, 128, 128, 0.15) !important; border: 1px solid rgba(128, 128, 128, 0.2) !important; border-radius: 4px !important; height: 10px !important; }}
    .stProgress div[style*="translateX"] {{ background-color: {GLOBAL_COLOUR} !important; height: 10px !important; border-radius: 4px !important; }}

    /* 6. SIDEBAR COMPACTNESS */
    [data-testid="stSidebar"] hr {{ margin: 0.5rem 0 !important; opacity: 0.2; border-bottom-color: {GLOBAL_COLOUR} !important; }}
    [data-testid="stSidebar"] p {{ font-size: 0.8rem !important; margin-bottom: 0.2rem !important; }}

    /* 7. CUSTOM SAAS PODIUM/CARDS (Restored distinct box backgrounds) */
    .podium-container {{ display: flex; gap: 8px; margin-bottom: 8px; }}
    .podium-box {{ flex: 1; text-align: center; padding: 6px; border-radius: 6px; background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); }}
    .first-place {{ border-top: 3px solid #FFD700; }}
    .second-place {{ border-top: 3px solid #C0C0C0; }}
    .third-place {{ border-top: 3px solid #CD7F32; }}
    .podium-title {{ font-size: 0.75rem; font-weight: bold; margin-bottom: 2px; color: var(--text-color); }}
    .podium-name {{ font-size: 0.9rem; font-weight: bold; margin-bottom: 0px; color: var(--text-color); }}
    .podium-score {{ font-size: 0.8rem; color: {GLOBAL_COLOUR}; margin: 0px; font-weight: 600; line-height: 1.1; }}

    /* 8. REDUCE STREAMLIT CONTAINER PADDING */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{ padding: 0.7rem !important; border-radius: 8px !important; }}

    /* 9. POPOVER & DATAFRAME STYLING */
    [data-testid="stDataFrame"] {{ margin-bottom: 0px !important; }}
    div[data-testid="stPopover"] button {{ justify-content: flex-start !important; }}
    div[data-testid="stPopover"] button p {{ text-align: left !important; }}
    div[role="radiogroup"] > label:first-of-type {{ margin-bottom: 12px !important; padding-bottom: 12px !important; border-bottom: 1px solid var(--border-color) !important; }}
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# CONFIGURATION & DATA LOADING
# ----------------------------------------------------------------------

DROPBOX_DIRECT_URL = "https://www.dropbox.com/scl/fi/m69ohs691eb8zbkdzsg9z/10000-beers-log.xlsx?rlkey=n7buk0hfmsubo7ivkz6qyf97s&st=2v1r6dop&dl=1"
BEER_GOAL = 10000


@st.cache_data(ttl=300, show_spinner="Fetching fresh beers...")
def load_data():
    try:
        beers_df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Beers List", engine='openpyxl')
        beers_df = beers_df.dropna(subset=['Beer Owner'])

        parsed_last_sync = pd.NaT
        parsed_manual_sync = pd.NaT

        try:
            meta_df = pd.read_excel(DROPBOX_DIRECT_URL, sheet_name="Metadata", header=None, engine='openpyxl')

            def format_date_str(val):
                if pd.isna(val): return ""
                if isinstance(val, (int, float)): return (pd.to_datetime('1899-12-30') + pd.Timedelta(days=val)).strftime('%d/%m/%Y')
                if isinstance(val, (pd.Timestamp, datetime)): return val.strftime('%d/%m/%Y')
                return str(val).strip()

            parsed_manual_sync = pd.to_datetime(f"{format_date_str(meta_df.iloc[1, 1])} {str(meta_df.iloc[1, 2]).strip()}", dayfirst=True, errors='coerce')
            if pd.notna(parsed_manual_sync): parsed_manual_sync = parsed_manual_sync.replace(tzinfo=timezone.utc)

            parsed_last_sync = pd.to_datetime(f"{format_date_str(meta_df.iloc[2, 1])} {str(meta_df.iloc[2, 2]).strip()}", dayfirst=True, errors='coerce')
            if pd.notna(parsed_last_sync): parsed_last_sync = parsed_last_sync.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        beers_df['Is_Fallback_Time'] = beers_df['Date of Beer (UTC)'].isna() | beers_df['Time of Beer (UTC)'].isna()
        fallback_dt = parsed_manual_sync if pd.notna(parsed_manual_sync) else datetime.now(timezone.utc)

        beers_df['Date of Beer (UTC)'] = beers_df['Date of Beer (UTC)'].fillna(fallback_dt.strftime('%d/%m/%Y')).apply(format_date_str)
        beers_df['Time of Beer (UTC)'] = beers_df['Time of Beer (UTC)'].fillna(fallback_dt.strftime('%H:%M:%S'))

        normalized_dates = pd.to_datetime(beers_df['Date of Beer (UTC)'], dayfirst=True, errors='coerce')
        beers_df['Datetime'] = pd.to_datetime(normalized_dates.dt.strftime('%Y-%m-%d') + " " + beers_df['Time of Beer (UTC)'].astype(str), errors='coerce')

        beers_df = beers_df.dropna(subset=['Datetime']).sort_values(by="Datetime").reset_index(drop=True)
        beers_df['Datetime'] = beers_df['Datetime'].dt.tz_localize('UTC')
        return beers_df, parsed_last_sync, parsed_manual_sync
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.NaT, pd.NaT


df, last_sync_dt, manual_sync_dt = load_data()

if df.empty:
    st.warning("No data found. Please check your Excel file.")
    st.stop()


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------

def time_ago(timestamp):
    if pd.isna(timestamp): return "Never"
    total_secs = (datetime.now(timezone.utc) - timestamp).total_seconds()
    if total_secs < 60:
        return f"{int(max(0, total_secs))}s ago"
    elif total_secs < 3600:
        return f"{int(total_secs // 60)}m ago"
    elif total_secs < 86400:
        return f"{int(total_secs // 3600)}h ago"
    else:
        return f"{int(total_secs // 86400)}d ago"


def format_custom_date(input_dt):
    if pd.isna(input_dt): return "Unknown"
    dt_day = input_dt.day
    day_suffix = "th" if 11 <= (dt_day % 100) <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(dt_day % 10, "th")
    return f"{dt_day}{day_suffix} {input_dt.strftime('%b %y')}"


def get_ordinal(rank_num):
    if 11 <= (rank_num % 100) <= 13: return str(rank_num) + "th"
    return str(rank_num) + {1: "st", 2: "nd", 3: "rd"}.get(rank_num % 10, "th")


# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------

with st.sidebar:
    st.image("assets/profile.jpg", clamp=True)
    st.markdown("---")

    st.markdown("###### Recent Beers 🍺")
    for _, beer_row in df.sort_values(by="Datetime", ascending=False).head(10).iterrows():
        display_time = "recently" if beer_row.get('Is_Fallback_Time', False) else time_ago(beer_row['Datetime'])
        st.markdown(f"<div style='font-size: 0.75rem; padding: 2px 0;'><b>{beer_row['Beer Owner']}</b> <span style='opacity:0.6; float:right;'>{display_time}</span></div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("###### System Status")
    st.markdown(f"""
        <div style="font-size: 0.75rem; margin-bottom: 10px;">
            <div style="opacity:0.7">Last Entry: <span style="color:{GLOBAL_COLOUR}; font-weight:bold; float:right;">{time_ago(manual_sync_dt)}</span></div>
            <div style="opacity:0.7">Last Sync: <span style="color:{GLOBAL_COLOUR}; font-weight:bold; float:right;">{time_ago(last_sync_dt)}</span></div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("↻ Reload", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ----------------------------------------------------------------------
# MAIN DASHBOARD
# ----------------------------------------------------------------------

# Title strictly above tabs, zero bottom margin for tighter spacing
st.markdown("<h2 style='margin-bottom: 0px;'>🍻 10,000 Beers Challenge</h2>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Dashboard", "Full Beer List"])

with tab1:
    # Add a tiny visual gap below tabs before rendering KPIs
    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

    # --- SAAS HEADER: TOP KPIs & PROGRESS ---
    total_beers = len(df)
    progress_pct = total_beers / BEER_GOAL
    first_beer_time = df['Datetime'].min()
    current_time = datetime.now(timezone.utc)
    days_elapsed = (current_time - first_beer_time).total_seconds() / 86400

    if days_elapsed > 0:
        beers_per_day = total_beers / days_elapsed
        eta_date = current_time + pd.Timedelta(days=(BEER_GOAL - total_beers) / beers_per_day)
        eta_str = format_custom_date(eta_date)
        velocity_str = f"{beers_per_day:.1f} beers / day"
    else:
        eta_str, velocity_str = "TBD", "TBD"

    # Encapsulated KPIs in boxes
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        with st.container(border=True):
            st.metric("Total Beers So Far", f"{total_beers:,} / {BEER_GOAL:,}")
    with col_kpi2:
        with st.container(border=True):
            st.metric("Flow of Beer", velocity_str)
    with col_kpi3:
        with st.container(border=True):
            st.metric("Estimated Finish Date", eta_str)

    # Progress bar HTML (Restored custom background block style)
    st.markdown(f"""
        <div style="background-color: rgba(128, 128, 128, 0.15); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 4px; height: 16px; width: 100%; position: relative; overflow: hidden; margin-top: 8px; margin-bottom: 16px;">
            <div style="background-color: {GLOBAL_COLOUR}; height: 100%; width: {min(progress_pct * 100, 100)}%;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; padding-left: 8px; font-size: 0.65rem; font-weight: 800; color: white; text-shadow: 0px 1px 2px rgba(0,0,0,0.8);">{math.floor(progress_pct * 100)}%</div>
        </div>
    """, unsafe_allow_html=True)

    # --- MAIN GRID: 3 COLUMNS ---
    c1, c2, c3 = st.columns([1.1, 1, 1.1])

    # COLUMN 1: LEADERBOARDS
    with c1:
        with st.container(border=True):
            st.markdown("###### All-Time Leaderboard")
            total_days = max(1, (pd.Timestamp.now(tz='UTC') - df['Datetime'].min()).days)
            lb_df = df['Beer Owner'].value_counts().reset_index()
            lb_df.columns = ['Name', 'Beers']
            lb_df['Spd'] = (lb_df['Beers'] / total_days).round(1)

            t_names = lb_df['Name'].tolist() + ["N/A"] * 3
            t_scores = lb_df['Beers'].tolist() + [0] * 3
            t_spd = lb_df['Spd'].tolist() + [0.0] * 3

            st.markdown(f"""
                <div class='podium-container'>
                    <div class='podium-box first-place'>
                        <div class='podium-title'>1st 🥇</div>
                        <div class='podium-name'>{t_names[0]}</div>
                        <div class='podium-score'>{t_scores[0]}<br><span style='font-size:0.65rem; color:var(--text-color); font-weight:normal; opacity:0.7;'>~{t_spd[0]} beers / day</span></div>
                    </div>
                    <div class='podium-box second-place'>
                        <div class='podium-title'>2nd 🥈</div>
                        <div class='podium-name'>{t_names[1]}</div>
                        <div class='podium-score'>{t_scores[1]}<br><span style='font-size:0.65rem; color:var(--text-color); font-weight:normal; opacity:0.7;'>~{t_spd[1]} beers / day</span></div>
                    </div>
                    <div class='podium-box third-place'>
                        <div class='podium-title'>3rd 🥉</div>
                        <div class='podium-name'>{t_names[2]}</div>
                        <div class='podium-score'>{t_scores[2]}<br><span style='font-size:0.65rem; color:var(--text-color); font-weight:normal; opacity:0.7;'>~{t_spd[2]} beers / day</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if len(lb_df) > 3:
                rest_df = lb_df.iloc[3:].copy()
                rest_df.insert(0, '#', [get_ordinal(i + 4) for i in range(len(rest_df))])
                # Height expanded to ~395px to align perfectly with the bottoms of cols 2 and 3
                st.dataframe(rest_df[['#', 'Name', 'Beers']], use_container_width=True, hide_index=True, height=395)

    # COLUMN 2: DISTRIBUTION & CALENDAR
    with c2:
        custom_colors = {"Tom": "#FFBA00", "Logan": "#D80030", "Archie": "#FF8A00", "Mills": "#00D5A0", "JJ": "#3461EF", "Moo": "#6DCFBA", "KSI": "#8936B6", "Ashton": "#A871FF", "Sam": "#E50184"}
        with st.container(border=True):
            st.markdown("###### Share of Total")
            fig_pie = px.pie(lb_df, values='Beers', names='Name', hole=0.4, color='Name', color_discrete_map=custom_colors)
            # Implemented texttemplate using HTML bold tags (<b>) to ensure crisp, bold lettering
            fig_pie.update_traces(textposition='inside', texttemplate='<b>%{label}<br>%{percent}</b>', insidetextfont=dict(color='white', size=11))
            fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=10), showlegend=False, height=225)
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        with st.container(border=True):
            st.markdown("###### Activity Heatmap")
            daily_series = df.groupby(df['Datetime'].dt.date).size()
            today_date = current_time.date()
            start_dt = daily_series.index.min()
            pad_start = start_dt - pd.Timedelta(days=start_dt.weekday())
            pad_end = today_date + pd.Timedelta(days=(6 - today_date.weekday()))
            dates = pd.date_range(pad_start, pad_end, freq='D')

            num_wks = len(dates) // 7
            z_grid = [[None] * num_wks for _ in range(7)]
            m_labels = {}
            l_month = None

            for i, d in enumerate(dates):
                if start_dt <= d.date() <= today_date: z_grid[d.weekday()][i // 7] = int(daily_series.get(d.date(), 0))
                if d.day == 1 or i == 0:
                    if d.strftime('%b') != l_month:
                        m_labels[i // 7] = d.strftime('%b')
                        l_month = d.strftime('%b')

            r, g, b = tuple(int(GLOBAL_COLOUR.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

            # Using neutral RGBA for zero-values works gracefully on both Light and Dark mode
            colors = [[0.0, "rgba(128, 128, 128, 0.15)"], [0.001, "rgba(128, 128, 128, 0.15)"], [0.001, f"rgba({r},{g},{b},0.3)"], [0.5, f"rgba({r},{g},{b},0.7)"], [1.0, f"rgb({r},{g},{b})"]]

            fig_cal = go.Figure(data=go.Heatmap(z=z_grid, colorscale=colors, zmin=0, zmax=max(1, daily_series.max()), xgap=1, ygap=1, showscale=False))
            fig_cal.update_layout(
                height=180, margin=dict(l=20, r=5, t=20, b=5),
                xaxis=dict(showgrid=False, zeroline=False, tickmode='array', tickvals=list(m_labels.keys()), ticktext=list(m_labels.values()), side='top', tickfont=dict(size=9)),
                yaxis=dict(showgrid=False, zeroline=False, autorange='reversed', ticktext=['M', 'T', 'W', 'T', 'F', 'S', 'S'], tickvals=[0, 1, 2, 3, 4, 5, 6], tickfont=dict(size=8))
            )
            st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

    # COLUMN 3: TRENDS & TEMPORAL
    with c3:
        with st.container(border=True):
            st.markdown("###### Cumulative Beers")
            daily_counts = df.set_index('Datetime').resample('D').size().cumsum().reset_index()
            daily_counts.columns = ['Date', 'Beers']
            fig_line = px.line(daily_counts, x='Date', y='Beers')
            fig_line.update_traces(line_color=GLOBAL_COLOUR, line_width=2, fill='tozeroy', fillcolor=f"rgba({r},{g},{b},0.1)")
            fig_line.update_layout(margin=dict(l=0, r=10, t=5, b=0), xaxis_title="", yaxis_title="", height=225, xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9)), yaxis=dict(zeroline=False, tickfont=dict(size=9)))
            st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        cc1, cc2 = st.columns(2)
        with cc1:
            with st.container(border=True):
                st.markdown("###### Peak Times (UTC)")
                hour_map = {h: f"{h % 12 or 12}{'AM' if h < 12 else 'PM'}" for h in range(24)}
                temp_df = df.copy()
                temp_df['Hr'] = temp_df['Datetime'].dt.hour.map(hour_map)
                order = [f"{h % 12 or 12}{'AM' if h < 12 else 'PM'}" for h in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4]]
                h_counts = temp_df['Hr'].value_counts().reset_index()
                fig_h = px.bar(h_counts, x='Hr', y='count', category_orders={"Hr": order})
                fig_h.update_traces(marker_color=GLOBAL_COLOUR)
                fig_h.update_layout(margin=dict(l=0, r=0, t=5, b=0), xaxis_title="", yaxis_title="", height=180, xaxis=dict(zeroline=False, tickfont=dict(size=8)), yaxis=dict(zeroline=False, visible=False))
                st.plotly_chart(fig_h, use_container_width=True, config={'displayModeBar': False})

        with cc2:
            with st.container(border=True):
                st.markdown("###### Peak Days (UTC)")
                temp_df['Day'] = temp_df['Datetime'].dt.day_name().str[:3]
                d_counts = temp_df['Day'].value_counts().reindex(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], fill_value=0).reset_index()
                fig_d = px.bar(d_counts, x='Day', y='count')
                fig_d.update_traces(marker_color=GLOBAL_COLOUR)
                fig_d.update_layout(margin=dict(l=0, r=0, t=5, b=0), xaxis_title="", yaxis_title="", height=180, xaxis=dict(zeroline=False, tickfont=dict(size=8)), yaxis=dict(zeroline=False, visible=False))
                st.plotly_chart(fig_d, use_container_width=True, config={'displayModeBar': False})

with tab2:
    # Add a visual gap before the list components
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    col_title2, col_filter = st.columns([4, 1], vertical_alignment="center")
    with col_title2:
        st.markdown("###### Complete Log Data")
    with col_filter:
        owners_sorted = df['Beer Owner'].value_counts().index.tolist()
        with st.popover("Filter Owner", use_container_width=True):
            selected_owner = st.radio("Person:", ["𝗔𝗹𝗹"] + owners_sorted, label_visibility="collapsed")

    # Fast processing: duplicate Datetime to use native Streamlit frontend formatting
    display_df = df[['Datetime', 'Beer Owner']].sort_values(by="Datetime", ascending=False).reset_index(drop=True)
    display_df.insert(0, "Beer #", range(len(display_df), 0, -1))

    if selected_owner != "𝗔𝗹𝗹":
        display_df = display_df[display_df['Beer Owner'] == selected_owner]

    # Create dummy columns to map the Datetime object via column_config
    display_df['Date'] = display_df['Datetime']
    display_df['Time (UTC)'] = display_df['Datetime']

    # Use native column config formatting rather than slow string conversions
    st.dataframe(
        display_df[['Beer #', 'Beer Owner', 'Date', 'Time (UTC)']],
        use_container_width=True,
        hide_index=True,
        height=670,
        column_config={
            "Date": st.column_config.DatetimeColumn("Date", format="DD MMM YYYY"),
            "Time (UTC)": st.column_config.DatetimeColumn("Time (UTC)", format="HH:mm")
        }
    )

    st.markdown(f"<div style='font-size: 0.75rem; color: var(--text-color); opacity: 0.7; padding-top: 5px;'>Showing {len(display_df):,} of {len(df):,} total beers</div>", unsafe_allow_html=True)