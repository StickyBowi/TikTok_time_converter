
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, quote
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="TikTok Video Analyzer",
    page_icon="🎬",
    layout="centered"
)


# ---------------------------------
# DESIGN
# ---------------------------------

st.markdown("""
<style>
.block-container {
    max-width: 850px;
    padding-top: 3rem;
}

h1 {
    font-weight: 750 !important;
    letter-spacing: -1px;
}

.subtitle {
    color: #888;
    margin-bottom: 25px;
}

.result-card {
    background: rgba(128,128,128,0.08);
    border: 1px solid rgba(128,128,128,0.2);
    padding: 22px;
    border-radius: 14px;
    margin: 12px 0;
}

.result-label {
    font-size: 0.8rem;
    color: #888;
    margin-bottom: 6px;
    text-transform: uppercase;
}

.result-value {
    font-size: 1.1rem;
    font-weight: 600;
}

.big-date {
    font-size: 1.8rem;
    font-weight: 750;
}

div.stButton > button {
    border-radius: 10px;
    height: 3rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------
# URL AND ID EXTRACTION
# ---------------------------------

def extract_video_info(url):

    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or "").lower()

    allowed_hosts = {
        "tiktok.com",
        "www.tiktok.com",
        "m.tiktok.com"
    }

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Enter a complete HTTPS TikTok URL.")

    if hostname not in allowed_hosts:
        raise ValueError("Not a recognized TikTok URL.")

    match = re.search(
        r"/(?:video|photo)/(\d{15,20})(?:/|$)",
        parsed.path
    )

    if not match:
        raise ValueError(
            "No video ID found. Use a full TikTok video URL."
        )

    video_id = int(match.group(1))

    if video_id >= 2**64:
        raise ValueError("Video ID exceeds 64 bits.")

    username_match = re.search(
        r"/@([^/]+)/(?:video|photo)/",
        parsed.path
    )

    username = (
        username_match.group(1)
        if username_match else None
    )

    return video_id, username


# ---------------------------------
# TIMESTAMP CONVERSION
# ---------------------------------

def convert_timestamp(video_id):

    unix_timestamp = video_id >> 32

    utc_time = datetime.fromtimestamp(
        unix_timestamp,
        tz=timezone.utc
    )

    swedish_time = utc_time.astimezone(
        ZoneInfo("Europe/Stockholm")
    )

    return unix_timestamp, swedish_time


# ---------------------------------
# FETCH PUBLIC TIKTOK METADATA
# ---------------------------------

@st.cache_data(ttl=1800, show_spinner=False)
def get_tiktok_metadata(url):

    endpoint = "https://www.tiktok.com/oembed"

    try:
        response = requests.get(
            endpoint,
            params={"url": url},
            headers={
                "User-Agent": "TikTokTimestampTool/1.0"
            },
            timeout=12
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        return data

    except (requests.RequestException, ValueError):
        return None


# ---------------------------------
# MAIN INTERFACE
# ---------------------------------

st.title("🎬 TikTok Video Analyzer")

st.markdown(
    '<div class="subtitle">'
    'Extract video timestamps, thumbnails '
    'and publicly available creator information.'
    '</div>',
    unsafe_allow_html=True
)

url = st.text_input(
    "Paste TikTok video URL",
    placeholder=(
        "https://www.tiktok.com/"
        "@username/video/7123456789012345678"
    )
)

analyze = st.button(
    "Analyze Video",
    type="primary",
    use_container_width=True
)


# ---------------------------------
# ANALYSIS
# ---------------------------------

if analyze:

    if not url.strip():
        st.warning("Please enter a TikTok video URL.")

    else:
        try:
            video_id, username = extract_video_info(url)

            unix_timestamp, swedish_time = (
                convert_timestamp(video_id)
            )

            # Use a canonical URL without tracking parameters
            if username:
                canonical_url = (
                    f"https://www.tiktok.com/"
                    f"@{username}/video/{video_id}"
                )
            else:
                canonical_url = url.strip()

            with st.spinner("Retrieving public video information..."):
                metadata = get_tiktok_metadata(canonical_url)

            # -----------------------------
            # VIDEO INFORMATION
            # -----------------------------

            st.subheader("Video Information")

            if metadata:

                thumbnail = metadata.get("thumbnail_url")
                title = metadata.get("title")
                author_name = metadata.get("author_name")
                author_url = metadata.get("author_url")

                col1, col2 = st.columns([1, 2])

                with col1:
                    if thumbnail:
                        st.image(
                            thumbnail,
                            use_container_width=True
                        )
                    else:
                        st.info("No thumbnail available.")

                with col2:
                    if title:
                        st.write("**Caption / Title**")
                        st.write(title)

                    st.write("**Video ID**")
                    st.code(str(video_id))

                    st.link_button(
                        "Open Video on TikTok",
                        canonical_url
                    )

                # -----------------------------
                # CREATOR INFORMATION
                # -----------------------------

                st.subheader("Creator Information")

                if author_name:
                    st.write("**Display name:**")
                    st.write(author_name)

                if username:
                    st.write("**Username:**")
                    st.write("@" + username)

                if author_url:
                    st.link_button(
                        "View Creator Profile",
                        author_url
                    )

                # -----------------------------
                # OPTIONAL EXTRA FIELDS
                # -----------------------------

                optional_fields = {
                    "duration": "Duration",
                    "view_count": "Views",
                    "like_count": "Likes",
                    "comment_count": "Comments",
                    "share_count": "Shares"
                }

                for field, label in optional_fields.items():
                    value = metadata.get(field)

                    if value is not None:
                        st.write(f"**{label}:** {value}")

            else:

                st.info(
                    "TikTok metadata could not be retrieved. "
                    "The timestamp calculation is still available."
                )

                st.write("**Video ID:**", video_id)

                if username:
                    st.write("**Username from URL:**", username)

                st.link_button(
                    "Open Video on TikTok",
                    canonical_url
                )

            # -----------------------------
            # TIMESTAMP RESULT
            # -----------------------------

            st.subheader("Timestamp Analysis")

            date_string = swedish_time.strftime(
                "%d %B %Y"
            )

            time_string = swedish_time.strftime(
                "%H:%M:%S"
            )

            timezone_name = swedish_time.tzname()

            st.markdown(f"""
            <div class="result-card">
                <div class="result-label">
                    Swedish Local Time
                </div>
                <div class="big-date">
                    {date_string}
                </div>
                <div class="result-value">
                    {time_string} {timezone_name}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Unix Timestamp",
                    str(unix_timestamp)
                )

            with col2:
                st.metric(
                    "Timezone",
                    timezone_name
                )

            with st.expander("Technical Details"):

                binary = format(video_id, "064b")

                st.write("**64-bit Binary ID**")
                st.code(binary)

                st.write("**First 32 bits**")
                st.code(binary[:32])

                st.write("**UTC Time**")
                st.write(
                    datetime.fromtimestamp(
                        unix_timestamp,
                        tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
                )

            # -----------------------------
            # VIDEO PREVIEW
            # -----------------------------

            with st.expander("Video Preview"):

                player_url = (
                    "https://www.tiktok.com/player/v1/"
                    + str(video_id)
                )

                components.iframe(
                    player_url,
                    height=580,
                    scrolling=False
                )

        except (ValueError, OverflowError) as e:
            st.error(str(e))


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "TikTok Video Analyzer | "
    "Timestamps derived from video IDs. "
    "Timezone: Europe/Stockholm. "
    "Metadata availability depends on TikTok."
)
