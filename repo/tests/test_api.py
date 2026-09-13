import pytest
from httpx import AsyncClient, ASGITransport
from src.app.main import app
import io
from PIL import Image

def create_dummy_image_bytes():
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "SignalScope" in res.text

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert len(data["capabilities"]) > 0

@pytest.mark.asyncio
async def test_analyze_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_dummy_image_bytes()
        files = {"file": ("test.png", img_bytes, "image/png")}
        res = await ac.post("/api/v1/analyze", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "prediction" in data
        assert "calibrated_confidence" in data
        assert "gradcam_heatmap" in data
        assert "generator_attribution" in data
        assert "explanation" in data

@pytest.mark.asyncio
async def test_analyze_batch_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_dummy_image_bytes()
        files = [
            ("files", ("test1.png", img_bytes, "image/png")),
            ("files", ("test2.png", img_bytes, "image/png"))
        ]
        res = await ac.post("/api/v1/analyze-batch", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["total_analyzed"] == 2

@pytest.mark.asyncio
async def test_metadata_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_dummy_image_bytes()
        files = {"file": ("test.png", img_bytes, "image/png")}
        res = await ac.post("/api/v1/inspect-metadata", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "has_exif" in data
        assert "provenance_verdict" in data

@pytest.mark.asyncio
async def test_robustness_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_dummy_image_bytes()
        files = {"file": ("test.png", img_bytes, "image/png")}
        res = await ac.post("/api/v1/test-robustness", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "robustness_score" in data
        assert len(data["perturbation_results"]) == 3

@pytest.mark.asyncio
async def test_multimodal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_dummy_image_bytes()
        files = {"file": ("test.png", img_bytes, "image/png")}
        data_payload = {"caption": "Authentic photograph of a ceramic mug"}
        res = await ac.post("/api/v1/analyze-multimodal", files=files, data=data_payload)
        assert res.status_code == 200
        res_json = res.json()
        assert "text_image_consistency_score" in res_json

@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "unseen_generator_roc_auc" in data
        assert "confusion_matrix" in data
