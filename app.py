
import streamlit as st
import os
import hashlib

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Meeting Assistant",
    page_icon="🎤",
    layout="wide"
)

# --------------------------------------------------
# Session State
# --------------------------------------------------

if "transcript" not in st.session_state:
    st.session_state.transcript = ""

if "meeting_result" not in st.session_state:
    st.session_state.meeting_result = None

if "uploaded_file_hash" not in st.session_state:
    st.session_state.uploaded_file_hash = None

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

os.makedirs("uploads", exist_ok=True)


# --------------------------------------------------
# Cached Meeting Agent
# --------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_agent(model_name):
    from meeting_agent import MeetingAgent
    return MeetingAgent(model=model_name)


# --------------------------------------------------
# Helper: Save Uploaded File
# --------------------------------------------------

def save_uploaded_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Reuse an existing saved file if its content is unchanged.
    if (
        st.session_state.uploaded_file_hash == file_hash
        and st.session_state.uploaded_file_path
        and os.path.exists(st.session_state.uploaded_file_path)
    ):
        return st.session_state.uploaded_file_path

    # Avoid collisions between files with the same name.
    extension = os.path.splitext(uploaded_file.name)[1]
    file_path = os.path.join("uploads", f"{file_hash}{extension}")

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    st.session_state.uploaded_file_hash = file_hash
    st.session_state.uploaded_file_path = file_path

    return file_path


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("🎤 AI Meeting Assistant")

st.write(
    """
Upload a meeting transcript, audio, or video file.

The assistant generates:
- Summary
- Decisions Taken
- Action Items
- Risks
- Open Items
"""
)


# --------------------------------------------------
# Sidebar Settings
# --------------------------------------------------

st.sidebar.header("⚙️ Settings")

model_name = st.sidebar.selectbox(
    "Choose Ollama Model",
    ["phi3", "llama3:8b"]
)


# --------------------------------------------------
# Input Type
# --------------------------------------------------

input_type = st.radio(
    "Select Input Type",
    ["Transcript", "Audio", "Video"],
    horizontal=True
)


# --------------------------------------------------
# Transcript Upload
# --------------------------------------------------

if input_type == "Transcript":

    uploaded_file = st.file_uploader(
        "Upload Transcript (.txt)",
        type=["txt"],
        key="transcript_upload"
    )

    if uploaded_file:
        try:
            transcript = uploaded_file.getvalue().decode("utf-8-sig")

            if st.session_state.transcript != transcript:
                st.session_state.transcript = transcript
                st.session_state.meeting_result = None

            st.success("Transcript loaded")

            with st.expander("📄 View Transcript"):
                st.text(st.session_state.transcript)

        except UnicodeDecodeError:
            st.error("Unable to read this file. Please upload a UTF-8 text file.")


# --------------------------------------------------
# Audio Upload
# --------------------------------------------------

elif input_type == "Audio":

    uploaded_file = st.file_uploader(
        "Upload Audio",
        type=["mp3", "wav", "m4a"],
        key="audio_upload"
    )

    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)

        st.audio(file_path)

        if st.button("🎧 Convert Audio to Text"):
            try:
                from transcriber import transcribe

                with st.spinner("Running Whisper..."):
                    transcript = transcribe(file_path)

                st.session_state.transcript = transcript
                st.session_state.meeting_result = None

                st.success("Transcription completed")

            except Exception as e:
                st.error(f"Transcription failed: {e}")

        if st.session_state.transcript:
            with st.expander("📄 View Transcript"):
                st.text(st.session_state.transcript)


# --------------------------------------------------
# Video Upload
# --------------------------------------------------

elif input_type == "Video":

    uploaded_file = st.file_uploader(
        "Upload Video",
        type=["mp4", "mov", "avi", "mkv"],
        key="video_upload"
    )

    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)

        st.video(file_path)

        if st.button("🎬 Convert Video to Text"):
            try:
                from transcriber import transcribe

                with st.spinner("Running Whisper..."):
                    transcript = transcribe(file_path)

                st.session_state.transcript = transcript
                st.session_state.meeting_result = None

                st.success("Video transcription completed")

            except Exception as e:
                st.error(f"Video transcription failed: {e}")

        if st.session_state.transcript:
            with st.expander("📄 View Transcript"):
                st.text(st.session_state.transcript)


# --------------------------------------------------
# Analyze Meeting
# --------------------------------------------------

if st.session_state.transcript:

    st.divider()
    st.success("Transcript ready")

    if st.button("🚀 Analyze Meeting", type="primary"):
        try:
            with st.spinner("Analyzing with Ollama..."):
                agent = get_agent(model_name)

                result = agent.analyze_meeting(
                    st.session_state.transcript
                )

            st.session_state.meeting_result = result
            st.success("Analysis completed")

        except Exception as e:
            st.error(f"Analysis failed: {e}")


# --------------------------------------------------
# Meeting Results
# --------------------------------------------------

if st.session_state.meeting_result:

    result = st.session_state.meeting_result

    st.divider()
    st.header("📊 Meeting Analysis")

    # Attendees
    st.subheader("👥 Attendees")

    attendees = result.get("attendees", [])

    if attendees:
        for attendee in attendees:
            if isinstance(attendee, dict):
                name = attendee.get("name", "Unknown")
                email = attendee.get("email", "Not available")
                st.write(f"• {name} ({email})")
            else:
                st.write(f"• {attendee}")
    else:
        st.info("No attendees identified")

    # Summary
    st.subheader("📝 Summary")
    st.write(result.get("summary", "No summary available"))

    # Decisions
    st.subheader("✅ Decisions Taken")

    decisions = result.get("decisions", [])

    if decisions:
        for decision in decisions:
            if isinstance(decision, dict):
                decision_text = (
                    decision.get("decision")
                    or decision.get("description")
                    or str(decision)
                )
            else:
                decision_text = str(decision)

            st.write(f"• {decision_text}")
    else:
        st.info("No decisions found")

    # Action Items
    st.subheader("📋 Action Items")

    actions = result.get("action_items", [])

    if actions:
        for action in actions:
            if isinstance(action, dict):
                st.markdown(
                    f"""
**Owner:** {action.get('owner', 'Unassigned')}

**Task:** {action.get('task', 'Not Available')}

**Deadline:** {action.get('deadline', 'Not Mentioned')}
"""
                )
            else:
                st.write(f"• {action}")

            st.divider()
    else:
        st.info("No action items found")

    # Risks
    st.subheader("⚠️ Risks")

    risks = result.get("risks", [])

    if risks:
        for risk in risks:
            if isinstance(risk, dict):
                risk_text = (
                    risk.get("risk")
                    or risk.get("description")
                    or str(risk)
                )
            else:
                risk_text = str(risk)

            st.write(f"• {risk_text}")
    else:
        st.info("No risks identified")

    # Open Items
    st.subheader("🔓 Open Items")

    open_items = result.get("open_items", [])

    if open_items:
        for item in open_items:
            if isinstance(item, dict):
                item_text = (
                    item.get("item")
                    or item.get("description")
                    or str(item)
                )
            else:
                item_text = str(item)

            st.write(f"• {item_text}")
    else:
        st.info("No open items")

    # --------------------------------------------------
    # Email Report
    # --------------------------------------------------

    st.divider()
    st.subheader("📧 Send Meeting Report")

    st.write(
        "The meeting report will be sent to the attendee "
        "email addresses extracted from the meeting."
    )

    if st.button("📨 Send Report to All Attendees"):
        try:
            from email_sender import send_meeting_report

            with st.spinner("Sending meeting report..."):
                send_meeting_report(result)

            st.success(
                f"Meeting report sent successfully to "
                f"{len(attendees)} attendee(s)."
            )

        except Exception as e:
            st.error(f"Email failed: {e}")
