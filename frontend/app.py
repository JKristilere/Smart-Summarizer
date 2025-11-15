"""
Advanced Streamlt Frontend with Streaming Support
"""

import streamlit as st
import os
import requests
from typing import Optional, Dict, Any, Generator
import time
from datetime import datetime
import json


BASE_URL= os.getenv("BACKEND_URL", "http://localhost:8000")
# BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Smart Summarizer & Chat App",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS with animations
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        animation: fadeIn 0.5s;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 4px;
        margin: 1rem 0;
        animation: slideIn 0.3s;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
    }
    .typing-indicator {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: #e9ecef;
        border-radius: 20px;
        margin: 0.5rem 0;
    }
    .typing-indicator span {
        animation: blink 1.4s infinite;
        font-size: 1.2rem;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes blink {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .session-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    .quick-action-btn {
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 20px;
        border: 2px solid #667eea;
        background: white;
        color: #667eea;
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-action-btn:hover {
        background: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_file_id' not in st.session_state:
    st.session_state.current_file_id = None
if 'current_content_type' not in st.session_state:
    st.session_state.current_content_type = None
if 'current_url' not in st.session_state:
    st.session_state.current_url = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processing' not in st.session_state:
    st.session_state.processing = False


# Helper Functions
def make_request(method:str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server. Please ensure it's running.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The content might be too large or the sever is busy.")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Server error: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None
    
def stream_chat_response(query:str, file_id: str, 
                         include_vector_search: bool = True, 
                         top_k: int = 5) -> Generator[str, None, None]:
    """Stream chat response from backend"""
    try:
        url = f"{BASE_URL}/chat/stream/"
        data = {
            "query": query,
            "file_id": file_id,
            "include_vector_search": include_vector_search,
            "top_k": top_k
        }

        with requests.post(url, json=data, stream=True, timeout=300) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"


# Sidebar
with st.sidebar:
    st.markdown("<div class='main-header'>🎥 Smart Summarizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>AI-Powered Content Analysis</div>", unsafe_allow_html=True)
    
    st.divider()

    # Mode selection
    mode = st.radio(
        "Select Content Type",
        ["📺 YouTube Video", "🎵 Audio File"],
        index=0
    )

    st.divider()

    # Current session info
    if st.session_state.current_file_id:
        st.markdown("### 🎯 Active Session")
        st.markdown(f"<div class='session-badge'>{st.session_state.current_content_type}</div>", 
                    unsafe_allow_html=True)
        st.code(st.session_state.current_file_id, language=None)

        if st.session_state.current_url:
            st.markdown(f"**Source:** {st.session_state.current_url[:50]}...")
        
        st.divider()

        # Quick actions
        st.markdown("### Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                with st.spinner("Refreshing..."):
                    result = make_request("POST", "/chat/history/",
                                          json={"file_id": st.session_state.current_file_id,
                                                "limit": 50})
                    if result and result.get("status") == "success":
                        st.session_state.chat_history = result.get("history", [])
                        st.success("Chat history refreshed!")
                        time.sleep(0.5)
                        st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                result = make_request("DELETE", f"/chat/history/{st.session_state.current_file_id}")
                if result and result.get("status") == "success":
                    st.session_state.messages = []
                    st.session_state.chat_history = []
                    st.success("Chat history cleared!")
                    time.sleep(0.5)
                    st.rerun()
        
        if st.button("🆕 New Session", use_container_width=True, type="primary"):
            for key in ['current_file_id', 'current_content_type', 'current_url', 
                       'messages', 'summary', 'chat_history']:
                if key in st.session_state:
                    st.session_state[key]= None if key != 'messages' else []
            st.rerun()

    st.divider()


    # Settings
    with st.expander(" ⚙️ Settings", expanded=False):
        use_streaming = st.checkbox("Enable Streaming", value=False,
                                    help="Stream responses in real-time (recommended)")
        include_vector_search = st.checkbox("Include Vector Search", value=True,
                                            help="Search relevant content for answers")
        top_k = st.slider("Context Chunks", min_value=1, max_value=10, value=5,
                          help="Number of relevant chunks to retrieve")
        
        st.divider()

        st.markdown("**Performance Mode:**")
        if st.radio("Select", ["⚡ Fast (less context)", "🎯 Balanced", "🔬 Detailed (more context)"], 
                   index=1, label_visibility="collapsed") == "⚡ Fast (less context)":
            top_k = 3
        elif st.radio("Select", ["⚡ Fast", "🎯 Balanced", "🔬 Detailed"], 
                     index=1, label_visibility="collapsed") == "🔬 Detailed (more context)":
            top_k = 8

    st.divider()

    # Stats
    if st.session_state.chat_history:
        st.markdown("### 📊 Session Stats")
        total_msgs = len(st.session_state.chat_history)
        user_msgs = sum(1 for msg in st.session_state.chat_history if msg["role"] == "user")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", total_msgs)
        with col2:
            st.metric("User Messages", user_msgs)
    
    st.divider()


    # About
    with st.expander("ℹ️ About & Help"):
        st.markdown("""
        **Version:** 1.00
        **Model:** Llama 3.3 70B
        **Features:**
        - Real-time streaming
        - Context-aware chat
        - Persistent history
        - Multi-format support
        
        **Support:** [GitHub](https://github.com/JKristilere/smart-summarizer)
        """)


# Main content
st.markdown("<div class='main-header'>AI Content Analyzer</div>", unsafe_allow_html=True)

# Create tabs
if st.session_state.current_file_id:
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📝 Summary", "📜 History", "💡 Suggested Questions"])
else:
    tab1, tab2 = st.tabs(["📥 Ingest Content", "📖 Getting Started"])
    tab3, tab4 = None, None

# Tab 1: Ingest or Chat
if st.session_state.current_file_id:
    with tab1:
        st.markdown("### Interactive Chat")

        # Chat container
        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("💭 Ask anything about the content...", key="chat_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Gen AI reponse
            with st.chat_message("assistant"):
                if use_streaming:
                    # Streaming reponse
                    response_placeholder = st.empty()
                    full_response = ""

                    for chunk in stream_chat_response(
                        query=prompt,
                        file_id=st.session_state.current_file_id,
                        include_vector_search=include_vector_search,
                        top_k=top_k
                    ):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")

                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    # Response without streaming
                    with st.spinner("Generating response..."):
                        result = make_request("POST", "/chat/",
                                              json={
                                                  "query": prompt,
                                                  "file_id": st.session_state.current_file_id,
                                                  "include_vector_search": include_vector_search,
                                                  "top_k": top_k
                                              })
                        if result and result.get("status") == "success":
                            response = result.get("response", "No response received")
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            error_msg = "❌ Sorry, I couldn't process your request."
                            st.error(error_msg)

else:
    with tab1:
        if mode == "📺 YouTube Video":
            st.markdown("### 📺 YouTube Video Analysis")

            # Input selection
            st.markdown("#### Enter a YouTube video URL:")
            youtube_url = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                label_visibility="collapsed"
            )


            # Advanced options
            with st.expander("🔍 Advanced Options"):
                youtube_query = st.text_area(
                    "Optional: Ask a specific question",
                    placeholder="e.g., What are the main topics? What statistics are mentioned?",
                    height=100
                )

            # Process button
            if st.button("🎥 Load Video", use_container_width=True, type="primary"):
                if not youtube_url:
                    st.warning("Please enter a YouTube video URL.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("📥 Fetching video transcript...")
                    progress_bar.progress(25)

                    with st.spinner("Processing..."):
                        result = make_request("POST", "/ingest/youtube/",
                                              json={
                                                  "url": youtube_url,
                                                  "query": youtube_query or None
                                              })
                        
                        progress_bar.progress(75)
                        status_text.text("Generating summary...")

                        if result and result.get("status") == "success":
                            progress_bar.progress(100)
                            status_text.text("✅ Complete!")

                            st.session_state.current_file_id = result.get("video_id")
                            st.session_state.current_content_type = "YouTube Video"
                            st.session_state.current_url = youtube_url
                            st.session_state.summary = result.get("summary")
                            st.session_state.messages = []
                            
                            st.success("🎉 Video analyzed successfully!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()

                        else:
                            progress_bar.empty()
                            status_text.empty()
                            error_msg = "❌ Failed to process video. Please check the URL."
                            st.error(error_msg)
        
        else:  # Audio File
            st.markdown("### 🎵 Audio File Analysis")

            # File uploader with preview
            audio_file = st.file_uploader(
                "Upload an Audio File",
                type=["mp3", "wav", "m4a", "mp4"],
                # type=["video/mp4", "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a"],
                help="Supported formats: MP3, WAV, M4A, MP4"
            )

            if audio_file:
                # Show file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Filename", audio_file.name)
                with col2:
                    st.metric("File Size", f"{audio_file.size / 1024/ 1024:.2f} MB")
                with col3:
                    st.metric("File Type", audio_file.type)

                # Advanced options
                with st.expander("🔍 Advanced Options"):
                    audio_query = st.text_area(
                        "Optional: Ask a specific question",
                        placeholder="e.g., What are the action items? Who said what?",
                        height=100
                    )

                # Process button
                if st.button("🚀 Transcribe & Analyze", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("🎙️ Transcribing audio...")
                    progress_bar.progress(25)

                    try:
                        # Reset file pointer to beginning
                        audio_file.seek(0)

                        # Read file content

                        file_content = audio_file.read()
                        files = {"audio_file": (audio_file.name, file_content, audio_file.type)}
                        data = {"query": audio_query if audio_query else None} 
                        
                        with st.spinner("This may take a few minutes..."):

                            result = make_request("POST", "/ingest/audio/", files=files, data=data)
                            progress_bar.progress(75)
                            status_text.text("Generating summary...")

                            if result and result.get("status") == "success":
                                progress_bar.progress(100)
                                status_text.text("✅ Complete!")

                                st.session_state.current_file_id = result.get("file_id")
                                st.session_state.current_content_type = "Audio File"
                                st.session_state.current_url = audio_file.name
                                st.session_state.summary = result.get("summary")
                                st.session_state.messages = []

                                st.success("🎉 Audio file analyzed successfully!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()

                            else:
                                progress_bar.empty()
                                status_text.empty()
                                error_msg = "❌ Failed to process audio file. Please check the file format."
                                st.error(error_msg)

                    except requests.exceptions.Timeout:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("⏱️ Request timed out. The audio file might be too large (>100MB) or processing is taking longer than expected.")
                    
                    except requests.exceptions.ConnectionError:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("❌ Could not connect to backend server. Please ensure it's running.")
                    
                    except requests.exceptions.HTTPError as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ Server error: {e.response.status_code} - {e.response.text}")
                    
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ Unexpected error: {str(e)}")
                        st.exception(e)  # Show full traceback in development


# Tab 2: Summary or Getting Started
if st.session_state.current_file_id:
    with tab2:
        st.markdown("### 📝 AI-Generated Summary")

        if st.session_state.summary:
            # Summary card
            st.markdown(f"""
                         <div style='background: white; padding: 2rem; border-radius: 12px; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()

            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Copy Summary", use_container_width=True):
                    st.toast("Summary copied to clipboard!", icon="📋")
            with col2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.info("🚧 Feature coming soon!")
            with col3:
                if st.button("💾 Export", use_container_width=True):
                    st.download_button(
                        "Download as TXT",
                        st.session_state.summary,
                        file_name=f"summary_{st.session_state.current_file_id}.txt",
                        mime="text/plain"
                    )
        else:
            st.info("📝 No summary available.")

else:
    with tab2:
        st.markdown("### 📝 Getting Started")

        # Welcome message
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;'>
            <h2 style='color: white; margin: 0;'>Welcome to Smart Summarizer! 🎉</h2>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>
                Analyze YouTube videos and audio files with AI-powered insights
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎥 For Videos")
            st.markdown("""
            1. **Paste URL** - Any YouTube video link
            2. **Get Summary** - Instant AI-powered analysis
            3. **Ask Questions** - Chat about the content
            4. **Export Results** - Save for later
            """)
            
            st.markdown("#### 💡 Example Questions")
            st.code("""
• What is this video about?
• Summarize the main points
• What statistics were mentioned?
• Explain [specific topic]
            """, language=None)
        
        with col2:
            st.markdown("#### 🎵 For Audio")
            st.markdown("""
            1. **Upload File** - MP3, WAV, M4A, MP4
            2. **Auto-Transcribe** - Speech-to-text
            3. **Get Insights** - AI analysis
            4. **Interactive Chat** - Ask anything
            """)
            
            st.markdown("#### 🎯 Use Cases")
            st.code("""
• Meeting transcriptions
• Podcast summaries
• Lecture notes
• Interview analysis
            """, language=None)


if tab3:
    with tab3:
        st.markdown("### 📜 Conversation History")

        # Refresh button
        if st.button("🔄 Refresh History", use_container_width=True):
            with st.spinner("Loading..."):
                result = make_request("POST", "/chat/history/",
                                      json={
                                          "file_id": st.session_state.current_file_id,
                                          "limit": 50
                                      })
                if result and result.get("status") == "success":
                    st.session_state.chat_history = result.get("history", [])
                    st.success("✅ Loaded!")
        
        if st.session_state.chat_history:
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            user_msgs = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
            assistant_msgs = [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
            
            with col1:
                st.metric("📊 Total", len(st.session_state.chat_history))
            with col2:
                st.metric("👤 Questions", len(user_msgs))
            with col3:
                st.metric("🤖 Responses", len(assistant_msgs))
            with col4:
                if st.session_state.chat_history:
                    first_msg = datetime.fromisoformat(st.session_state.chat_history[0]["created_at"].replace("Z", "+00:00"))
                    st.metric("📅 Started", first_msg.strftime("%m/%d"))
            
            st.divider()
            
            # Display messages
            for msg in st.session_state.chat_history:
                timestamp = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                time_str = timestamp.strftime("%I:%M %p")
                
                with st.container():
                    if msg["role"] == "user":
                        st.markdown(f"**👤 You** · _{time_str}_")
                        st.info(msg["message"])
                    else:
                        st.markdown(f"**🤖 Assistant** · _{time_str}_")
                        st.success(msg["message"])
                    st.divider()
        else:
            st.info("📭 No conversation history yet. Start chatting to see your messages!")


if tab4:
    with tab4:
        st.markdown("### 💡 Suggested Questions")
        st.markdown("Click any question to ask it instantly!")
        
        suggestions = {
            "📊 Overview": [
                "What is the main topic of this content?",
                "Give me a comprehensive summary",
                "What are the key takeaways?",
            ],
            "🔍 Details": [
                "What specific examples or case studies are mentioned?",
                "Are there any statistics or data points discussed?",
                "What evidence supports the main arguments?",
            ],
            "💼 Actionable": [
                "What are the action items or recommendations?",
                "How can I apply this information?",
                "What are the next steps suggested?",
            ],
            "🤔 Analysis": [
                "What are the strengths and weaknesses discussed?",
                "How does this compare to industry standards?",
                "What are the potential implications?",
            ]
        }

        for category, questions in suggestions.items():
            st.markdown(f'### {category}')
            cols = st.columns(1)
            for question in questions:
                if st.button(f"💬 {question}", key=f"suggest_{question}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    st.rerun()
            st.divider()


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Built with ❤️ using FastAPI, Streamlit, and Groq LLM</p>
    <p style='font-size: 0.9rem;'>© 2025 Smart Summarizer · All rights reserved</p>
</div>
""", unsafe_allow_html=True)