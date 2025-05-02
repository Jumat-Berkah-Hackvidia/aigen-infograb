# --- START OF MODIFIED api.py ---

import base64
import json
import tempfile
import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory, url_for # Added send_from_directory, url_for, request
from flask_cors import CORS
import google.generativeai as genai
import PyPDF2
from PIL import Image
from io import BytesIO
import jinja2
import pdfkit
import uuid
import os
import hashlib
import shutil # Added for cleanup in finally blocks

app = Flask(__name__)
CORS(app) # Allow all origins for simplicity in testing

# --- Configuration ---
USER_IMAGE_STORAGE_DIR = "user_images" # Directory to store user images persistently
# Ensure the user image storage directory exists
os.makedirs(USER_IMAGE_STORAGE_DIR, exist_ok=True)

# Configure Gemini API
def configure_genai(api_key):
    genai.configure(api_key=api_key)

# --- Helper Functions ---

def get_user_image_path(email):
    """Generates a safe path for storing a user's image based on their email."""
    if not email:
        return None
    email_hash = hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()
    return os.path.join(USER_IMAGE_STORAGE_DIR, f"{email_hash}.jpg")

# --- Static File Serving Route ---
@app.route('/user-images/<path:filename>')
def serve_user_image(filename):
    """Serves images stored for users."""
    # Security: Ensure filename is safe, send_from_directory helps prevent path traversal
    print(f"Attempting to serve image: {filename} from {USER_IMAGE_STORAGE_DIR}")
    try:
        # Using absolute path for send_from_directory is generally more robust
        abs_image_dir = os.path.abspath(USER_IMAGE_STORAGE_DIR)
        return send_from_directory(abs_image_dir, filename)
    except FileNotFoundError:
        print(f"Image not found: {filename}")
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Error serving image"}), 500

# --- PDF Generation and Processing ---

def generate_pdf_from_html(html_content):
    """Generate a PDF directly from HTML content"""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, f'product_brief_{uuid.uuid4()}.pdf')
        options = {'encoding': 'UTF-8', 'enable-local-file-access': None, 'quiet': ''} # Use quiet=''
        pdfkit.from_string(html_content, pdf_path, options=options)
        return pdf_path, temp_dir
    except Exception as e:
        print(f"Error in direct HTML to PDF conversion: {str(e)}")
        # Clean up temp dir if created and error occurs
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None, None

def process_pdf(pdf_file_stream):
    pdf_text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file_stream)
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() or "" # Append empty string if None
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None
    return pdf_text

def process_image(image_bytes):
    """Processes image bytes using Gemini"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        image_parts = [{"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode('utf-8')}]
        prompt = "Describe this product image in detail, focusing on key visual features, design elements, style, colors, and any visible text relevant to a product brief."
        # Ensure content is passed correctly for multimodal models
        response = model.generate_content([prompt, image_parts[0]])
        return response.text
    except Exception as e:
        print(f"Error processing image with Gemini: {str(e)}")
        return None

def generate_product_brief(campaign_info, pdf_content=None, image_description=None):
    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepare prompt parts
    prompt_parts = [
        "Please analyze the following campaign information and generate an improved product brief.",
        "\n\nCAMPAIGN INFORMATION:",
        json.dumps(campaign_info, indent=2)
    ]
    if image_description:
        prompt_parts.extend(["\n\nIMAGE DESCRIPTION (from uploaded/associated image):", image_description])
    if pdf_content:
        prompt_parts.extend(['\n\nADDITIONAL CONTEXT FROM PDF:', pdf_content])
    prompt_parts.extend([
        "\n\nBased on ALL the information provided above, please provide:",
        "1. An improved Campaign Description: Make it engaging, concise, and highlight the product's key benefits and unique selling points.",
        "2. Clear Campaign Goals: Define specific, measurable, achievable, relevant, and time-bound (SMART) goals aligned with the product and campaign description.",
        "3. Important Notes: List crucial considerations, potential challenges, or key takeaways for campaign execution.",
        "\nFormat your response strictly as a JSON object with these exact keys: \"Campaign Description\", \"Campaign Goals\", \"Important Note\". The value for each key should be a single string, potentially containing markdown for formatting (like bullet points using '*' or '-'). Do not include ```json markers or any other text outside the JSON object."
    ])
    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        # Basic cleanup attempt for potential markdown fences
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip() # Strip again after potential fence removal

        # Attempt to parse the JSON response
        result = json.loads(response_text)
        required_keys = ["Campaign Description", "Campaign Goals", "Important Note"]
        validated_result = {}
        for key in required_keys:
            validated_result[key] = result.get(key, f"AI Error: No content generated for '{key}'.") # Provide clearer default
        return validated_result

    except json.JSONDecodeError as json_e:
        print(f"Error parsing JSON response from model: {json_e}")
        print(f"Model Raw Response:\n{response.text}")
        # Try to extract sections manually as a fallback (less reliable)
        desc = goals = notes = f"Error parsing AI response. Raw: {response.text}"
        # Basic string splitting attempt 
        try:
            parts = response.text.split('\n\n') # Example split
            # Find parts based on keywords (very basic)
            for part in parts:
                if "Campaign Description" in part: desc = part.split(":",1)[-1].strip()
                if "Campaign Goals" in part: goals = part.split(":",1)[-1].strip()
                if "Important Note" in part: notes = part.split(":",1)[-1].strip()
        except: pass # Ignore errors during fallback parsing
        return {
            "Campaign Description": desc,
            "Campaign Goals": goals,
            "Important Note": notes + f" (JSON Parsing Error: {json_e})"
        }
    except Exception as e:
        print(f"Error generating/processing content with Gemini: {str(e)}")
        return {
            "Campaign Description": "Error communicating with or processing response from AI model.",
            "Campaign Goals": "Error communicating with or processing response from AI model.",
            "Important Note": f"Generation/Processing Error: {str(e)}"
        }


# PDF Template 
PDF_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ campaign_info.campaign_name }} - Product Brief</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #2563EB; padding-bottom: 20px; }
        .logo { font-size: 24px; font-weight: bold; color: #1E3A8A; }
        .campaign-title { font-size: 28px; font-weight: bold; margin: 10px 0; color: #1E3A8A; }
        .meta-info { display: flex; justify-content: space-between; flex-wrap: wrap; margin: 20px 0; background-color: #F3F4F6; padding: 15px; border-radius: 8px; }
        .meta-item { margin-bottom: 10px; flex-basis: 48%; }
        .meta-label { font-weight: bold; color: #6B7280; }
        .section { margin-bottom: 30px; padding: 20px; background-color: #F8FAFC; border-radius: 8px; border-left: 5px solid #2563EB; }
        .section-title { font-size: 20px; font-weight: bold; color: #2563EB; margin-top: 0; margin-bottom: 15px; }
        .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #6B7280; border-top: 1px solid #E5E7EB; padding-top: 20px; }
        .image-container { text-align: center; margin: 20px 0; }
        img { max-width: 80%; max-height: 400px; height: auto; border-radius: 8px; border: 1px solid #ccc; }
        .brief-content div { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="header"> <div class="logo">Product Brief Generator</div> <h1 class="campaign-title">{{ campaign_info.campaign_name }}</h1> <p>Generated on {{ generation_date }}</p> </div>
    <div class="meta-info"> <div class="meta-item"> <div class="meta-label">Product Name:</div> <div>{{ campaign_info.product_name }}</div> </div> <div class="meta-item"> <div class="meta-label">Category:</div> <div>{{ campaign_info.category }}</div> </div> <div class="meta-item"> <div class="meta-label">Price Range:</div> <div>{{ campaign_info.price_range }}</div> </div> <div class="meta-item"> <div class="meta-label">Campaign Period:</div> <div>{{ campaign_info.campaign_period }}</div> </div> </div>
    {% if has_image and image_data_uri %} <div class="image-container"> <img src="{{ image_data_uri }}" alt="Product Image"> </div> {% endif %}
    <div class="section brief-content"> <h2 class="section-title">Campaign Description</h2> <div>{{ brief.campaign_description }}</div> </div>
    <div class="section brief-content"> <h2 class="section-title">Campaign Goals</h2> <div>{{ brief.campaign_goals }}</div> </div>
    <div class="section brief-content"> <h2 class="section-title">Important Notes</h2> <div>{{ brief.important_note }}</div> </div>
    <div class="footer"> <p>Generated using AiDorse Product Brief Generator</p> <p>© {{ current_year }} AiDorse</p> </div>
</body>
</html>
"""

def generate_pdf(campaign_info, brief, image_path=None):
    """Generate a PDF file for the product brief using a Jinja template"""
    temp_dir = None
    pdf_path = None
    try:
        temp_dir = tempfile.mkdtemp()
        image_data_uri = None
        has_image = False
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as img_file:
                    image_binary = img_file.read()
                    image_base64 = base64.b64encode(image_binary).decode('utf-8')
                    _, ext = os.path.splitext(image_path)
                    image_type = ext.lower().lstrip('.')
                    if image_type not in ['jpeg', 'jpg', 'png', 'gif']: image_type = 'jpeg'
                    elif image_type == 'jpg': image_type = 'jpeg'
                    image_data_uri = f"data:image/{image_type};base64,{image_base64}"
                    has_image = True
            except Exception as img_e:
                print(f"Error processing image file {image_path} for PDF: {img_e}")
                has_image = False

        template_data = {
            'campaign_info': campaign_info,
            'brief': {
                'campaign_description': brief.get('Campaign Description', ''),
                'campaign_goals': brief.get('Campaign Goals', ''),
                'important_note': brief.get('Important Note', '')
            },
            'generation_date': datetime.datetime.now().strftime('%B %d, %Y'),
            'current_year': datetime.datetime.now().year,
            'has_image': has_image,
            'image_data_uri': image_data_uri if has_image else None
        }
        template = jinja2.Template(PDF_TEMPLATE)
        html_content = template.render(**template_data)
        html_path = os.path.join(temp_dir, 'product_brief.html')
        pdf_path = os.path.join(temp_dir, 'product_brief.pdf')
        with open(html_path, 'w', encoding='utf-8') as f: f.write(html_content)
        pdfkit_options = {
            'encoding': 'UTF-8', 'enable-local-file-access': None, 'quiet': '',
            'margin-top': '20mm', 'margin-right': '20mm', 'margin-bottom': '20mm', 'margin-left': '20mm',
            'page-size': 'A4',
        }
        pdfkit.from_file(html_path, pdf_path, options=pdfkit_options)
        return pdf_path, temp_dir
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None, None # Return None for path and dir on error

# --- Flask Routes ---

@app.route('/generate-brief', methods=['POST'])
def create_product_brief():
    request_id = str(uuid.uuid4())
    final_image_path_for_pdf = None # Path to the image file on server
    image_url_for_response = None # Publicly accessible URL for the image

    try:
        # --- 1. Extract Form Data ---
        email = request.form.get('email')
        if not email:
            return jsonify({"error": "Email address is required."}), 400

        campaign_info = {
            "email": email,
            "campaign_name": request.form.get('campaign_name', 'Untitled Campaign'),
            "product_name": request.form.get('product_name', 'N/A'),
            "category": request.form.get('category', 'N/A'),
            "price_range": request.form.get('price_range', 'N/A'),
            "campaign_period": request.form.get('campaign_period', 'N/A'),
            "current_description": request.form.get('current_description', ''),
            "current_goals": request.form.get('current_goals', ''),
            "current_notes": request.form.get('current_notes', '')
        }

        # --- 2. Process PDF (if provided) ---
        pdf_content = None
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename != '':
                print(f"Processing PDF file: {pdf_file.filename}")
                pdf_content = process_pdf(pdf_file.stream)
                if pdf_content is None:
                    print("Failed to process PDF content.")
                    # Optionally return error or just proceed without PDF

        # --- 3. Handle Image ---
        image_description = None
        image_bytes_for_gemini = None
        user_image_path = get_user_image_path(email) # Potential persistent path

        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file and image_file.filename != '':
                print(f"Processing newly uploaded image: {image_file.filename}")
                try:
                    img_bytes = image_file.read()
                    image = Image.open(BytesIO(img_bytes))
                    if image.mode in ('RGBA', 'P'): image = image.convert('RGB')
                    image.save(user_image_path, format='JPEG', quality=85) # Save/overwrite
                    print(f"Saved new image for {email} to {user_image_path}")
                    # Read back saved bytes for Gemini
                    with open(user_image_path, "rb") as f_saved: image_bytes_for_gemini = f_saved.read()
                    final_image_path_for_pdf = user_image_path # Set path for PDF
                except Exception as img_e:
                    print(f"Error processing/saving uploaded image: {img_e}")
                    # Proceed without image if saving fails

        elif user_image_path and os.path.exists(user_image_path):
            print(f"Using existing image for {email} from {user_image_path}")
            try:
                with open(user_image_path, "rb") as f_existing: image_bytes_for_gemini = f_existing.read()
                final_image_path_for_pdf = user_image_path # Use existing path for PDF
            except Exception as img_read_e:
                print(f"Error reading existing image {user_image_path}: {img_read_e}")
                image_bytes_for_gemini = None
                final_image_path_for_pdf = None

        # If we have an image path (new or existing), generate its public URL
        if final_image_path_for_pdf:
            try:
                image_filename = os.path.basename(final_image_path_for_pdf)
                # Construct the URL using request.host_url and the static route
                # request.host_url includes scheme, host, port (e.g., http://127.0.0.1:8080/)
                image_url_for_response = f"{request.host_url.rstrip('/')}{url_for('serve_user_image', filename=image_filename)}"
                print(f"Generated image URL: {image_url_for_response}")
            except Exception as url_e:
                print(f"Error generating image URL: {url_e}")
                # Proceed without URL if generation fails

        # Process image with Gemini if bytes available
        if image_bytes_for_gemini:
            print("Sending image to Gemini for description...")
            image_description = process_image(image_bytes_for_gemini)
            if image_description: print("Received image description from Gemini.")
            else: print("Failed to get image description from Gemini.")

        # --- 4. Generate Improved Brief using Gemini ---
        print("Generating improved product brief with Gemini...")
        improved_brief = generate_product_brief(campaign_info, pdf_content, image_description)

        # --- 5. Store Data for PDF Download ---
        app.config[f'brief_{request_id}'] = {
            'campaign_info': campaign_info,
            'brief': improved_brief,
            'image_path_for_pdf': final_image_path_for_pdf,
        }

        # --- 6. Prepare and Return JSON Response ---
        response_data = improved_brief.copy()
        response_data['request_id'] = request_id
        response_data['image_url'] = image_url_for_response # *** ADDED IMAGE URL ***
        print(f"Brief generation complete for request_id: {request_id}")
        return jsonify(response_data)

    except Exception as e:
        print(f"Unhandled error in /generate-brief: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "An unexpected server error occurred.",
            "details": str(e),
            "Campaign Description": "Error during processing.",
            "Campaign Goals": "Error during processing.",
            "Important Note": "Please check server logs."
        }), 500


@app.route('/download-pdf/<request_id>', methods=['GET'])
def download_pdf_route(request_id):
    pdf_temp_dir = None
    pdf_path = None
    try:
        brief_data_key = f'brief_{request_id}'
        brief_data = app.config.get(brief_data_key)
        if not brief_data:
            print(f"Brief data not found for request_id: {request_id}")
            return jsonify({"error": "Brief data not found or expired. Please generate it again."}), 404

        print(f"Generating PDF for request_id: {request_id}")
        pdf_path, pdf_temp_dir = generate_pdf(
            brief_data['campaign_info'],
            brief_data['brief'],
            brief_data.get('image_path_for_pdf')
        )

        if not pdf_path:
            print(f"Failed to generate PDF for request_id: {request_id}. Trying fallback.")
            try:
                # Simplified fallback generation
                camp_desc = brief_data['brief'].get('Campaign Description', 'N/A').replace('\n', '<br>')
                camp_goals = brief_data['brief'].get('Campaign Goals', 'N/A').replace('\n', '<br>')
                imp_notes = brief_data['brief'].get('Important Note', 'N/A').replace('\n', '<br>')
                campaign_name = brief_data['campaign_info'].get('campaign_name', 'Product Brief')
                simple_html = f"<!DOCTYPE html><html><head><title>{campaign_name}</title><meta charset='UTF-8'></head><body><h1>{campaign_name}</h1><h2>Campaign Description</h2><p>{camp_desc}</p><h2>Campaign Goals</h2><p>{camp_goals}</p><h2>Important Notes</h2><p>{imp_notes}</p><hr><p><small>Generated by Product Brief Generator (Fallback)</small></p></body></html>"
                pdf_path, pdf_temp_dir = generate_pdf_from_html(simple_html)
                if not pdf_path:
                    print(f"Fallback PDF generation also failed for request_id: {request_id}")
                    return jsonify({"error": "Failed to generate PDF even with fallback."}), 500
            except Exception as fallback_e:
                print(f"Error during fallback PDF generation for {request_id}: {fallback_e}")
                # Clean up temp dir if created during failed fallback
                if pdf_temp_dir and os.path.exists(pdf_temp_dir): shutil.rmtree(pdf_temp_dir, ignore_errors=True)
                return jsonify({"error": "Failed to generate PDF due to an internal error during fallback."}), 500

        # Send PDF file
        print(f"Sending PDF file: {pdf_path}")
        # Ensure the file exists before sending
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file path does not exist after generation: {pdf_path}")
            return jsonify({"error": "Internal error: Generated PDF file not found."}), 500

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name="product_brief.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error in /download-pdf/{request_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An error occurred while preparing the PDF download: {str(e)}"}), 500

    finally:
        # Cleanup temporary PDF directory and remove config entry
        if pdf_temp_dir and os.path.exists(pdf_temp_dir):
            try:
                shutil.rmtree(pdf_temp_dir)
                print(f"Cleaned up temporary PDF directory: {pdf_temp_dir}")
            except Exception as cleanup_e:
                print(f"Error cleaning up temporary directory {pdf_temp_dir}: {cleanup_e}")
        if brief_data_key in app.config:
            try:
                del app.config[brief_data_key]
                print(f"Removed brief data from config for request_id: {request_id}")
            except KeyError: pass


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. AI features will likely fail.")
    else:
        try:
            configure_genai(api_key)
            print("Gemini API configured successfully.")
        except Exception as config_e:
            print(f"Error configuring Gemini API: {config_e}")

    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask server on host 0.0.0.0 port {port}")
    print(f"Serving user images from: {os.path.abspath(USER_IMAGE_STORAGE_DIR)}")
    print(f"Access user images via: http://<your_ip>:{port}/user-images/<hashed_email>.jpg")
    app.run(debug=True, host='0.0.0.0', port=port)