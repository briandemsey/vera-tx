"""
VERA-TX: Verification Engine for Results & Accountability - Texas
Type 4 Dyslexia Screening using TELPAS and STAAR Assessment Data

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_PASSWORD = "vera2026"

# Texas colors
TX_BLUE = "#002868"  # Texas blue
TX_RED = "#BF0A30"   # Texas red
TX_WHITE = "#FFFFFF"

# ============================================================================
# SAMPLE DATA - Texas Districts
# ============================================================================

def load_districts():
    """Load Texas district data."""
    districts_data = [
        ("101912", "Houston ISD", 194000, 58200, 30.0, 84.2, "B"),
        ("057905", "Dallas ISD", 145000, 50750, 35.0, 82.5, "B"),
        ("015907", "San Antonio ISD", 47000, 14100, 30.0, 79.8, "C"),
        ("220905", "Fort Worth ISD", 74000, 25160, 34.0, 81.3, "B"),
        ("227901", "Austin ISD", 75000, 18750, 25.0, 88.4, "B"),
        ("071902", "El Paso ISD", 54000, 16200, 30.0, 83.1, "B"),
        ("220901", "Arlington ISD", 52000, 13520, 26.0, 86.7, "B"),
        ("178905", "Corpus Christi ISD", 35000, 8750, 25.0, 85.2, "B"),
        ("043910", "Plano ISD", 50000, 7500, 15.0, 94.5, "A"),
        ("240901", "Laredo ISD", 23000, 11500, 50.0, 78.4, "C"),
    ]

    df = pd.DataFrame(districts_data, columns=[
        'district_id', 'district_name', 'total_students',
        'ell_count', 'ell_percent', 'graduation_rate', 'accountability_rating'
    ])
    return df

def load_telpas_data():
    """Load sample TELPAS (Texas English Language Proficiency Assessment System) data."""
    telpas_data = []

    districts = [
        ("101912", "Houston ISD"),
        ("057905", "Dallas ISD"),
        ("015907", "San Antonio ISD"),
        ("220905", "Fort Worth ISD"),
        ("227901", "Austin ISD"),
        ("071902", "El Paso ISD"),
        ("220901", "Arlington ISD"),
        ("178905", "Corpus Christi ISD"),
        ("043910", "Plano ISD"),
        ("240901", "Laredo ISD"),
    ]

    for district_id, district_name in districts:
        for grade in range(3, 9):
            for year in [2024, 2025]:
                # Generate realistic TELPAS scores (scale 100-600)
                base_speaking = 345 + (grade * 8)
                base_writing = 300 + (grade * 6)

                # Add district-specific variation
                if district_id == "240901":  # Laredo - highest EL%, larger delta
                    speaking_adj = 40
                    writing_adj = -10
                elif district_id == "057905":  # Dallas
                    speaking_adj = 35
                    writing_adj = -5
                elif district_id == "101912":  # Houston
                    speaking_adj = 30
                    writing_adj = 0
                elif district_id == "043910":  # Plano - higher performing
                    speaking_adj = 15
                    writing_adj = 15
                else:
                    speaking_adj = 25
                    writing_adj = 5

                telpas_data.append({
                    'district_id': district_id,
                    'district_name': district_name,
                    'grade': grade,
                    'year': year,
                    'total_tested': 300 + (grade * 20) if district_id in ["101912", "057905"] else 100 + (grade * 10),
                    'listening_avg': base_speaking + speaking_adj - 5,
                    'speaking_avg': base_speaking + speaking_adj,
                    'reading_avg': base_writing + writing_adj + 15,
                    'writing_avg': base_writing + writing_adj,
                    'composite_avg': (base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 25
                })

    return pd.DataFrame(telpas_data)

def load_staar_data():
    """Load sample STAAR (State of Texas Assessments of Academic Readiness) data."""
    staar_data = []

    districts = [
        ("101912", "Houston ISD"),
        ("057905", "Dallas ISD"),
        ("015907", "San Antonio ISD"),
        ("220905", "Fort Worth ISD"),
        ("227901", "Austin ISD"),
        ("071902", "El Paso ISD"),
        ("220901", "Arlington ISD"),
        ("178905", "Corpus Christi ISD"),
        ("043910", "Plano ISD"),
        ("240901", "Laredo ISD"),
    ]

    for district_id, district_name in districts:
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['Reading/ELA', 'Math']:
                    # Generate realistic STAAR proficiency distributions
                    if district_id == "043910":  # Plano - highest performing
                        approaches = 88 + (grade * 0.3)
                        meets = 65 + (grade * 0.4)
                        masters = 38 + (grade * 0.5)
                    elif district_id in ["240901", "015907"]:  # Lower performing
                        approaches = 62 + (grade * 0.3)
                        meets = 32 + (grade * 0.3)
                        masters = 12 + (grade * 0.3)
                    elif district_id in ["101912", "057905"]:  # Large urban
                        approaches = 70 + (grade * 0.3)
                        meets = 42 + (grade * 0.3)
                        masters = 18 + (grade * 0.4)
                    else:  # Average
                        approaches = 75 + (grade * 0.3)
                        meets = 48 + (grade * 0.3)
                        masters = 22 + (grade * 0.4)

                    staar_data.append({
                        'district_id': district_id,
                        'district_name': district_name,
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'total_tested': 4000 + (grade * 100) if district_id in ["101912", "057905"] else 800 + (grade * 50),
                        'approaches_pct': min(95, approaches),
                        'meets_pct': min(80, meets),
                        'masters_pct': min(55, masters)
                    })

    return pd.DataFrame(staar_data)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    """Simple password authentication."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="color: {TX_BLUE}; font-size: 3rem; margin-bottom: 10px;">VERA-TX</h1>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 40px;">
            Verification Engine for Results & Accountability<br>Texas Implementation
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="password_input")
        if st.button("Access VERA-TX", use_container_width=True):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")

    st.markdown("""
    <div style="text-align: center; margin-top: 60px; color: #999; font-size: 0.85rem;">
        <p>VERA-TX analyzes TELPAS and STAAR assessment data to identify Type 4 dyslexia candidates.</p>
        <p style="margin-top: 10px;">Contact: brian@h-edu.solutions</p>
    </div>
    """, unsafe_allow_html=True)

    return False

# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(telpas_df, district_id, grade, year):
    """
    Compute Type 4 (oral-written delta) analysis for a district.

    Type 4 candidates show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score
    Flag threshold: Delta > 8 points (on normalized scale)
    """
    filtered = telpas_df[
        (telpas_df['district_id'] == district_id) &
        (telpas_df['grade'] == grade) &
        (telpas_df['year'] == year)
    ]

    if filtered.empty:
        return None

    row = filtered.iloc[0]

    # Calculate delta (Speaking - Writing)
    speaking = row['speaking_avg']
    writing = row['writing_avg']
    delta = speaking - writing

    # Normalize to 0-100 scale for threshold comparison
    delta_normalized = delta / 5  # Approximate normalization

    # Flag if delta exceeds threshold
    flagged = delta_normalized > 8

    return {
        'district_id': district_id,
        'district_name': row['district_name'],
        'grade': grade,
        'year': year,
        'speaking_avg': speaking,
        'writing_avg': writing,
        'delta': delta,
        'delta_normalized': delta_normalized,
        'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }

# ============================================================================
# DASHBOARD PAGES
# ============================================================================

def render_overview(districts_df, telpas_df, staar_df):
    """Render the overview dashboard."""
    st.header("Texas Education Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Districts", len(districts_df))
    with col2:
        st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3:
        st.metric("English Learners", f"{districts_df['ell_count'].sum():,}")
    with col4:
        avg_grad = districts_df['graduation_rate'].mean()
        st.metric("Avg Graduation Rate", f"{avg_grad:.1f}%")

    st.divider()

    # District overview table
    st.subheader("Pilot Districts")

    display_df = districts_df.copy()
    display_df['ell_percent'] = display_df['ell_percent'].apply(lambda x: f"{x:.1f}%")
    display_df['graduation_rate'] = display_df['graduation_rate'].apply(lambda x: f"{x:.1f}%")
    display_df.columns = ['District ID', 'District Name', 'Total Students', 'EL Count', 'EL %', 'Grad Rate', 'A-F Rating']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # EL Population chart
    st.subheader("English Learner Population by District")

    fig = px.bar(
        districts_df.sort_values('ell_count', ascending=True),
        x='ell_count',
        y='district_name',
        orientation='h',
        color='ell_percent',
        color_continuous_scale=[[0, '#ffffff'], [0.5, TX_BLUE], [1, TX_RED]],
        labels={'ell_count': 'English Learners', 'district_name': 'District', 'ell_percent': 'EL %'}
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def render_telpas_analysis(telpas_df, districts_df):
    """Render TELPAS assessment analysis."""
    st.header("TELPAS Assessment Analysis")

    st.markdown("""
    **TELPAS (Texas English Language Proficiency Assessment System)** measures English learners'
    proficiency across four domains: Listening, Speaking, Reading, and Writing.
    """)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="telpas_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="telpas_grade")

    with col3:
        year = st.selectbox("Select Year", options=[2025, 2024], key="telpas_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Filter data
    filtered = telpas_df[
        (telpas_df['district_id'] == district_id) &
        (telpas_df['grade'] == grade) &
        (telpas_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        st.divider()

        # Domain scores
        st.subheader("TELPAS Domain Scores")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2:
            st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3:
            st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4:
            st.metric("Writing", f"{row['writing_avg']:.0f}")

        # Domain comparison chart
        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=domains,
            y=scores,
            marker_color=[TX_BLUE, TX_RED, TX_BLUE, TX_RED],
            text=[f"{s:.0f}" for s in scores],
            textposition='outside'
        ))
        fig.update_layout(
            title=f"TELPAS Domain Scores - {district} - Grade {grade} ({year})",
            yaxis_title="Scale Score",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Oral vs Written gap highlight
        oral_avg = (row['listening_avg'] + row['speaking_avg']) / 2
        written_avg = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral_avg - written_avg

        st.subheader("Oral vs Written Gap")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oral Average", f"{oral_avg:.0f}", help="(Listening + Speaking) / 2")
        with col2:
            st.metric("Written Average", f"{written_avg:.0f}", help="(Reading + Writing) / 2")
        with col3:
            delta_color = "normal" if gap < 25 else "inverse"
            st.metric("Gap", f"{gap:+.0f}", delta=f"{'Flag' if gap > 30 else 'OK'}", delta_color=delta_color)

def render_type4_detection(telpas_df, districts_df):
    """Render Type 4 detection analysis."""
    st.header("Type 4 Detection")

    st.markdown("""
    **Type 4 dyslexia candidates** demonstrate strong oral communication abilities but
    significant challenges with written expression. VERA-TX identifies these students by
    analyzing the delta between TELPAS Speaking and Writing domain scores.

    **Flag Threshold:** Speaking - Writing delta > 8 points (normalized scale)
    """)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="type4_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="type4_grade")

    with col3:
        year = st.selectbox("Select Year", options=[2025, 2024], key="type4_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Run analysis
    result = compute_type4_analysis(telpas_df, district_id, grade, year)

    if result:
        st.divider()

        # Results
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Speaking Score", f"{result['speaking_avg']:.0f}")
        with col2:
            st.metric("Writing Score", f"{result['writing_avg']:.0f}")
        with col3:
            st.metric("Delta", f"{result['delta']:+.0f}")
        with col4:
            status = "🚨 FLAGGED" if result['flagged'] else "✅ OK"
            st.metric("Status", status)

        # Visual delta display
        st.subheader("Oral-Written Delta Analysis")

        fig = go.Figure()

        # Speaking bar
        fig.add_trace(go.Bar(
            name='Speaking',
            x=['Score'],
            y=[result['speaking_avg']],
            marker_color=TX_RED,
            text=[f"{result['speaking_avg']:.0f}"],
            textposition='outside'
        ))

        # Writing bar
        fig.add_trace(go.Bar(
            name='Writing',
            x=['Score'],
            y=[result['writing_avg']],
            marker_color=TX_BLUE,
            text=[f"{result['writing_avg']:.0f}"],
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Speaking vs Writing - {district} - Grade {grade}",
            barmode='group',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if result['flagged']:
            st.error(f"""
            **Type 4 Flag Triggered**

            This grade level shows a significant oral-written gap (delta: {result['delta']:+.0f}).

            - **Estimated students affected:** {result['estimated_flagged']} of {result['total_tested']} tested
            - **Recommended action:** Individual student-level screening for Type 4 dyslexia
            - **Next steps:** Cross-reference with STAAR Reading/ELA writing performance
            """)
        else:
            st.success(f"""
            **No Type 4 Flag**

            The oral-written gap for this grade level is within normal range (delta: {result['delta']:+.0f}).

            - **Students tested:** {result['total_tested']}
            - **Continue monitoring:** Regular TELPAS domain analysis recommended
            """)

        # All grades comparison for district
        st.subheader(f"All Grades - {district} ({year})")

        all_grades_data = []
        for g in range(3, 9):
            r = compute_type4_analysis(telpas_df, district_id, g, year)
            if r:
                all_grades_data.append(r)

        if all_grades_data:
            grades_df = pd.DataFrame(all_grades_data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=grades_df['grade'],
                y=grades_df['speaking_avg'],
                name='Speaking',
                mode='lines+markers',
                line=dict(color=TX_RED, width=3),
                marker=dict(size=10)
            ))
            fig.add_trace(go.Scatter(
                x=grades_df['grade'],
                y=grades_df['writing_avg'],
                name='Writing',
                mode='lines+markers',
                line=dict(color=TX_BLUE, width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade",
                yaxis_title="Scale Score",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

def render_staar_analysis(staar_df, districts_df):
    """Render STAAR assessment analysis."""
    st.header("STAAR Assessment Analysis")

    st.markdown("""
    **STAAR (State of Texas Assessments of Academic Readiness)** measures student achievement
    in Reading/ELA and Mathematics aligned to Texas Essential Knowledge and Skills (TEKS).
    """)

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="staar_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="staar_grade")

    with col3:
        subject = st.selectbox("Select Subject", options=['Reading/ELA', 'Math'], key="staar_subject")

    with col4:
        year = st.selectbox("Select Year", options=[2025, 2024], key="staar_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Filter data
    filtered = staar_df[
        (staar_df['district_id'] == district_id) &
        (staar_df['grade'] == grade) &
        (staar_df['subject'] == subject) &
        (staar_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        st.divider()

        # Performance levels
        st.subheader("Performance Distribution")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Approaches Grade Level", f"{row['approaches_pct']:.1f}%")
        with col2:
            st.metric("Meets Grade Level", f"{row['meets_pct']:.1f}%")
        with col3:
            st.metric("Masters Grade Level", f"{row['masters_pct']:.1f}%")

        # Performance chart
        levels = ['Approaches\nGrade Level', 'Meets\nGrade Level', 'Masters\nGrade Level']
        values = [row['approaches_pct'], row['meets_pct'], row['masters_pct']]
        colors = ['#f57c00', TX_BLUE, TX_RED]

        fig = go.Figure(data=[
            go.Bar(x=levels, y=values, marker_color=colors, text=[f"{v:.1f}%" for v in values], textposition='outside')
        ])
        fig.update_layout(
            title=f"STAAR {subject} Performance - {district} - Grade {grade} ({year})",
            yaxis_title="Percentage",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

def render_export(telpas_df, staar_df, districts_df):
    """Render data export page."""
    st.header("Export Data")

    st.markdown("Download assessment data for further analysis.")

    # District filter
    district = st.selectbox(
        "Select District (or All)",
        options=["All Districts"] + districts_df['district_name'].tolist()
    )

    year = st.selectbox("Select Year", options=[2025, 2024])

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("TELPAS Data")
        if district == "All Districts":
            export_telpas = telpas_df[telpas_df['year'] == year]
        else:
            district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
            export_telpas = telpas_df[(telpas_df['district_id'] == district_id) & (telpas_df['year'] == year)]

        st.dataframe(export_telpas, use_container_width=True, hide_index=True)

        csv_telpas = export_telpas.to_csv(index=False)
        st.download_button(
            "Download TELPAS CSV",
            csv_telpas,
            f"vera_tx_telpas_{year}.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:
        st.subheader("STAAR Data")
        if district == "All Districts":
            export_staar = staar_df[staar_df['year'] == year]
        else:
            district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
            export_staar = staar_df[(staar_df['district_id'] == district_id) & (staar_df['year'] == year)]

        st.dataframe(export_staar, use_container_width=True, hide_index=True)

        csv_staar = export_staar.to_csv(index=False)
        st.download_button(
            "Download STAAR CSV",
            csv_staar,
            f"vera_tx_staar_{year}.csv",
            "text/csv",
            use_container_width=True
        )

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="VERA-TX | Texas Type 4 Detection",
        page_icon="⭐",
        layout="wide"
    )

    # Custom CSS
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #fafafa;
        }}
        .block-container {{
            padding-top: 2rem;
        }}
        h1, h2, h3 {{
            color: {TX_BLUE};
        }}
        .stButton > button {{
            background-color: {TX_BLUE};
            color: white;
        }}
        .stButton > button:hover {{
            background-color: {TX_RED};
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Authentication
    if not check_password():
        return

    # Load data
    districts_df = load_districts()
    telpas_df = load_telpas_data()
    staar_df = load_staar_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {TX_BLUE}; margin: 0;">VERA-TX</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Texas Implementation</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "TELPAS Analysis", "Type 4 Detection", "STAAR Analysis", "Export Data"]
    )

    st.sidebar.divider()

    st.sidebar.markdown("""
    **Data Sources:**
    - TELPAS (English Language Proficiency)
    - STAAR (Academic Readiness)
    - TEA Accountability (A-F Ratings)

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points

    ---

    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    # Render selected page
    if page == "Overview":
        render_overview(districts_df, telpas_df, staar_df)
    elif page == "TELPAS Analysis":
        render_telpas_analysis(telpas_df, districts_df)
    elif page == "Type 4 Detection":
        render_type4_detection(telpas_df, districts_df)
    elif page == "STAAR Analysis":
        render_staar_analysis(staar_df, districts_df)
    elif page == "Export Data":
        render_export(telpas_df, staar_df, districts_df)

if __name__ == "__main__":
    main()
