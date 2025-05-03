# AiDorse Product Brief Generator API Documentation

This documentation provides details on how to integrate with the AiDorse Product Brief Generator API.

## Base URL

When running: `https://hackvidia.riqgarden.pp.ua`

## Endpoints

### 1. Generate Brief

Generates an AI-enhanced product brief based on the provided information.

**Endpoint:** `/generate-brief`  
**Method:** `POST`  
**Content-Type:** `multipart/form-data`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | String | Yes | User's email address |
| campaign_name | String | No | Name of the campaign |
| product_name | String | No | Name of the product |
| platform | String | No | Platform for the campaign (e.g., Instagram, Facebook) |
| category | String | No | Product category |
| price_range | String | No | Price range of the product |
| campaign_period | String | No | Duration of the campaign |
| current_description | String | No | Current campaign description if available |
| current_goals | String | No | Current campaign goals if available |
| current_notes | String | No | Current additional notes if available |
| pdf_file | File | No | Additional context document in PDF format |
| product_image | File | No | Product image (JPEG, PNG, GIF) |

#### Response

**Success Response (200 OK)**

```json
{
  "Campaign Description": "Detailed AI-enhanced campaign description...",
  "Campaign Goals": "Clear campaign goals with bullet points...",
  "Important Note": "Important considerations for the campaign...",
  "request_id": "unique-identifier-for-pdf-download",
  "image_url": "http://example.com/user-images/hashed-email.jpg"
}
```

**Error Response (400 Bad Request)**

```json
{
  "error": "Email address is required."
}
```

**Error Response (500 Internal Server Error)**

```json
{
  "error": "An unexpected server error occurred.",
  "details": "Error details...",
  "Campaign Description": "Error during processing.",
  "Campaign Goals": "Error during processing.",
  "Important Note": "Please check server logs."
}
```

### 2. Download PDF

Downloads the generated product brief as a PDF file.

**Endpoint:** `/download-pdf/{request_id}`  
**Method:** `GET`

#### Path Parameters

| Parameter | Description |
|-----------|-------------|
| request_id | The unique identifier returned from a successful generate-brief call |

#### Response

**Success Response**

PDF file with filename `product_brief.pdf`

**Error Response (404 Not Found)**

```json
{
  "error": "Brief data not found or expired. Please generate it again."
}
```

**Error Response (500 Internal Server Error)**

```json
{
  "error": "An error occurred while preparing the PDF download: [error details]"
}
```

### 3. Retrieve User Image

Retrieves a stored user image.

**Endpoint:** `/user-images/{filename}`  
**Method:** `GET`

#### Path Parameters

| Parameter | Description |
|-----------|-------------|
| filename | The filename of the user image (typically a hashed email address with .jpg extension) |

#### Response

**Success Response**
- Image file (JPEG format)

**Error Response (404 Not Found)**

```json
{
  "error": "Image not found"
}
```

## Examples

### Example: Generate Brief Request

```javascript
// Using fetch with FormData
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('campaign_name', 'Summer Collection Launch');
formData.append('product_name', 'EcoFriendly Water Bottle');
formData.append('category', 'Eco-friendly Products');
formData.append('price_range', '$20-30');
formData.append('campaign_period', 'June 1 - August 31, 2024');
formData.append('current_description', 'Launch of our new water bottle.');
formData.append('current_goals', 'Increase sales and awareness.');
formData.append('current_notes', 'Target environmentally conscious consumers.');

// Add PDF if available
if (pdfFileInput.files[0]) {
  formData.append('pdf_file', pdfFileInput.files[0]);
}

// Add image if available
if (imageInput.files[0]) {
  formData.append('product_image', imageInput.files[0]);
}

fetch('https://hackvidia.riqgarden.pp.ua/generate-brief', {
  method: 'POST',
  body: formData,
})
.then(response => response.json())
.then(data => {
  console.log('Success:', data);
  // Store request_id for PDF download
  const requestId = data.request_id;
  // Update UI with returned brief content
  updateBriefContent(data);
  // Save image URL if present
  if (data.image_url) {
    displayProductImage(data.image_url);
  }
})
.catch(error => {
  console.error('Error:', error);
});
```

### Example: Download PDF

```javascript
// Using the request_id from the generate-brief response
function downloadPDF(requestId) {
  window.location.href = `https://hackvidia.riqgarden.pp.ua/download-pdf/${requestId}`;
}
```

## Implementation Notes

1. The API will save and persist user images based on the email address. The same image will be reused for future requests with the same email unless a new image is uploaded.

2. The `request_id` returned from a successful brief generation is temporary and will expire after the PDF is downloaded or after a server restart.

3. The brief generation process may take a few seconds to complete due to AI processing time.

4. For best results, provide clear and detailed information in the form fields, and optionally include relevant images and PDF documents.
