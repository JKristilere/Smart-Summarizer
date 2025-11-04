# Smart Youtube, Audio and Podcast Summarizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**An open-source LangChain + FastAPI + Streamlit app** that summarizes YouTube videos or podcasts into concise insights, chapters, and key takeaways — all powered by **local LLMs** and **free tools** (no API keys needed).

---

## Features

-  Summarize Youtube video and audio podcasts
- Generate chapter-wise breakdowns and TL;DRs 
- Ask follow-up questions (Q&A) about the content
- Works 100% locally — powered by [Ollama](https://ollama.ai) and [Chroma](https://www.trychroma.com)  
- Clean and simple UI powered by [Streamlit](https://streamlit.io) and FastAPI
-  Optional Whisper transcription for audio files

---

## Installation

1. Clone the repository:

   ```bash
   git clone [https://github.com/your-username/your-repo.git](https://github.com/your-username/your-repo.git)
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment variables:

   ```bash
    export GROQ_API_KEY=your-groq-api-key
    export CHROMA_API_KEY=your-chroma-api-key
   ```

   Note: You can obtain an GROQ API key from [here](https://ollama.ai/) and a Chroma API key from [here](https://www.trychroma.com/).


4. Run the app:

   ```bash
   streamlit run app.py
   ```

   This will start the app on http://localhost:8501.


## Contributing

1. Fork the repository on GitHub.

2. Create a new branch for your changes.

3. Make your changes and commit them.

4. Push your changes to your forked repository.

5. Submit a pull request to the original repository.

## License

This project is licensed under the MIT License.
