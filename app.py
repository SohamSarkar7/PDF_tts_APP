import streamlit as st
import sys
import re
import os
from exception import CustomeException
from loggers import logging
import fitz
import easyocr
import numpy as np
from pdf2image import convert_from_path
from transformers import pipeline
import io
from gtts import gTTS
import tempfile

# Initialize EasyOCR reader
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['en'])

reader = load_ocr_reader()

# Initialize Hugging Face summarization pipeline and cache it
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

summarizer = load_summarizer()

def pdf_reader(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        text = ""

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            page_text = page.get_text()

            if page_text.strip():
                text += page_text
            else:
                images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
                for img in images:
                    img_np = np.array(img)
                    extracted_text = reader.readtext(img_np, detail=0)
                    text += " ".join(extracted_text)

        return text
    except Exception as e:
        logging.info("Error occured in Pdf file")
        raise CustomeException(e, sys)

def cleaned_data(text):
    main = text.strip().split("\n")
    text = [re.sub(r'[*\-#:•✔✓▶●@]', '', i).strip() for i in main if i.strip()]
    return text

def chunk_text(text, max_tokens=512):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def summarize_large_text(text, target_length=1000, min_length=30):
    try:
        chunks = chunk_text(text, max_tokens=512)
        summaries = []
        for chunk in chunks:
            if chunk.strip():
                summary = summarizer(chunk, max_length=250, min_length=min_length, do_sample=False)
                summaries.append(summary[0]['summary_text'])

        combined_summary = " ".join(summaries)

        final_summary = combined_summary
        while len(final_summary.split()) > target_length:
            final_summary = summarizer(final_summary, max_length=target_length + 200, min_length=min_length, do_sample=False)[0]['summary_text']

        final_summary_words = final_summary.split()
        if len(final_summary_words) > target_length:
            final_summary = " ".join(final_summary_words[:target_length])

        return final_summary
    except Exception as e:
        raise CustomeException(e, sys)
    
def convert_text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en',tld ='co.in')

        audio_dir = 'Audio_files'
        os.makedirs(audio_dir,exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3',dir=audio_dir) as tmp_file:
            audio_path = tmp_file.name
            tts.save(audio_path)
        st.success("Audio generated successfully!")
        return audio_path
    except Exception as e:
        st.error(f"Failed to convert text to speech: {str(e)}")
        return None


def process_pdf(uploaded_file, target_length):
    try:
        file_stream = io.BytesIO(uploaded_file.read())
        with fitz.open(stream=file_stream, filetype="pdf") as pdf_document:
            text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()

                if page_text.strip():
                    text += page_text
                else:
                    file_stream.seek(0) # reset stream to beginning.
                    images = convert_from_path(file_stream, first_page=page_num + 1, last_page=page_num + 1)
                    for img in images:
                        img_np = np.array(img)
                        extracted_text = reader.readtext(img_np, detail=0)
                        text += " ".join(extracted_text)

        cleaned_text = cleaned_data(text)
        cleaned_text = " ".join(cleaned_text)

        summary = summarize_large_text(cleaned_text, target_length=target_length)
        return summary
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url('background.jpg'); /* Replace with your image path */
        background-size: cover;
        background-repeat: no-repeat;
    }
    .title-bar {
        background: linear-gradient(to right, #6a11cb, #2575fc);
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        animation: neon 2s ease-in-out infinite alternate;
    }
    @keyframes neon {
        from { box-shadow: 0 0 10px #6a11cb; }
        to { box-shadow: 0 0 20px #2575fc; }
    }
    .st-emotion-cache-1y4p8pa {
        background-color: rgba(30, 30, 30, 0.8);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .st-emotion-cache-10trblm {
        background-color: rgba(40, 40, 40, 0.8);
        padding: 10px;
        border-radius: 5px;
    }
    .st-file-uploader div div {
        background: linear-gradient(135deg, #444, #222);
        border: 2px solid #555;
        padding: 25px;
        border-radius: 12px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .st-file-uploader div div:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.4);
    }
    .st-button button {
        background: linear-gradient(to right,rgb(244, 24, 75),rgb(172, 62, 42));
        color: white;
        padding: 15px 30px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .st-button button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.3);
    }
    .st-button button.masterpiece {
        background: linear-gradient(to right, #4a00e0, #8e2de2);
        animation: masterpieceGlow 2s ease-in-out infinite alternate;
    }
    @keyframes masterpieceGlow {
        from { box-shadow: 0 0 15px #4a00e0; }
        to { box-shadow: 0 0 30px #8e2de2; }
    }
    .st-spinner > div > div {
        border-color: #ff4b2b;
        border-left-color: transparent;
        border-width: 4px;
        width: 40px;
        height: 40px;
    }
    .summary-box {
        background-color: white;
        color: #333;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title-bar"><h1> PDF Listner </h1></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
logging.info("Successfully File Uploaded")
target_length = st.slider("Target Summary Length (words)", min_value=100, max_value=2000, value=1000, step=100)
logging.info("Target seted")

if uploaded_file is not None:
    if st.button("Summarize"):
        st.markdown("""
            <script>
            const button = document.querySelector('.st-button button');
            button.classList.add('masterpiece');
            </script>
            """, unsafe_allow_html=True)
        with st.spinner("Summerizing..."):
            summary = process_pdf(uploaded_file, target_length)
            logging.info("Summery extracted succesfully")
            st.markdown("""
                <script>
                const button = document.querySelector('.st-button button');
                button.classList.remove('masterpiece');
                </script>
                """, unsafe_allow_html=True)
            if summary:
                st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                logging.info("Summery Displayed")
                audio_path = convert_text_to_speech(summary)
                if audio_path:
                    st.audio(audio_path, format="audio/mp3")
                    with open(audio_path, 'rb') as audio_file:
                        st.download_button("Download Audio", data=audio_file, file_name="Summery.mp3")
            else:
                st.error("Failed to convert text to speech.")
                