# Haze Couture Body Measurement API

A REST API that estimates key body measurements from 1–4 uploaded photos.
Built with FastAPI and MediaPipe for Haze Couture's SIWES Intern Challenge.

---

## What It Does

Upload 1–4 full-body photos of a person and receive estimated measurements:
```json
{
    "height_cm": 170.0,
    "shoulder_width_cm": 38.2,
    "chest_cm": 40.1,
    "waist_cm": 32.5,
    "hip_cm": 36.0
}
```

---

## Project Structure
```
haze-body-api/
├── app/
│   ├── __init__.py         
│   ├── main.py             # FastAPI entry point — API routes live here
│   ├── engine.py           # AI logic — MediaPipe pose estimation
│   ├── utils.py            # Image preparation and multi-image averaging
│   └── models/             # Auto-downloaded MediaPipe model weights
├── data/
│   └── samples/            # Sample images for testing
├── docs/
│   └── write_up.pdf        # Technical write-up (Deliverable 5)
├── tests/
│   └── test_api.py         # Basic API tests
├── conftest.py             # Pytest path configuration
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/dpam17/HAZE-BODY-API.git
cd haze-body-api
```

### 2. Create and Activate a Virtual Environment
```bash
# Create the virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the API Locally
```bash
uvicorn app.main:app --reload
```

The API will be live at:
```
http://127.0.0.1:8000
```

> **Note:** On first run, the MediaPipe pose landmarker model will be downloaded
> automatically to `app/models/`. This requires an internet connection and
> happens only once.

---

## How to Use the API

### Option 1 — Local Test UI (Easiest)
While uvicorn is running, open `test_ui.html` directly in your browser.
Upload a photo and see results instantly — no terminal needed.

### Option 2 — Browser (Swagger UI)
FastAPI comes with a built-in testing interface. Once running, visit:
```
http://127.0.0.1:8000/docs
```

### Option 3 — curl (Terminal)

**Windows PowerShell:**
```bash
# Single image
curl.exe -X POST "http://127.0.0.1:8000/measure" -F "images=@data/samples/your_photo.jpg"

# Multiple images
curl.exe -X POST "http://127.0.0.1:8000/measure" -F "images=@data/samples/photo1.jpg" -F "images=@data/samples/photo2.jpg"
```

**Mac/Linux:**
```bash
# Single image
curl -X POST "http://127.0.0.1:8000/measure" -F "images=@data/samples/your_photo.jpg"

# Multiple images
curl -X POST "http://127.0.0.1:8000/measure" \
  -F "images=@data/samples/photo1.jpg" \
  -F "images=@data/samples/photo2.jpg"
```

### Option 4 — Live Deployed Demo
Test the API without installing anything:
```
[YOUR DEPLOYED URL HERE]
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Health check — confirms API is running |
| POST | `/measure` | Upload 1–4 images, returns body measurements |

### Parameters for `/measure`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | File(s) | Yes | — | 1–4 full body photos (JPEG, PNG, WEBP) |
| `real_height_cm` | Float | No | 170.0 | Person's actual height for better accuracy |

---

## How It Works

1. Uploaded images are decoded from raw bytes into RGB format
2. Google's MediaPipe Pose Landmarker model detects 33 body landmarks
3. Pixel distances between key landmarks are calculated using the Pythagorean theorem
4. A scale factor (cm per pixel) is derived from the person's pixel height vs assumed real height
5. All measurements are converted from pixels to centimeters using that scale factor
6. If multiple images are uploaded, measurements are averaged across all valid results

---

## CPU-Only Design

This API is designed to run entirely on CPU — no GPU required:

- Uses **MediaPipe Lite** model — optimized for fast CPU inference
- Uses **opencv-python-headless** — no display or graphics hardware dependencies
- All post-landmark calculations are pure arithmetic

---

## Tips for Best Results

- Stand **straight** and **face the camera directly**
- Ensure your **full body is visible** — head to toe
- Use a **plain background** where possible
- Good **lighting** improves landmark detection significantly
- Uploading **2–4 photos** produces more reliable averaged results

---

## Known Limitations

- Chest and waist measurements are approximations —
  MediaPipe does not provide direct landmarks for these points
- Accuracy depends on how close the person's height is to the assumed 170cm default
- Side profile or angled photos will reduce accuracy
- Works best with front-facing full body images
- Close-up or partial body photos will return unreliable measurements

---

## Running Tests
```bash
pip install pytest httpx
pytest tests/test_api.py -v
```

Expected output:
```
tests/test_api.py::test_root_endpoint            PASSED
tests/test_api.py::test_measure_no_images        PASSED
tests/test_api.py::test_measure_wrong_file_type  PASSED
tests/test_api.py::test_measure_too_many_images  PASSED
tests/test_api.py::test_measure_with_real_image  PASSED
```

---

## AI Tools Used

| Tool | Purpose |
|------|---------|
| Claude (Anthropic) | Code generation, architecture guidance, debugging, explanations |
| MediaPipe (Google) | Pretrained pose landmark detection model |

---

## What I'd Improve With More Time

- Allow users to input their real height for a more accurate scale factor
- Add a landmark confidence check that rejects unusable images with a clear warning
- Add side-profile image support for better chest and waist estimation
- Implement actual video frame extraction and measurement averaging across frames
- Replace chest and waist multiplier approximations with anatomically grounded estimation

---

Built by PAM DAVID WENG — Haze Couture Intern Challenge Submission