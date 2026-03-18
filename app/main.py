from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from app.utils import process_multiple_images, load_and_prepare_image
from app.engine import estimate_measurements

app = FastAPI(
    title="BodyMetrics API",
    description="REST API for anatomical measurement extraction from images.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def root():
    """Returns the branded web interface for the API."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>BodyMetrics API</title>
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
            }
            .haze-card { width: 100%; max-width: 480px; }
            .haze-header { text-align: center; margin-bottom: 48px; }
            .haze-wordmark {
                font-family: 'Cormorant Garamond', serif;
                font-weight: 300;
                font-size: 42px;
                letter-spacing: 14px;
                text-transform: uppercase;
            }
            .upload-zone {
                border: 1px solid #1e1e1e;
                padding: 36px 24px;
                text-align: center;
                cursor: pointer;
                background: #0d0d0d;
                margin-bottom: 16px;
            }
            .submit-btn {
                width: 100%;
                padding: 16px;
                background: transparent;
                border: 1px solid #1e1e1e;
                color: #888;
                letter-spacing: 5px;
                text-transform: uppercase;
                cursor: pointer;
            }
            .results-wrap { margin-top: 36px; display: none; }
            .results-wrap.visible { display: block; }
            .measurements-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #111; }
            .measurement-cell { background: #0d0d0d; padding: 20px 16px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="haze-card">
            <div class="haze-header">
                <div class="haze-wordmark">BodyMetrics</div>
                <div style="font-size: 9px; letter-spacing: 4px; color: #444; text-transform: uppercase;">Extraction Engine</div>
            </div>
            <div class="upload-zone" id="uploadZone">
                <input type="file" style="position:absolute; opacity:0; inset:0;" id="fileInput" accept="image/*" multiple>
                <span style="font-size: 10px; letter-spacing: 3px; color: #444; text-transform: uppercase;">Upload Photos</span>
            </div>
            <div id="filesSelected" style="font-size: 10px; text-align: center; margin-bottom: 16px; color: #666;"></div>
            <button class="submit-btn" id="submitBtn" onclick="submitMeasurements()">Measure</button>
            <div class="results-wrap" id="resultsWrap"><div id="resultsContent"></div></div>
        </div>
        <script>
            const fileInput = document.getElementById('fileInput');
            fileInput.addEventListener('change', () => {
                const count = fileInput.files.length;
                document.getElementById('filesSelected').textContent = count + ' image(s) selected';
            });
            async function submitMeasurements() {
                const formData = new FormData();
                for (let f of fileInput.files) formData.append('images', f);
                formData.append('real_height_cm', 170);
                const res = await fetch('/measure', { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) showResults(data);
            }
            function showResults(data) {
                let html = '<div class="measurements-grid">';
                for (let [k, v] of Object.entries(data)) {
                    html += `<div class="measurement-cell"><div style="font-size: 24px;">${v}</div><div style="font-size: 8px;">${k}</div></div>`;
                }
                document.getElementById('resultsContent').innerHTML = html + '</div>';
                document.getElementById('resultsWrap').classList.add('visible');
            }
        </script>
    </body>
    </html>
    """

@app.post("/measure")
async def measure_body(
    images: List[UploadFile] = File(...),
    real_height_cm: Optional[float] = Form(170.0)
):
    """Primary endpoint for measurement processing."""
    if not (1 <= len(images) <= 4):
        raise HTTPException(status_code=400, detail="Upload 1-4 images.")

    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    for img in images:
        if img.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

    if len(images) == 1:
        file_bytes = await images[0].read()
        image_rgb, w, h = load_and_prepare_image(file_bytes)
        
        if image_rgb is None:
            raise HTTPException(status_code=400, detail="Invalid image file.")

        result = estimate_measurements(image_rgb, w, h, real_height_cm)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        return result

    result = await process_multiple_images(images, real_height_cm)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result