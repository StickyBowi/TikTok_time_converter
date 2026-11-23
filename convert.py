
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import streamlit as st


# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="TikTok Timestamp Converter",
    page_icon="🕒",
    layout="centered"
)


# ---------------------------------
# CUSTOM DESIGN
# ---------------------------------

st.markdown("""
<style>
    .block-container {
        max-width: 720px;
        padding-top: 4rem;
    }

    h1 {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        letter-spacing: -1px;
    }

    .subtitle {
        color: #888;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }

    .result-box {
        background: rgba(128,128,128,0.08);
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 14px;
        padding: 25px;
        margin-top: 20px;
    }

    .result-label {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 5px;
    }

    .result-date {
        font-size: 1.7rem;
        font-weight: 700;
        margin-bottom: 18px;
    }

    .result-detail {
        font-size: 0.9rem;
        margin-top: 8px;
        overflow-wrap: anywhere;
    }

    div.stButton > button {
        border-radius: 10px;
        height: 3rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------
# CONVERSION FUNCTIONS
# ---------------------------------

def extract_video_id(url):
    """Extract video ID from a full TikTok URL."""

    parsed = urlparse(url.strip())

    hostname = (parsed.hostname or "").lower()

    if hostname not in (
        "tiktok.com",
        "www.tiktok.com",
        "m.tiktok.com"
    ):
        raise ValueError("Please enter a valid TikTok URL.")

    match = re.search(
        r"/(?:video|photo)/(\d{15,20})(?:/|$)",
        parsed.path
    )

    if not match:
        raise ValueError(
            "Could not find a video ID in the URL."
        )

    return int(match.group(1))


def convert_timestamp(video_id):
    """Extract the first 32 bits as Unix seconds."""

    if not 0 <= video_id < 2**64:
        raise ValueError("Invalid 64-bit video ID.")

    # Shift right by 32 bits
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

    return unix_timestamp, swedish_time


# ---------------------------------
# USER INTERFACE
# ---------------------------------

st.title("🕒 TikTok Timestamp Converter")

st.markdown(
    '<div class="subtitle">'
    'Discover the creation timestamp embedded '
    'in a TikTok video ID.'
    '</div>',
    unsafe_allow_html=True
)

url = st.text_input(
    "TikTok video URL",
    placeholder=(
        "https://www.tiktok.com/"
        "@username/video/7123456789012345678"
    )
)

convert = st.button(
    "Extract Timestamp",
    type="primary",
    use_container_width=True
)


# ---------------------------------
# PROCESS INPUT
# ---------------------------------

if convert:

    if not url.strip():
        st.warning("Please paste a TikTok URL.")

    else:
        try:
            video_id = extract_video_id(url)

            unix_timestamp, swedish_time = (
                convert_timestamp(video_id)
            )

            date_string = swedish_time.strftime(
                "%d %B %Y"
            )

            time_string = swedish_time.strftime(
                "%H:%M:%S"
            )

            timezone_name = swedish_time.tzname()

            st.markdown(f"""
            <div class="result-box">

                <div class="result-label">
                    SWEDISH LOCAL TIME
                </div>

                <div class="result-date">
                    {date_string}<br>
                    {time_string} {timezone_name}
                </div>

                <hr>

                <div class="result-label">
                    VIDEO ID
                </div>

                <div class="result-detail">
                    {video_id}
                </div>

                <br>

                <div class="result-label">
                    UNIX TIMESTAMP
                </div>

                <div class="result-detail">
                    {unix_timestamp}
                </div>

            </div>
            """, unsafe_allow_html=True)

        except (ValueError, OverflowError) as e:
            st.error(str(e))


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "Timestamp extracted from the first 32 bits "
    "of the TikTok video ID. "
    "Times are displayed in Europe/Stockholm."
)
