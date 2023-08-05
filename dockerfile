FROM python:3.11

RUN pip install streamlit numpy pandas matplotlib langchain openai 
RUN pip install beautifulsoup4 
RUN pip install streamlit_chat
