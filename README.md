# AiDorse AI GEN | Product Brief Generator - Setup and Usage Guide

This guide will help you set up and run both the Product Brief API and the Streamlit test interface.

## Prerequisites

- Python 3.7+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey/))

## Setup Instructions

### Step 1: Create a project directory

```bash
mkdir product-brief-generator
cd product-brief-generator
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install dependencies

Create a `requirements.txt` file with the following contents:

```
flask==2.3.3
flask-cors==4.0.0
google-generativeai==0.3.2
PyPDF2==3.0.1
pillow==10.0.1
requests==2.31.0
streamlit==1.28.0
pandas==2.1.1
jinja2==3.1.2
pdfkit==1.0.0
```

**Note:** The PDF generation feature requires `wkhtmltopdf` to be installed on your system:

**For Ubuntu/Debian:**
```bash
sudo apt-get install wkhtmltopdf xvfb fontconfig libxrender1
```

**For macOS:**
```bash
brew install wkhtmltopdf
```

**For Windows:**
Download and install from: https://wkhtmltopdf.org/downloads.html

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Step 4: Save the API for testting with Streamlit app files

1. Save the API code as `api.py`
2. Save the Streamlit interface code as `app.py`

### Step 5: Set up your Gemini API key

```bash
# For Windows
set GEMINI_API_KEY=your_api_key_here

# For macOS/Linux
export GEMINI_API_KEY=your_api_key_here
```
*we're recomending to use the `dotenv` package to manage environment variables in a `.env` file for better security and organization.*

## Running the Application

### Step 1: Start the API server

Open a terminal and run:

```bash
python api.py
```

This will start the Flask API server at http://localhost:8080

### Step 2: Start the Streamlit interface

Open another terminal and run:

```bash
streamlit run app.py
```

This will start the Streamlit app and open it in your default web browser (typically at http://localhost:8501)

## Using the Application

1. **Configure the API**: 
   - In the Streamlit sidebar, verify the API endpoint is set to `http://localhost:8080/generate-brief`

2. **Enter Campaign Information**:
   - Fill in the basic campaign details (name, product, category, etc.)
   - Enter your current product brief that you want to improve
   - Upload a product image (optional)
   - Upload a PDF document with additional information (optional)

3. **Generate Brief**:
   - Click the "Generate Product Brief" button
   - Wait for the API to process your request
   - View the improved product brief in the right panel

4. **Download Results**:
   - Use the "Download JSON" button to save the generated brief

## Troubleshooting

- **API Connection Error**: Make sure the API server is running on port 8080 and accessible
- **Image Processing Errors**: Ensure uploaded images are in JPG, JPEG, or PNG format
- **PDF Processing Errors**: Check that PDFs are valid and readable
- **API Key Issues**: Verify your Gemini API key is correct and has been properly set

## Further Customization

- Modify the API code to adjust the prompt or add additional features
- Customize the Streamlit interface to match your branding or add new functionality
- Extend the application to save generated briefs to a database

For any additional help, refer to the documentation for [Flask](https://flask.palletsprojects.com/), [Streamlit](https://docs.streamlit.io/), and [Google Generative AI](https://ai.google.dev/docs).