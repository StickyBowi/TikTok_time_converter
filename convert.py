
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
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
# CUSTOM DESIGN
# ---------------------------------

st.markdown("""
<style>
.block-container {
    max-width: 850px;
    padding-top: 3rem;
    padding-bottom: 3rem;
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
# EXTRACT VIDEO ID AND USERNAME
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
        raise ValueError(
            "Please enter a complete TikTok URL."
        )

    if hostname not in allowed_hosts:
        raise ValueError(
            "Not a recognized TikTok URL."
        )

    match = re.search(
        r"/(?:video|photo)/(\d{15,20})(?:/|$)",
        parsed.path
    )

    if not match:
        raise ValueError(
            "No video ID found. "
            "Please use a full TikTok video URL."
        )

    video_id = int(match.group(1))

    if not 0 <= video_id < 2**64:
        raise ValueError(
            "Video ID exceeds the 64-bit range."
        )

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

    # Extract first 32 bits
    unix_timestamp = video_id >> 32

    # Convert to UTC
    utc_time = datetime.fromtimestamp(
        unix_timestamp,
        tz=timezone.utc
    )

    # Convert to Swedish local time
    swedish_time = utc_time.astimezone(
        ZoneInfo("Europe/Stockholm")
    )

    return unix_timestamp, utc_time, swedish_time


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
                "User-Agent": "Mozilla/5.0"
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
# EMBEDDED PLAYER FUNCTION
# ---------------------------------

def show_tiktok_player(video_id, height=580):

    player_url = (
        "https://www.tiktok.com/player/v1/"
        + str(video_id)
    )

    components.iframe(
        player_url,
        height=height,
        scrolling=False
    )


# ---------------------------------
# MAIN INTERFACE
# ---------------------------------

st.title("🎬 TikTok Video Analyzer")

st.markdown(
    '<div class="subtitle">'
    'Extract timestamps, video information '
    'and publicly available creator details.'
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
        st.warning(
            "Please enter a TikTok video URL."
        )

    else:
        try:

            # Extract ID and username
            video_id, username = extract_video_info(url)

            # Convert timestamp
            unix_timestamp, utc_time, swedish_time = (
                convert_timestamp(video_id)
            )

            # Construct canonical video URL
            if username:
                canonical_url = (
                    f"https://www.tiktok.com/"
                    f"@{username}/video/{video_id}"
                )
            else:
                canonical_url = url.strip()

            # Fetch metadata
            with st.spinner(
                "Retrieving public video information..."
            ):
                metadata = get_tiktok_metadata(
                    canonical_url
                )

            # ---------------------------------
            # VIDEO INFORMATION
            # ---------------------------------

            st.subheader("Video Information")

            title = (
                metadata.get("title")
                if metadata else None
            )

            author_name = (
                metadata.get("author_name")
                if metadata else None
            )

            author_url = (
                metadata.get("author_url")
                if metadata else None
            )

            col1, col2 = st.columns(
                [1, 2],
                gap="medium"
            )

            # SMALL EMBEDDED PLAYER
            with col1:

                show_tiktok_player(
                    video_id,
                    height=300
                )

            # VIDEO DETAILS
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

            # ---------------------------------
            # CREATOR INFORMATION
            # ---------------------------------

            st.subheader("Creator Information")

            if author_name:
                st.write("**Display Name:**")
                st.write(author_name)

            if username:
                st.write("**Username:**")
                st.write("@" + username)

            if author_url:
                st.link_button(
                    "View Creator Profile",
                    author_url
                )

            if not metadata:
                st.info(
                    "TikTok metadata could not be retrieved. "
                    "The timestamp calculation and embedded "
                    "players may still work."
                )

            # ---------------------------------
            # OPTIONAL METADATA
            # ---------------------------------

            if metadata:

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
                        st.write(
                            f"**{label}:** {value}"
                        )

            # ---------------------------------
            # TIMESTAMP ANALYSIS
            # ---------------------------------

            st.subheader("Timestamp Analysis")

            date_string = swedish_time.strftime(
                "%d %B %Y"
            )

            time_string = swedish_time.strftime(
                "%H:%M:%S"
            )

            timezone_name = swedish_time.tzname()

            # FIXED HTML RENDERING:
            # HTML starts at the beginning of the line.
            st.markdown(
                f"""
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
""",
                unsafe_allow_html=True
            )

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

            # ---------------------------------
            # TECHNICAL DETAILS
            # ---------------------------------

            with st.expander("Technical Details"):

                binary = format(
                    video_id,
                    "064b"
                )

                st.write("**64-bit Binary Video ID**")
                st.code(binary)

                st.write("**First 32 bits**")
                st.code(binary[:32])

                st.write("**Unix Timestamp**")
                st.code(str(unix_timestamp))

                st.write("**UTC Date and Time**")
                st.write(
                    utc_time.strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                )

                st.write("**Swedish Date and Time**")
                st.write(
                    swedish_time.strftime(
                        "%Y-%m-%d %H:%M:%S %Z"
                    )
                )

            # ---------------------------------
            # FULL-SIZED VIDEO PLAYER
            # ---------------------------------

            st.subheader("Video Preview")

            with st.expander(
                "Open Full Video Player",
                expanded=False
            ):

                show_tiktok_player(
                    video_id,
                    height=650
                )

        except (ValueError, OverflowError) as e:

            st.error(str(e))


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "TikTok Video Analyzer | "
    "Timestamps derived from the first 32 bits "
    "of TikTok video IDs. "
    "Times displayed in Europe/Stockholm. "
    "Creator metadata depends on TikTok availability."
)
