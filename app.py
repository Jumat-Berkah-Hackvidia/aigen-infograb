# --- START OF MODIFIED app.py ---

import streamlit as st
import requests
import json

# --- Configuration ---
DEFAULT_API_ENDPOINT = "http://localhost:8080" # Base URL

# --- Page Setup ---
st.set_page_config(
    page_title="AI Product Brief Generator", # Updated title
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Existing CSS here */
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; margin-bottom: 1rem; text-align: center; }
    .sub-header { font-size: 1.5rem; font-weight: bold; color: #2563EB; margin-top: 1.5rem; margin-bottom: 0.75rem; border-bottom: 2px solid #DBEAFE; padding-bottom: 0.25rem; }
    .card { background-color: #F9FAFB; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #E5E7EB; }
    .result-card { background-color: #EFF6FF; padding: 1.5rem; border-radius: 0.5rem; border-left: 5px solid #2563EB; margin-bottom: 1rem; }
    .info-text { font-size: 0.9rem; color: #6B7280; }
    .stButton>button { width: 100%; background-color: #1D4ED8; color: white; }
    .stDownloadButton>button { width: 100%; background-color: #3B82F6; color: white; border: none; }
    .stDownloadButton>button:hover { background-color: #2563EB; }
    .centered-text { text-align: center; margin-bottom: 1.5rem; }
    .footer-text { text-align: center; font-size: 0.8rem; color: #9CA3AF; margin-top: 2rem; }
    .download-pdf-link { display: block; background-color: #3B82F6; color: white !important; padding: 0.55rem; text-align: center; border-radius: 0.5rem; font-weight: bold; text-decoration: none; width: 100%; box-sizing: border-box; transition: background-color 0.2s ease; }
    .download-pdf-link:hover { background-color: #2563EB; color: white !important; text-decoration: none; }
    /* Style for the displayed image */
    .processed-image-container { margin-top: 1rem; margin-bottom: 1rem; padding: 1rem; background-color: #F9FAFB; border: 1px dashed #D1D5DB; border-radius: 0.5rem; text-align: center; }
    .processed-image-container img { max-width: 100%; height: auto; max-height: 350px; border-radius: 0.375rem; }
</style>
""", unsafe_allow_html=True)

# --- Main Title ---
st.markdown('<p class="main-header">AI Product Brief Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="centered-text info-text">Upload campaign details, product image, and documents to get AI-powered suggestions.</p>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<p class="sub-header" style="margin-top:0; border:none;">API Configuration</p>', unsafe_allow_html=True)
    api_base_url = st.text_input(
        "API Base URL", value=DEFAULT_API_ENDPOINT,
        help="Base URL of the API (e.g., http://localhost:8080)"
    )
    generate_brief_endpoint = f"{api_base_url.rstrip('/')}/generate-brief"
    st.divider()
    st.markdown("### About This App")
    st.info(
        "Uses Google Gemini AI via a backend API to enhance product briefs. "
        "Uploaded images are linked to your email."
    )
    st.markdown("### How it Works")
    st.markdown(
        "1. Enter Email\n"
        "2. Fill Campaign Info\n"
        "3. (Optional) Upload Image\n"
        "4. (Optional) Upload PDF\n"
        "5. Generate\n"
        "6. Review & Download"
    )

# --- Main Content Columns ---
col1, col2 = st.columns([3, 2], gap="large")

# --- Input Form (Left Column) ---
with col1:
    st.markdown('<p class="sub-header">Provide Your Campaign Details</p>', unsafe_allow_html=True)
    with st.form(key="campaign_form"):
        st.markdown("#### Core Information")
        email = st.text_input("Your Email Address*", placeholder="user@example.com", help="Required. Links uploads.")
        # ... (keep other input fields as before) ...
        campaign_name = st.text_input("Campaign Name", placeholder="e.g., Summer Splash Swimwear Launch")
        product_name = st.text_input("Product Name", placeholder="e.g., Summer Swim Set")
        platform = st.selectbox("Platform", options=["Instagram", "Facebook", "Twitter", "TikTok"], index=0)
        category = st.text_input("Category", placeholder="e.g., Apparel - Swimwear")
        price_range = st.text_input("Price Range", placeholder="e.g., Rp 20,000 - Rp 50,000")
        campaign_period = st.text_input("Campaign Period", placeholder="e.g., June 1st - July 31st, 2024")

        st.markdown("#### Current Brief Details (Optional)")
        st.markdown('<p class="info-text">Provide existing brief sections for the AI to improve.</p>', unsafe_allow_html=True)
        current_description = st.text_area("Current Campaign Description", placeholder="Enter existing description...", height=100)
        current_goals = st.text_area("Current Campaign Goals", placeholder="Enter existing goals...", height=100)
        current_notes = st.text_area("Current Important Notes", placeholder="Enter existing notes...", height=100)

        st.markdown("#### Supporting Files (Optional)")
        product_image = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"], help="Upload product image (Max 10MB).")
        pdf_file = st.file_uploader("Upload Supporting PDF", type=["pdf"], help="Upload relevant PDF (Max 10MB).")
        if product_image: st.image(product_image, caption="Uploaded Image Preview", width=250)

        submit_button = st.form_submit_button("✨ Generate Product Brief ✨")

# --- Function to make API request ---
def call_generate_api(api_url, form_data, files):
    """Sends data to the backend API and handles response."""
    try:
        st.toast(f"Sending request to {api_url}...")
        response = requests.post(api_url, data=form_data, files=files, timeout=120)
        response.raise_for_status()
        st.toast("Received response from API.", icon="✅")
        return response.json(), None
    except requests.exceptions.RequestException as e: # Catch broader request errors
        error_message = f"API Request Failed: {e.__class__.__name__}"
        details = ""
        if isinstance(e, requests.exceptions.HTTPError):
            error_message = f"API Error: {e.response.status_code}"
            try: details = e.response.json().get('error', e.response.text)
            except: details = e.response.text
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_message = f"Connection Error: Cannot connect to API at {api_url}."
        elif isinstance(e, requests.exceptions.Timeout):
            error_message = "Request Timeout: API took too long."

        full_error = f"{error_message}{' - ' + details if details else ''}"
        st.error(f"Failed to generate brief: {full_error}")
        print(f"API Call Error: {full_error}") # Log full error for debugging
        return None, full_error
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        st.error(error_message)
        print(f"Unexpected Error during API call: {error_message}")
        return None, error_message

# --- Process Form Submission ---
if submit_button:
    if not email:
        st.warning("⚠️ Please enter your email address.", icon="📧")
    elif not api_base_url:
        st.warning("⚠️ Please enter the API Base URL in the sidebar.", icon="⚙️")
    else:
        form_data = { "email": email, "campaign_name": campaign_name, "product_name": product_name,"platform": platform, "category": category, "price_range": price_range, "campaign_period": campaign_period, "current_description": current_description, "current_goals": current_goals, "current_notes": current_notes }
        files = {}
        if product_image: files["product_image"] = (product_image.name, product_image, product_image.type)
        if pdf_file: files["pdf_file"] = (pdf_file.name, pdf_file, pdf_file.type)

        with st.spinner("🧠 Generating brief with AI... Please wait..."):
            result, error = call_generate_api(generate_brief_endpoint, form_data, files)

        # --- Display Results (Right Column) ---
        with col2:
            st.markdown('<p class="sub-header">Generated Product Brief</p>', unsafe_allow_html=True)
            if error:
                st.markdown('<div class="card"><p class="info-text">Generation failed. See error above.</p></div>', unsafe_allow_html=True)
            elif result:
                st.session_state.api_result = result
                st.session_state.api_base_url = api_base_url # Store base url used

                st.success("🎉 Product brief generated successfully!")

                # ***** DISPLAY IMAGE USED *****
                image_url = result.get("image_url")
                if image_url:
                    st.markdown('<div class="processed-image-container">', unsafe_allow_html=True)
                    st.markdown("###### Image Used in Analysis")
                    try:
                        # Attempt to display the image directly from the URL
                        st.image(image_url, caption="Image processed by the AI")
                    except Exception as img_display_err:
                        # Fallback if st.image fails (e.g., network issue, invalid format)
                        st.warning(f"Could not display image preview from URL.")
                        st.caption(f"Image URL: {image_url}")
                        print(f"Streamlit st.image error: {img_display_err}")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("ℹ️ No product image was processed for this brief.")
                # ******************************

                # Display text sections
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("#### Campaign Description")
                st.markdown(result.get("Campaign Description", "_No description generated._"))
                st.markdown('</div>', unsafe_allow_html=True)
                # ... (display Goals and Notes cards as before) ...
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("#### Campaign Goals")
                st.markdown(result.get("Campaign Goals", "_No goals generated._"))
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("#### Important Notes")
                st.markdown(result.get("Important Note", "_No important notes generated._"))
                st.markdown('</div>', unsafe_allow_html=True)

                # Download section
                st.markdown("---")
                st.markdown("#### Download Results")
                download_col1, download_col2 = st.columns(2)
                json_data = json.dumps(st.session_state.api_result, indent=2)
                with download_col1:
                    st.download_button(label="📥 Download JSON", data=json_data, file_name=f"{campaign_name or 'product'}_brief.json", mime="application/json", use_container_width=True)
                if "request_id" in st.session_state.api_result:
                    with download_col2:
                        pdf_download_url = f"{st.session_state.api_base_url.rstrip('/')}/download-pdf/{st.session_state.api_result['request_id']}"
                        st.markdown(f'<a href="{pdf_download_url}" target="_blank" class="download-pdf-link">📄 Download PDF</a>', unsafe_allow_html=True)
                else:
                    with download_col2: st.caption("PDF download unavailable.")

            else:
                st.warning("No results returned from the API.")

# --- Placeholder or Redraw from Session State ---
# Check if results exist in session state
if 'api_result' in st.session_state and not submit_button:
    # Redraw previous results if page reloads without new submission
    with col2:
            st.markdown('<p class="sub-header">Generated Product Brief (Previous)</p>', unsafe_allow_html=True)
            result = st.session_state.api_result
            api_base_url_used = st.session_state.api_base_url

            # ***** DISPLAY IMAGE USED (from session state) *****
            image_url = result.get("image_url")
            if image_url:
                st.markdown('<div class="processed-image-container">', unsafe_allow_html=True)
                st.markdown("###### Image Used in Analysis")
                try: st.image(image_url, caption="Image processed by the AI")
                except Exception as img_display_err:
                    st.warning(f"Could not display image preview from URL.")
                    st.caption(f"Image URL: {image_url}")
                    print(f"Streamlit st.image error on redraw: {img_display_err}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("ℹ️ No product image was processed for this brief.")
            # ******************************

            # Display text sections 
            st.markdown('<div class="result-card">', unsafe_allow_html=True); st.markdown("#### Campaign Description"); st.markdown(result.get("Campaign Description", "_No description generated._")); st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-card">', unsafe_allow_html=True); st.markdown("#### Campaign Goals"); st.markdown(result.get("Campaign Goals", "_No goals generated._")); st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-card">', unsafe_allow_html=True); st.markdown("#### Important Notes"); st.markdown(result.get("Important Note", "_No important notes generated._")); st.markdown('</div>', unsafe_allow_html=True)

            # Download section 
            st.markdown("---"); st.markdown("#### Download Results"); download_col1, download_col2 = st.columns(2)
            json_data = json.dumps(result, indent=2)
            with download_col1: st.download_button(label="📥 Download JSON", data=json_data, file_name=f"{result.get('campaign_name', 'product')}_brief.json", mime="application/json", use_container_width=True)
            if "request_id" in result:
                with download_col2: pdf_download_url = f"{api_base_url_used.rstrip('/')}/download-pdf/{result['request_id']}"; st.markdown(f'<a href="{pdf_download_url}" target="_blank" class="download-pdf-link">📄 Download PDF</a>', unsafe_allow_html=True)
            else: 
                with download_col2: st.caption("PDF download unavailable.")

elif not submit_button and 'api_result' not in st.session_state:
    # Initial placeholder if no submission yet and nothing in session state
    with col2:
        st.markdown('<p class="sub-header">Generated Product Brief</p>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("📄 Fill out the form and click 'Generate Product Brief'.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown('<p class="footer-text">Powered by Google Gemini 2.0 Flash | Streamlit Interface</p>', unsafe_allow_html=True)

