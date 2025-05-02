import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import pandas as pd
import os

# Set page configuration
st.set_page_config(
    page_title="Product Brief Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2563EB;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .result-card {
        background-color: #EFF6FF;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2563EB;
    }
    .info-text {
        font-size: 0.9rem;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<p class="main-header">Product Brief Generator</p>', unsafe_allow_html=True)
st.markdown('Upload campaign information and get AI-generated product brief suggestions')

# Set up sidebar for API configuration
with st.sidebar:
    st.markdown('<p class="sub-header">API Configuration</p>', unsafe_allow_html=True)
    
    # API endpoint input
    api_endpoint = st.text_input(
        "API Endpoint", 
        value="http://localhost:8080/generate-brief",
        help="URL of the Product Brief Suggestion API"
    )
    
    st.divider()
    st.markdown("### About")
    st.info(
        "This Streamlit app serves as a testing interface for the Product Brief "
        "Suggestion API. Upload product information, images, and PDFs to generate "
        "AI-enhanced product briefs using Google's Gemini 2.0 Flash model."
    )

# Create two columns for input and output
col1, col2 = st.columns([3, 2])

# Input form in the left column
with col1:
    st.markdown('<p class="sub-header">Campaign Information</p>', unsafe_allow_html=True)
    
    with st.form(key="campaign_form"):
        # Basic campaign information
        campaign_name = st.text_input("Campaign Name", placeholder="Summer Collection Launch")
        product_name = st.text_input("Product Name", placeholder="Premium Tee Collection")
        category = st.text_input("Category", placeholder="Apparel")
        price_range = st.text_input("Price Range (IDR)", placeholder="150,000 - 300,000")
        campaign_period = st.text_input("Campaign Period", placeholder="June 1 - July 15, 2025")
        
        st.markdown('<p class="sub-header">Current Product Brief</p>', unsafe_allow_html=True)
        st.markdown('<p class="info-text">Enter your existing product brief details that you want to improve</p>', unsafe_allow_html=True)
        
        # Current product brief
        current_description = st.text_area(
            "Campaign Description", 
            placeholder="Enter your current campaign description here...",
            height=100
        )
        
        current_goals = st.text_area(
            "Campaign Goals", 
            placeholder="Enter your current campaign goals here...",
            height=100
        )
        
        current_notes = st.text_area(
            "Important Notes", 
            placeholder="Enter your current important notes here...",
            height=100
        )
        
        st.markdown('<p class="sub-header">Files</p>', unsafe_allow_html=True)
        
        # File uploads
        product_image = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])
        pdf_file = st.file_uploader("Upload PDF Document", type=["pdf"])
        
        # Preview uploaded image
        if product_image:
            st.image(product_image, caption="Uploaded Product Image", width=300)
        
        # Submit button
        submit_button = st.form_submit_button("Generate Product Brief")

# Function to make API request
def generate_product_brief(form_data, files):
    try:
        response = requests.post(api_endpoint, data=form_data, files=files)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Request Error: {str(e)}"

# Process form submission
if submit_button:
    # Prepare form data
    form_data = {
        "campaign_name": campaign_name,
        "product_name": product_name,
        "category": category,
        "price_range": price_range,
        "campaign_period": campaign_period,
        "current_description": current_description,
        "current_goals": current_goals,
        "current_notes": current_notes
    }
    
    # Prepare files
    files = {}
    if product_image:
        files["product_image"] = product_image
    if pdf_file:
        files["pdf_file"] = pdf_file
    
    # Show spinner during API call
    with st.spinner("Generating product brief..."):
        result, error = generate_product_brief(form_data, files)
    
    # Display results in the right column
    with col2:
        st.markdown('<p class="sub-header">Generated Product Brief</p>', unsafe_allow_html=True)
        
        if error:
            st.error(error)
        elif result:
            # Display each section in a formatted card
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### Campaign Description")
            st.write(result.get("Campaign Description", "No description generated"))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="result-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
            st.markdown("### Campaign Goals")
            st.write(result.get("Campaign Goals", "No goals generated"))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="result-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
            st.markdown("### Important Notes")
            st.write(result.get("Important Note", "No important notes generated"))
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add download options in a container
            download_col1, download_col2 = st.columns(2)
            
            # Option to download the result as JSON
            json_data = json.dumps(result, indent=2)
            with download_col1:
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="product_brief.json",
                    mime="application/json",
                )
            
            # Option to download the result as PDF
            if "request_id" in result:
                with download_col2:
                    pdf_url = f"{api_endpoint.replace('/generate-brief', '')}/download-pdf/{result['request_id']}"
                    st.markdown(f'<a href="{pdf_url}" target="_blank" style="text-decoration:none"><div style="background-color:#2778ee;color:white;padding:0.55rem;text-align:center;border-radius:0.5rem;font-weight:bold;display:inline-block;width:100%">Download PDF</div></a>', unsafe_allow_html=True)
        else:
            st.warning("No results returned from the API")

# Initialize the right column with placeholder text if no generation yet
if not submit_button:
    with col2:
        st.markdown('<p class="sub-header">Generated Product Brief</p>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("Fill out the form and click 'Generate Product Brief' to see results here.")
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<p class="info-text">Powered by Gemini 2.0 Flash | Created with Streamlit</p>', unsafe_allow_html=True)