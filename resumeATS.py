import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# Function to get Gemini output
def get_gemini_output(pdf_text, prompt):
    response = model.generate_content([pdf_text, prompt])
    return response.text

def read_pdf(uploaded_file):
    if uploaded_file is not None:
        pdf_reader = PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() or ""
        return pdf_text
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit UI setup
st.set_page_config(page_title="ResumeATS Pro", layout="wide")

# Apple-like minimal styling
st.markdown("""
    <style>
    .main { background-color: #f5f5f7; color: #1d1d1f; }
    .stButton>button {
        background-color: #0071e3; color: white; border-radius: 20px;
    }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("ResumeATS Pro")
st.subheader("Optimize Your Resume for ATS and Land Your Dream Job 🚀")

# File upload
upload_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

# Job description input
job_description = st.text_area("Enter the job description (optional)")

# Analysis options
analysis_option = st.radio(
    "Choose analysis type:", 
    ["Quick Scan", "Detailed Analysis", "ATS Optimization"]
)

# Session state initialization
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "psychometric_done" not in st.session_state:
    st.session_state.psychometric_done = False
if "response" not in st.session_state:
    st.session_state.response = ""

# Analyze resume
if st.button("Analyze Resume"):
    if upload_file is not None:
        pdf_text = read_pdf(upload_file)

        if analysis_option == "Quick Scan":
            prompt = f"""
            You are ResumeChecker, an expert in resume analysis. Provide a quick scan:
            1. Identify the most suitable profession for this resume.
            2. List 3 key strengths.
            3. Suggest 2 quick improvements.
            4. Give an overall ATS score out of 100.
            
            Resume: {pdf_text}
            Job description: {job_description}
            """
        elif analysis_option == "Detailed Analysis":
            prompt = f"""
            You are ResumeChecker, an expert in resume analysis. Provide a detailed analysis:
            1. Identify the most suitable profession.
            2. List 5 strengths.
            3. Suggest 3–5 improvements with specifics.
            4. Rate Impact, Brevity, Style, Structure, Skills (out of 10).
            5. Review each section (Summary, Experience, Education).
            6. Give an overall ATS score breakdown.
            
            Resume: {pdf_text}
            Job description: {job_description}
            """
        else:  # ATS Optimization
            prompt = f"""
            You are ResumeChecker, an expert in ATS optimization. Analyze the resume:
            1. Identify keywords from the job description to include.
            2. Suggest reformatting for ATS readability.
            3. Recommend keyword density improvements.
            4. Suggest 3–5 ways to tailor the resume for this job.
            5. Give an ATS compatibility score out of 100.
            
            Resume: {pdf_text}
            Job description: {job_description}
            """

        response = get_gemini_output(pdf_text, prompt)
        st.session_state.response = response
        st.session_state.analysis_done = True
        st.session_state.psychometric_done = False  # Reset when new analysis done
        st.session_state.questions = []  # Reset old questions

        st.success("Resume analyzed successfully ✅")

    else:
        st.error("Please upload a resume to analyze.")

# Show analysis results
if st.session_state.analysis_done:
    st.subheader("Analysis Results")
    st.write(st.session_state.response)

    # ============ Psychometric Section ============
    st.markdown("---")
    st.subheader("🧠 Psychometric Assessment")

    st.write(
        "Let's evaluate your personality traits based on your resume and job context. "
        "Answer the following questions honestly to receive insights about your work style and behavioral strengths."
    )

    pdf_text = read_pdf(upload_file) if upload_file else ""

    # Generate psychometric questions only once
    if not st.session_state.questions:
        question_prompt = f"""
        You are a professional psychometric evaluator. Based on this resume and job description, 
        create 5 short, personality-assessment questions that help reveal work habits, team behavior, motivation, and adaptability.
        Resume: {pdf_text}
        Job description: {job_description}
        """
        raw_questions = get_gemini_output(pdf_text, question_prompt)
        st.session_state.questions = [
            q.strip("•- ") for q in raw_questions.split("\n") if q.strip()
        ][:5]  # Keep only 5 clear ones

    # Display questions and text inputs
    for i, q in enumerate(st.session_state.questions):
        st.session_state.answers[q] = st.text_input(f"Q{i+1}. {q}", value=st.session_state.answers.get(q, ""))

    # Submit button
    if st.button("Submit Psychometric Answers"):
        # Combine answers
        answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.answers.items()])
        insight_prompt = f"""
        You are a professional psychologist and career advisor.
        Analyze the following psychometric answers and provide:
        1. A short summary of personality traits.
        2. 3 strengths relevant to workplace success.
        3. 2 potential development areas.
        4. Overall personality fit for the provided job description.
        5. Give an overall psychometric score out of 100.
        
        Answers:
        {answers_text}
        Job description: {job_description}
        """
        insight = get_gemini_output(pdf_text, insight_prompt)

        st.session_state.psychometric_done = True
        st.session_state.insight = insight

    # Show psychometric results if done
    if st.session_state.psychometric_done:
        st.subheader("Personality Insights & Score")
        st.write(st.session_state.insight)

    # ============ End Psychometric Section ============

    # Chat section
    st.markdown("---")
    st.subheader("💬 Have questions about your resume?")
    user_question = st.text_input("Ask me anything about your resume or analysis:")
    if user_question:
        chat_prompt = f"""
        Based on the resume and analysis above, answer:
        {user_question}
        
        Resume text: {pdf_text}
        Previous analysis: {st.session_state.response}
        """
        chat_response = get_gemini_output(pdf_text, chat_prompt)
        st.write(chat_response)

# Sidebar
st.sidebar.title("Resources")
st.sidebar.markdown("""
- [Resume Writing Tips](https://cdn-careerservices.fas.harvard.edu/wp-content/uploads/sites/161/2023/08/College-resume-and-cover-letter-4.pdf)
- [ATS Optimization Guide](https://career.io/career-advice/create-an-optimized-ats-resume)
- [Interview Preparation](https://hbr.org/2021/11/10-common-job-interview-questions-and-how-to-answer-them)
""")

st.sidebar.title("Feedback")
st.sidebar.text_area("Help us improve! Leave your feedback:")
st.sidebar.button("Submit Feedback")
