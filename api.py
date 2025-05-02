import base64
import json
import tempfile
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import google.generativeai as genai
import PyPDF2
import requests
from PIL import Image
from io import BytesIO
import jinja2
import pdfkit
import uuid
import os

app = Flask(__name__)
CORS(app)

# Configure Gemini API
def configure_genai(api_key):
    genai.configure(api_key=api_key)

# Alternative PDF generation method using direct HTML content
def generate_pdf_from_html(html_content):
    """Generate a PDF directly from HTML content"""
    try:
        # Create a temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Create temporary file paths
        pdf_path = os.path.join(temp_dir, 'product_brief.pdf')
        
        # Configure pdfkit options
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'quiet': None
        }
        
        # Generate PDF directly from HTML content
        pdfkit.from_string(html_content, pdf_path, options=options)
        
        return pdf_path
    except Exception as e:
        print(f"Error in direct HTML to PDF conversion: {str(e)}")

# Process PDF file
def process_pdf(pdf_file):
    pdf_text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_text += page.extract_text()
    except Exception as e:
        return f"Error processing PDF: {str(e)}"
    
    return pdf_text

# Process image using Gemini's vision capability
def process_image(image_data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        prompt = "Describe this product image in detail, including key features, design elements, and any text visible in the image."
        response = model.generate_content(prompt, image_parts)
        return response.text
    except Exception as e:
        return f"Error processing image: {str(e)}"

# Generate improved product brief
def generate_product_brief(campaign_info, pdf_content=None, image_description=None):
    # Initialize Gemini 2.0 Flash model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Prepare prompt with all available information
    prompt = f"""
    Please analyze the following campaign information and generate an improved product brief.
    
    CAMPAIGN INFORMATION:
    {json.dumps(campaign_info, indent=2)}
    
    {"IMAGE DESCRIPTION:" + image_description if image_description else ""}
    
    {"ADDITIONAL CONTEXT FROM PDF:" + pdf_content if pdf_content else ""}
    
    Based on the above information, please provide:
    1. An improved campaign description that is engaging and highlights the product's key benefits
    2. Clear campaign goals that are specific, measurable, and aligned with the product's positioning
    3. Important notes that should be considered during the campaign execution
    
    Format your response as a JSON with these keys: "Campaign Description", "Campaign Goals", "Important Note" and kept it the value inside in text format so theres no ugly json mess
    """
    
    # Generate response
    response = model.generate_content(prompt)
    
    try:
        # Extract JSON from response
        response_text = response.text
        # Find JSON content between ```json and ``` if present
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        result = json.loads(json_str)
        
        # Ensure all required keys are present
        required_keys = ["Campaign Description", "Campaign Goals", "Important Note"]
        for key in required_keys:
            if key not in result:
                result[key] = "No information provided"
                
        return result
    except Exception as e:
        return {
            "Campaign Description": "Error parsing model response",
            "Campaign Goals": "Error parsing model response",
            "Important Note": f"Error: {str(e)}"
        }

# Template for PDF generation
PDF_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ campaign_info.campaign_name }} - Product Brief</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #2563EB;
            padding-bottom: 20px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #1E3A8A;
        }
        .campaign-title {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
            color: #1E3A8A;
        }
        .meta-info {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin: 20px 0;
            background-color: #F3F4F6;
            padding: 15px;
            border-radius: 8px;
        }
        .meta-item {
            margin-bottom: 10px;
            flex-basis: 48%;
        }
        .meta-label {
            font-weight: bold;
            color: #6B7280;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #F8FAFC;
            border-radius: 8px;
            border-left: 5px solid #2563EB;
        }
        .section-title {
            font-size: 20px;
            font-weight: bold;
            color: #2563EB;
            margin-top: 0;
            margin-bottom: 15px;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 12px;
            color: #6B7280;
            border-top: 1px solid #E5E7EB;
            padding-top: 20px;
        }
        .image-container {
            text-align: center;
            margin: 20px 0;
        }
        img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Product Brief Generator</div>
        <h1 class="campaign-title">{{ campaign_info.campaign_name }}</h1>
        <p>Generated on {{ generation_date }}</p>
    </div>

    <div class="meta-info">
        <div class="meta-item">
            <div class="meta-label">Product Name:</div>
            <div>{{ campaign_info.product_name }}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Category:</div>
            <div>{{ campaign_info.category }}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Price Range:</div>
            <div>{{ campaign_info.price_range }}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Campaign Period:</div>
            <div>{{ campaign_info.campaign_period }}</div>
        </div>
    </div>

    {% if has_image %}
    <div class="image-container">
        <img src="{{ image_path }}" alt="Product Image">
    </div>
    {% endif %}

    <div class="section">
        <h2 class="section-title">Campaign Description</h2>
        <div>{{ brief.campaign_description|replace('\n', '<br>')|safe }}</div>
    </div>

    <div class="section">
        <h2 class="section-title">Campaign Goals</h2>
        <div>{{ brief.campaign_goals|replace('\n', '<br>')|safe }}</div>
    </div>

    <div class="section">
        <h2 class="section-title">Important Notes</h2>
        <div>{{ brief.important_note|replace('\n', '<br>')|safe }}</div>
    </div>

    <div class="footer">
        <p>Generated using AI-powered Product Brief Generator</p>
        <p>© {{ current_year }} Product Brief Generator</p>
    </div>
</body>
</html>
"""

def generate_pdf(campaign_info, brief, image_path=None):
    """Generate a PDF file for the product brief"""
    try:
        # Create a temp directory to store files
        temp_dir = tempfile.mkdtemp()
        
        # If image exists, create a base64 encoded version for embedding in HTML
        image_data_uri = None
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                image_binary = img_file.read()
                image_base64 = base64.b64encode(image_binary).decode('utf-8')
                image_type = "jpeg"  # Default to JPEG
                if image_path.lower().endswith('.png'):
                    image_type = "png"
                elif image_path.lower().endswith('.gif'):
                    image_type = "gif"
                image_data_uri = f"data:image/{image_type};base64,{image_base64}"
        
        # Prepare template data
        template_data = {
            'campaign_info': campaign_info,
            'brief': {
                'campaign_description': brief.get('Campaign Description', ''),
                'campaign_goals': brief.get('Campaign Goals', ''),
                'important_note': brief.get('Important Note', '')
            },
            'generation_date': datetime.datetime.now().strftime('%B %d, %Y'),
            'current_year': datetime.datetime.now().year,
            'has_image': image_data_uri is not None,
            'image_path': image_data_uri if image_data_uri else ''
        }
        
        # Render the HTML template
        template = jinja2.Template(PDF_TEMPLATE)
        html_content = template.render(**template_data)
        
        # Create HTML file
        html_path = os.path.join(temp_dir, 'product_brief.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate PDF from HTML
        pdf_path = os.path.join(temp_dir, 'product_brief.pdf')
        
        # Use pdfkit with proper configuration
        pdfkit_options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,  # Allow access to local files
            'quiet': None
        }
        
        pdfkit.from_file(html_path, pdf_path, options=pdfkit_options)
        
        return pdf_path
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None

@app.route('/generate-brief', methods=['POST'])
def create_product_brief():
    try:
        # Create a unique ID for this request (used for temp files)
        request_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()
        
        # Extract form data
        campaign_info = {
            "campaign_name": request.form.get('campaign_name', ''),
            "product_name": request.form.get('product_name', ''),
            "category": request.form.get('category', ''),
            "price_range": request.form.get('price_range', ''),
            "campaign_period": request.form.get('campaign_period', ''),
            "current_description": request.form.get('current_description', ''),
            "current_goals": request.form.get('current_goals', ''),
            "current_notes": request.form.get('current_notes', '')
        }
        
        # Process PDF if provided
        pdf_content = None
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '':
                pdf_content = process_pdf(pdf_file)
        
        # Process image if provided
        image_description = None
        image_path = None
        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file.filename != '':
                # Save image to temp directory for PDF
                image_path = os.path.join(temp_dir, f"product_image_{request_id}.jpg")
                image = Image.open(image_file)
                image.save(image_path)
                
                # Get description for AI
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                image_description = process_image(image_data)
        
        # Generate improved product brief
        improved_brief = generate_product_brief(campaign_info, pdf_content, image_description)
        
        # Store the brief for PDF generation endpoint
        app.config[f'brief_{request_id}'] = {
            'campaign_info': campaign_info,
            'brief': improved_brief,
            'image_path': image_path,
            'temp_dir': temp_dir
        }
        
        # Add request_id to the response
        response_data = improved_brief.copy() if improved_brief else {}
        response_data['request_id'] = request_id
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "Campaign Description": "Error occurred during processing",
            "Campaign Goals": "Error occurred during processing",
            "Important Note": "Please check your input and try again"
        }), 500

@app.route('/download-pdf/<request_id>', methods=['GET'])
def download_pdf(request_id):
    try:
        # Get stored brief data
        brief_data = app.config.get(f'brief_{request_id}')
        if not brief_data:
            return jsonify({"error": "Brief not found. Please generate it first."}), 404
        
        try:
            # First attempt to generate PDF with our primary method
            pdf_path = generate_pdf(
                brief_data['campaign_info'], 
                brief_data['brief'],
                brief_data['image_path']
            )
            
            # If primary method fails, try alternative method
            if not pdf_path:
                # Prepare template data
                template_data = {
                    'campaign_info': brief_data['campaign_info'],
                    'brief': {
                        'campaign_description': brief_data['brief'].get('Campaign Description', ''),
                        'campaign_goals': brief_data['brief'].get('Campaign Goals', ''),
                        'important_note': brief_data['brief'].get('Important Note', '')
                    },
                    'generation_date': datetime.datetime.now().strftime('%B %d, %Y'),
                    'current_year': datetime.datetime.now().year,
                    'has_image': False,  # Skip image in fallback method
                    'image_path': ''
                }
                
                # Render the HTML template
                template = jinja2.Template(PDF_TEMPLATE)
                html_content = template.render(**template_data)
                
                # Try alternative PDF generation method
                pdf_path = generate_pdf_from_html(html_content)
        except Exception as inner_e:
            print(f"Primary PDF generation failed: {str(inner_e)}")
            # Final fallback: generate a simple PDF without images
            camp_desc = brief_data['brief'].get('Campaign Description', '').replace('\n', '<br>')
            camp_goals = brief_data['brief'].get('Campaign Goals', '').replace('\n', '<br>')
            imp_notes = brief_data['brief'].get('Important Note', '').replace('\n', '<br>')
            
            simple_html = f"""
            <html>
            <body>
                <h1>{brief_data['campaign_info'].get('campaign_name', 'Product Brief')}</h1>
                <h2>Campaign Description</h2>
                <p>{camp_desc}</p>
                <h2>Campaign Goals</h2>
                <p>{camp_goals}</p>
                <h2>Important Notes</h2>
                <p>{imp_notes}</p>
            </body>
            </html>
            """
            pdf_path = generate_pdf_from_html(simple_html)
        
        if not pdf_path:
            return jsonify({"error": "Failed to generate PDF after multiple attempts"}), 500
            
        # Send PDF file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name="product_brief.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": f"Error generating PDF: {str(e)}"}), 500

if __name__ == "__main__":
    # Get API key from environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set")
    else:
        configure_genai(api_key)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))