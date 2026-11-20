import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import urlparse, parse_qs

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="YouTube Sentiment Analyzer",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #10101c, #19152b, #10101c);
    color: white;
}

[data-testid="stSidebar"] {
    background: #1d1b30;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    background: linear-gradient(90deg, #ff79b0, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #b9b5cc;
    font-size: 16px;
    margin-bottom: 25px;
}

.metric-card {
    background: linear-gradient(135deg, #292440, #352747);
    padding: 22px;
    border-radius: 15px;
    border: 1px solid #514064;
    text-align: center;
}

.metric-title {
    color: #c5bdd8;
    font-size: 15px;
}

.metric-value {
    font-size: 30px;
    font-weight: bold;
    margin-top: 8px;
}

.positive {
    color: #42e6a4;
}

.negative {
    color: #ff647c;
}

.neutral {
    color: #ffd166;
}

.section-title {
    color: #e6caff;
    font-size: 23px;
    font-weight: bold;
    margin-top: 20px;
}

.stButton > button {
    background: linear-gradient(90deg, #c44dff, #ff65a3);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    height: 45px;
    width: 100%;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #a934e8, #e74c91);
    color: white;
    border: none;
}

div[data-testid="stMetric"] {
    background: #292440;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #514064;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# INITIALIZATION
# =====================================================

analyzer = SentimentIntensityAnalyzer()

st.markdown(
    '<div class="main-title">📊 YouTube Sentiment Analyzer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Analyze audience reactions and discover what people think about a YouTube video.</div>',
    unsafe_allow_html=True
)


# =====================================================
# EXTRACT YOUTUBE VIDEO ID
# =====================================================

def get_video_id(url):

    try:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower().split(":")[0]

        if host not in [
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be"
        ]:
            return None

        if host in ["youtu.be", "www.youtu.be"]:
            return parsed.path.strip("/").split("/")[0] or None

        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        parts = parsed.path.strip("/").split("/")

        if len(parts) >= 2 and parts[0] in [
            "shorts", "embed", "live"
        ]:
            return parts[1]

    except Exception:
        return None

    return None


# =====================================================
# FETCH VIDEO TITLE
# =====================================================

def get_video_title(video_id, api_key):

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }

    response = requests.get(
        url, params=params, timeout=20
    )

    response.raise_for_status()

    items = response.json().get("items", [])

    if items:
        return items[0]["snippet"]["title"]

    return "YouTube Video"


# =====================================================
# FETCH YOUTUBE COMMENTS
# =====================================================

def get_comments(video_id, api_key, max_comments):

    comments = []

    url = "https://www.googleapis.com/youtube/v3/commentThreads"

    page_token = None

    while len(comments) < max_comments:

        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(100, max_comments - len(comments)),
            "textFormat": "plainText",
            "order": "relevance",
            "key": api_key
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            url, params=params, timeout=30
        )

        if response.status_code != 200:

            try:
                message = response.json()["error"]["message"]
            except (ValueError, KeyError):
                message = response.text

            raise Exception(message)

        data = response.json()

        for item in data.get("items", []):

            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            comments.append(comment)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    return comments


# =====================================================
# SENTIMENT ANALYSIS USING VADER
# =====================================================

def analyze_sentiment(comment):

    score = analyzer.polarity_scores(comment)["compound"]

    if score >= 0.05:
        sentiment = "Positive"

    elif score <= -0.05:
        sentiment = "Negative"

    else:
        sentiment = "Neutral"

    return sentiment, score


# =====================================================
# SIDEBAR SETTINGS
# =====================================================

st.sidebar.markdown("## ⚙️ Settings")

st.sidebar.markdown("---")

api_key = st.sidebar.text_input(
    "API key here",
    type="password",
    help="Enter your YouTube Data API v3 key."
)

max_comments = st.sidebar.selectbox(
    "Number of comments to analyze",
    [100, 200, 300, 500],
    index=3
)

st.sidebar.markdown("---")

st.sidebar.markdown("### 💡 About the Project")

st.sidebar.write(
    "This application uses Natural Language Processing "
    "and VADER sentiment analysis to identify audience "
    "opinions from YouTube comments."
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Developed using Python, Streamlit, VADER and YouTube API."
)


# =====================================================
# VIDEO URL INPUT
# =====================================================

st.markdown('<div class="section-title">🎬 Enter Video Details</div>',
            unsafe_allow_html=True)

video_url = st.text_input(
    "Paste YouTube Video Link",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed"
)

analyze_button = st.button(
    "🔍 Analyze YouTube Comments",
    use_container_width=True
)


# =====================================================
# PERFORM ANALYSIS
# =====================================================

if analyze_button:

    st.session_state.pop("results", None)
    st.session_state.pop("title", None)

    if not api_key:
        st.error("Please enter your YouTube API key.")

    elif not video_url:
        st.warning("Please paste a YouTube video link.")

    else:

        video_id = get_video_id(video_url)

        if not video_id:
            st.error("Invalid YouTube URL. Please enter a valid link.")

        else:

            try:

                with st.spinner(
                    "⏳ Fetching comments and analyzing sentiment..."
                ):

                    title = get_video_title(
                        video_id, api_key
                    )

                    comments = get_comments(
                        video_id,
                        api_key,
                        max_comments
                    )

                    if comments:

                        results = []

                        for comment in comments:

                            sentiment, score = analyze_sentiment(
                                comment
                            )

                            results.append({
                                "Comment": comment,
                                "Sentiment": sentiment,
                                "Score": score
                            })

                        df = pd.DataFrame(results)

                        st.session_state["results"] = df
                        st.session_state["title"] = title

                    else:
                        st.warning(
                            "No public comments were found for this video."
                        )

            except requests.exceptions.RequestException as e:
                st.error(f"Network/API error: {e}")

            except Exception as e:
                st.error(f"Error: {e}")


# =====================================================
# DISPLAY ANALYSIS RESULTS
# =====================================================

if "results" in st.session_state:

    df = st.session_state["results"]

    total = len(df)

    counts = df["Sentiment"].value_counts()

    positive = counts.get("Positive", 0)
    negative = counts.get("Negative", 0)
    neutral = counts.get("Neutral", 0)

    positive_pct = positive / total * 100
    negative_pct = negative / total * 100
    neutral_pct = neutral / total * 100

    st.markdown("---")

    # VIDEO DETAILS

    st.markdown(
        '<div class="section-title">🎥 Video Information</div>',
        unsafe_allow_html=True
    )

    st.success(
        f"Successfully analyzed {total} YouTube comments!"
    )

    st.markdown(f"**Video Title:** {st.session_state['title']}")

    # =================================================
    # METRIC CARDS
    # =================================================

    st.markdown(
        '<div class="section-title">📌 Sentiment Overview</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Comments</div>
            <div class="metric-value" style="color:#c4a5ff">
                {total}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">😊 Positive</div>
            <div class="metric-value positive">
                {positive_pct:.1f}%
            </div>
            <div class="metric-title">{positive} comments</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">😠 Negative</div>
            <div class="metric-value negative">
                {negative_pct:.1f}%
            </div>
            <div class="metric-title">{negative} comments</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">😐 Neutral</div>
            <div class="metric-value neutral">
                {neutral_pct:.1f}%
            </div>
            <div class="metric-title">{neutral} comments</div>
        </div>
        """, unsafe_allow_html=True)

    # =================================================
    # GRAPH DATA
    # =================================================

    chart_data = pd.DataFrame({
        "Sentiment": ["Positive", "Negative", "Neutral"],
        "Comments": [positive, negative, neutral],
        "Percentage": [
            positive_pct,
            negative_pct,
            neutral_pct
        ]
    })

    colors = {
        "Positive": "#35D39A",
        "Negative": "#FF5876",
        "Neutral": "#FFC857"
    }

    st.markdown("---")

    st.markdown(
        '<div class="section-title">📊 Sentiment Analysis Graphs</div>',
        unsafe_allow_html=True
    )

    # =================================================
    # BAR GRAPH
    # =================================================

    left, right = st.columns(2)

    with left:

        st.markdown("### 📊 Comment Distribution")

        fig1 = px.bar(
            chart_data,
            x="Sentiment",
            y="Comments",
            color="Sentiment",
            text="Comments",
            color_discrete_map=colors
        )

        fig1.update_traces(
            textposition="outside",
            marker_line_width=0
        )

        fig1.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="white",
                size=13
            ),
            showlegend=False,
            height=420,
            xaxis_title="Sentiment Category",
            yaxis_title="Number of Comments",
            yaxis=dict(rangemode="tozero")
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    # =================================================
    # DONUT GRAPH
    # =================================================

    with right:

        st.markdown("### 🍩 Sentiment Percentage")

        fig2 = px.pie(
            chart_data,
            names="Sentiment",
            values="Comments",
            hole=0.55,
            color="Sentiment",
            color_discrete_map=colors
        )

        fig2.update_traces(
            textinfo="percent+label",
            textfont_size=13,
            marker=dict(
                line=dict(
                    color="#19152b",
                    width=3
                )
            )
        )

        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            showlegend=False,
            height=420,
            annotations=[
                dict(
                    text=f"{total}<br>Comments",
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False
                )
            ]
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # =================================================
    # PERCENTAGE BAR GRAPH
    # =================================================

    st.markdown("### 📈 Sentiment Percentage Comparison")

    fig3 = px.bar(
        chart_data,
        x="Sentiment",
        y="Percentage",
        color="Sentiment",
        text=chart_data["Percentage"].apply(
            lambda x: f"{x:.1f}%"
        ),
        color_discrete_map=colors
    )

    fig3.update_traces(
        textposition="outside"
    )

    fig3.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=350,
        yaxis_title="Percentage (%)",
        xaxis_title="Sentiment",
        yaxis=dict(
            range=[0, 110],
            ticksuffix="%"
        )
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # =================================================
    # OVERALL SENTIMENT
    # =================================================

    st.markdown("---")

    st.markdown(
        '<div class="section-title">📝 Overall Sentiment Result</div>',
        unsafe_allow_html=True
    )

    if positive > negative and positive > neutral:

        st.success(
            f"😊 The overall audience sentiment is POSITIVE. "
            f"{positive_pct:.1f}% of analyzed comments are positive."
        )

    elif negative > positive and negative > neutral:

        st.error(
            f"😠 The overall audience sentiment is NEGATIVE. "
            f"{negative_pct:.1f}% of analyzed comments are negative."
        )

    elif neutral > positive and neutral > negative:

        st.info(
            f"😐 The overall audience sentiment is NEUTRAL. "
            f"{neutral_pct:.1f}% of analyzed comments are neutral."
        )

    else:

        st.info(
            "The audience sentiment is MIXED, with no single "
            "category having the highest count."
        )

    # =================================================
    # INDIVIDUAL COMMENT ANALYSIS
    # =================================================

    st.markdown("---")

    st.markdown(
        '<div class="section-title">💬 Individual Comment Analysis</div>',
        unsafe_allow_html=True
    )

    sentiment_filter = st.selectbox(
        "Filter comments by sentiment",
        ["All", "Positive", "Negative", "Neutral"]
    )

    if sentiment_filter == "All":
        display_df = df

    else:
        display_df = df[
            df["Sentiment"] == sentiment_filter
        ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing {len(display_df)} out of {total} comments."
    )

    # =================================================
    # DOWNLOAD CSV
    # =================================================

    st.markdown("---")

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download Sentiment Analysis Report",
        data=csv,
        file_name="youtube_sentiment_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("---")

    st.caption(
        "YouTube Comment Sentiment Analysis | "
        "Python • Streamlit • NLP • VADER"
    )