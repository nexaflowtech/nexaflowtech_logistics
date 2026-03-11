# Download Label via Postman (Delhivery)

## Two-step flow

### Step 1: Get PDF download link

**Request:**
```
GET https://track.delhivery.com/api/p/packing_slip?wbns=<AWB>&pdf=true&pdf_size=4R
```

**Headers:**
```
Authorization: Token <your_api_token>
Content-Type: application/json
```

**Example:**
```
GET https://track.delhivery.com/api/p/packing_slip?wbns=29898510049862&pdf=true&pdf_size=4R
Authorization: Token 9dd3c4d999716e90e212e4d23b409bb7a4da94e0
Content-Type: application/json
```

**Response:** JSON with `pdf_download_link`:
```json
{
  "packages": [{
    "pdf_download_link": "https://express-hq-prod.s3.ap-south-1.amazonaws.com/packing-slip/29898510049862.pdf?X-Amz-Algorithm=..."
  }]
}
```

### Step 2: Download the PDF

Copy the `pdf_download_link` URL from the response and open it in a new request or in your browser:

**Request:**
```
GET <pdf_download_link>
```

No auth headers needed – the URL is a pre-signed S3 link valid for 24 hours.

**Example:**
```
GET https://express-hq-prod.s3.ap-south-1.amazonaws.com/packing-slip/29898510049862.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&...
```

The response is the PDF file. In Postman, use "Send and Download" to save it.
