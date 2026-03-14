# main.py
# This is the entry point of our API — the front door of the whole system.
# It does three things:
# 1. Creates the FastAPI application
# 2. Defines the API endpoints (the URLs people can send requests to)
# 3. Receives uploaded files and passes them to utils.py and engine.py for processing
# Think of it like a receptionist — it receives requests,
# directs them to the right place, and sends back the response

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from app.utils import process_multiple_images, load_and_prepare_image
from app.engine import estimate_measurements

# --- Create the FastAPI app ---
# This one line creates our entire API application
# Everything else we write attaches to this object
app = FastAPI(
    title="Haze Couture Body Measurement API",
    description="Upload 1-4 photos to get estimated body measurements",
    version="1.0.0"
)

# --- CORS Middleware ---
# CORS = Cross Origin Resource Sharing
# This allows the API to be accessed from browsers and external tools
# Without this, browsers would block requests to our API for security reasons
# allow_origins=["*"] means: accept requests from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Root Endpoint ---
# Returns a beautiful branded HTML page anyone can use to test the API
# No terminal, no curl, no installation needed
# URL: GET /
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Haze Couture — Body Measurement API</title>
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }

            body {
                font-family: 'DM Mono', monospace;
                background: #080808;
                color: #fff;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
                position: relative;
                overflow-x: hidden;
            }

            body::before {
                content: '';
                position: fixed;
                top: -200px; left: -200px; right: -200px; bottom: -200px;
                background: radial-gradient(ellipse 60% 40% at 50% 20%, rgba(255,255,255,0.03) 0%, transparent 70%);
                pointer-events: none;
                z-index: 0;
            }

            .haze-card {
                width: 100%;
                max-width: 480px;
                position: relative;
                z-index: 1;
            }

            /* --- Header --- */
            .haze-header {
                text-align: center;
                margin-bottom: 48px;
            }

            .haze-wordmark {
                font-family: 'Cormorant Garamond', serif;
                font-weight: 300;
                font-size: 42px;
                letter-spacing: 14px;
                color: #fff;
                text-transform: uppercase;
                line-height: 1;
                margin-bottom: 8px;
            }

            .haze-sub {
                font-size: 9px;
                letter-spacing: 4px;
                color: #444;
                text-transform: uppercase;
            }

            .haze-divider {
                width: 40px;
                height: 1px;
                background: #222;
                margin: 20px auto;
            }

            /* --- Upload Zone --- */
            .upload-zone {
                border: 1px solid #1e1e1e;
                border-radius: 2px;
                padding: 36px 24px;
                text-align: center;
                cursor: pointer;
                transition: border-color 0.3s ease, background 0.3s ease;
                position: relative;
                background: #0d0d0d;
                margin-bottom: 16px;
            }

            .upload-zone:hover { border-color: #333; background: #111; }
            .upload-zone.dragover { border-color: #555; background: #141414; }

            .upload-icon {
                width: 32px;
                height: 32px;
                margin: 0 auto 12px;
                opacity: 0.2;
            }

            .upload-label {
                font-size: 10px;
                letter-spacing: 3px;
                color: #444;
                text-transform: uppercase;
                display: block;
                margin-bottom: 6px;
            }

            .upload-hint {
                font-family: 'Cormorant Garamond', serif;
                font-style: italic;
                font-size: 14px;
                color: #2a2a2a;
            }

            .file-input {
                position: absolute;
                inset: 0;
                opacity: 0;
                cursor: pointer;
                width: 100%;
                height: 100%;
            }

            /* --- Files Selected --- */
            .files-selected {
                font-size: 10px;
                letter-spacing: 2px;
                color: #666;
                text-transform: uppercase;
                text-align: center;
                margin-bottom: 16px;
                min-height: 16px;
            }

            /* --- Height Row --- */
            .height-row {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 28px;
                padding: 0 2px;
            }

            .height-label {
                font-size: 9px;
                letter-spacing: 3px;
                color: #333;
                text-transform: uppercase;
                white-space: nowrap;
                flex-shrink: 0;
            }

            .height-input {
                flex: 1;
                background: transparent;
                border: none;
                border-bottom: 1px solid #1e1e1e;
                color: #888;
                font-family: 'DM Mono', monospace;
                font-size: 13px;
                padding: 6px 0;
                outline: none;
                transition: border-color 0.3s;
                text-align: right;
            }

            .height-input:focus { border-bottom-color: #444; color: #ccc; }

            .height-unit {
                font-size: 9px;
                letter-spacing: 2px;
                color: #333;
                flex-shrink: 0;
            }

            /* --- Submit Button --- */
            .submit-btn {
                width: 100%;
                padding: 16px;
                background: transparent;
                border: 1px solid #1e1e1e;
                color: #888;
                font-family: 'DM Mono', monospace;
                font-size: 10px;
                letter-spacing: 5px;
                text-transform: uppercase;
                cursor: pointer;
                transition: all 0.3s ease;
                border-radius: 2px;
            }

            .submit-btn:hover:not(:disabled) {
                border-color: #444;
                color: #ccc;
                background: #0d0d0d;
            }

            .submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }

            /* --- Results --- */
            .results-wrap {
                margin-top: 36px;
                display: none;
            }

            .results-wrap.visible {
                display: block;
                animation: fadeUp 0.5s ease forwards;
            }

            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .results-label {
                font-size: 9px;
                letter-spacing: 4px;
                color: #333;
                text-transform: uppercase;
                margin-bottom: 20px;
                text-align: center;
            }

            .measurements-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1px;
                background: #111;
                border: 1px solid #111;
                border-radius: 2px;
                overflow: hidden;
                margin-bottom: 1px;
            }

            .measurement-cell {
                background: #0d0d0d;
                padding: 20px 16px;
                text-align: center;
            }

            .measurement-cell.full { grid-column: 1 / -1; }

            .m-value {
                font-family: 'Cormorant Garamond', serif;
                font-weight: 300;
                font-size: 32px;
                color: #ccc;
                line-height: 1;
                margin-bottom: 6px;
            }

            .m-unit {
                font-family: 'Cormorant Garamond', serif;
                font-style: italic;
                font-size: 13px;
                color: #333;
            }

            .m-label {
                font-size: 8px;
                letter-spacing: 2.5px;
                color: #2a2a2a;
                text-transform: uppercase;
                margin-top: 4px;
            }

            /* --- Error --- */
            .error-box {
                background: #0d0d0d;
                border: 1px solid #1e1e1e;
                border-radius: 2px;
                padding: 20px;
                text-align: center;
            }

            .error-text {
                font-family: 'Cormorant Garamond', serif;
                font-style: italic;
                font-size: 15px;
                color: #444;
            }

            /* --- Footer --- */
            .haze-footer {
                margin-top: 40px;
                text-align: center;
            }

            .footer-text {
                font-size: 8px;
                letter-spacing: 3px;
                color: #1e1e1e;
                text-transform: uppercase;
            }

            /* --- Processing Dots --- */
            .processing-dots span {
                animation: blink 1.4s infinite both;
            }
            .processing-dots span:nth-child(2) { animation-delay: 0.2s; }
            .processing-dots span:nth-child(3) { animation-delay: 0.4s; }

            @keyframes blink {
                0%, 80%, 100% { opacity: 0; }
                40% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="haze-card">

            <div class="haze-header">
                <div class="haze-wordmark">Haze</div>
                <div class="haze-sub">Body Measurement API</div>
                <div class="haze-divider"></div>
            </div>

            <div class="upload-zone" id="uploadZone">
                <input type="file" class="file-input" id="fileInput" accept="image/*" multiple>
                <svg class="upload-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="20" width="24" height="8" rx="1" stroke="#fff" stroke-width="1"/>
                    <path d="M16 4 L16 18 M10 10 L16 4 L22 10" stroke="#fff" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="upload-label">Upload Photos</span>
                <span class="upload-hint">1–4 full body images</span>
            </div>

            <div class="files-selected" id="filesSelected"></div>

            <div class="height-row">
                <span class="height-label">Height</span>
                <input type="number" class="height-input" id="heightInput" value="170" min="100" max="250">
                <span class="height-unit">cm</span>
            </div>

            <button class="submit-btn" id="submitBtn" onclick="submitMeasurements()">
                Measure
            </button>

            <div class="results-wrap" id="resultsWrap">
                <div class="results-label">Measurements</div>
                <div id="resultsContent"></div>
            </div>

            <div class="haze-footer">
                <div class="footer-text">Couture x AI — 2026</div>
            </div>

        </div>

        <script>
            const fileInput = document.getElementById('fileInput');
            const filesSelected = document.getElementById('filesSelected');
            const uploadZone = document.getElementById('uploadZone');

            // Update file count display when files are selected
            fileInput.addEventListener('change', () => {
                const count = fileInput.files.length;
                filesSelected.textContent = count === 0 ? ''
                    : count === 1 ? '01 image selected'
                    : '0' + count + ' images selected';
            });

            // Drag and drop support
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });

            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('dragover');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                fileInput.files = e.dataTransfer.files;
                const count = fileInput.files.length;
                filesSelected.textContent = count === 1
                    ? '01 image selected'
                    : '0' + count + ' images selected';
            });

            async function submitMeasurements() {
                const files = fileInput.files;
                const height = document.getElementById('heightInput').value;
                const resultsWrap = document.getElementById('resultsWrap');
                const resultsContent = document.getElementById('resultsContent');
                const btn = document.getElementById('submitBtn');

                if (files.length === 0) {
                    showError('Please select at least one image.');
                    return;
                }

                // Disable button and show processing state
                btn.disabled = true;
                btn.innerHTML = '<span class="processing-dots"><span>.</span><span>.</span><span>.</span></span>';
                resultsWrap.classList.remove('visible');

                // Build form data to send to /measure
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('images', files[i]);
                }
                formData.append('real_height_cm', height);

                try {
                    const response = await fetch('/measure', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (response.ok) {
                        showResults(data);
                    } else {
                        showError(data.detail || 'Something went wrong.');
                    }

                } catch (err) {
                    showError('Could not reach the API. Please try again.');
                }

                btn.disabled = false;
                btn.textContent = 'Measure';
            }

            function showResults(data) {
                const resultsWrap = document.getElementById('resultsWrap');
                const resultsContent = document.getElementById('resultsContent');

                const labels = {
                    height_cm: 'Height',
                    shoulder_width_cm: 'Shoulder',
                    chest_cm: 'Chest',
                    waist_cm: 'Waist',
                    hip_cm: 'Hip'
                };

                const entries = Object.entries(data);
                let html = '<div class="measurements-grid">';

                entries.forEach(([key, value], i) => {
                    const isLast = i === entries.length - 1;
                    const isOdd = entries.length % 2 !== 0;
                    const fullClass = isLast && isOdd ? ' full' : '';
                    html += '<div class="measurement-cell' + fullClass + '">'
                        + '<div class="m-value">' + parseFloat(value).toFixed(1)
                        + '<span class="m-unit"> cm</span></div>'
                        + '<div class="m-label">' + (labels[key] || key) + '</div>'
                        + '</div>';
                });

                html += '</div>';
                resultsContent.innerHTML = html;
                resultsWrap.classList.add('visible');
            }

            function showError(msg) {
                const resultsWrap = document.getElementById('resultsWrap');
                const resultsContent = document.getElementById('resultsContent');
                resultsContent.innerHTML = '<div class="error-box"><p class="error-text">' + msg + '</p></div>';
                resultsWrap.classList.add('visible');
            }
        </script>
    </body>
    </html>
    """


# --- Main Measurement Endpoint ---
# This is the core of the API — where the actual work happens
# URL: POST /measure
# It accepts 1 to 4 uploaded image files
# It returns the estimated body measurements as JSON
@app.post("/measure")
async def measure_body(
    # File(...) means: this field is required — the API will reject requests without it
    # List[UploadFile] means: accept a list of uploaded files (1 to 4 images)
    images: List[UploadFile] = File(...),

    # Optional real height input — if provided, measurements will be more accurate
    real_height_cm: Optional[float] = Form(170.0)
):
    # --- Validation: Check number of images ---
    # We only accept between 1 and 4 images
    if len(images) < 1 or len(images) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please upload between 1 and 4 images"
        )

    # --- Validation: Check file types ---
    # We only accept image files — not PDFs, videos, or anything else
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    for image in images:
        if image.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"{image.filename} is not a supported image type. Use JPEG, PNG, or WEBP."
            )

    # --- Single Image Path ---
    # If only one image is uploaded, process it directly
    if len(images) == 1:
        file_bytes = await images[0].read()
        image_rgb, image_width, image_height = load_and_prepare_image(file_bytes)

        if image_rgb is None:
            raise HTTPException(
                status_code=400,
                detail="Could not read the uploaded image. Please try a different file."
            )

        result = estimate_measurements(image_rgb, image_width, image_height, real_height_cm)

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        return result

    # --- Multiple Images Path ---
    # If 2-4 images are uploaded, average results across all of them
    else:
        result = process_multiple_images(images, real_height_cm)

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        return result