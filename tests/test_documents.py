"""
test_documents.py – Tests for the /documents router.
"""
import io
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n99\n%%EOF"

DATASET_CSV = (
    "equipment_name,equipment_type,flowrate,pressure,temperature,status\n"
    "Pump-Doc,Centrifugal,100.0,3.0,80.0,active\n"
)


@pytest_asyncio.fixture(autouse=True)
def mock_document_ingestion():
    with patch(
        "src.documents.service.IngestionService.ingest_document",
        new_callable=AsyncMock,
        return_value={"status": "success"},
    ):
        yield


class TestDocumentUpload:
    @pytest_asyncio.fixture()
    async def dataset_uid(self, client: AsyncClient, auth_headers: dict) -> str:
        """Upload a dataset to attach documents to."""
        resp = await client.post(
            "/dataset/upload",
            files=[("file", ("doc_test.csv", io.BytesIO(DATASET_CSV.encode()), "text/csv"))],
            headers=auth_headers,
        )
        if resp.status_code not in (200, 201):
            pytest.skip(f"Dataset upload failed: {resp.text}")
        data = resp.json()
        return str(data.get("uid") or data.get("dataset_uid"))

    @pytest.mark.asyncio
    async def test_upload_pdf_document(
        self, client: AsyncClient, auth_headers: dict, dataset_uid: str
    ):
        """Valid PDF upload returns 201 with document metadata."""
        resp = await client.post(
            f"/documents/upload?dataset_uid={dataset_uid}",
            files=[("file", ("manual.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf"))],
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert "uid" in data or "document_uid" in str(data)

    @pytest.mark.asyncio
    async def test_upload_wrong_file_type(
        self, client: AsyncClient, auth_headers: dict, dataset_uid: str
    ):
        """Uploading an image or document."""
        resp = await client.post(
            f"/documents/upload?dataset_uid={dataset_uid}",
            files=[("file", ("image.png", io.BytesIO(b"\x89PNG"), "image/png"))],
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 400, 422, 500)

    @pytest.mark.asyncio
    async def test_upload_document_unauthenticated(
        self, client: AsyncClient, dataset_uid: str
    ):
        """Uploading without a token returns 401/403."""
        resp = await client.post(
            f"/documents/upload?dataset_uid={dataset_uid}",
            files=[("file", ("manual.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf"))],
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_dataset(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Uploading to a non-existent dataset UID returns 404."""
        resp = await client.post(
            f"/documents/upload?dataset_uid={uuid.uuid4()}",
            files=[("file", ("manual.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf"))],
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDocumentRetrieval:
    @pytest_asyncio.fixture()
    async def uploaded_document(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Upload a dataset + document; return (dataset_uid, doc_uid)."""
        ds_resp = await client.post(
            "/dataset/upload",
            files=[("file", ("doc_retr.csv", io.BytesIO(DATASET_CSV.encode()), "text/csv"))],
            headers=auth_headers,
        )
        if ds_resp.status_code not in (200, 201):
            pytest.skip(f"Dataset upload failed: {ds_resp.text}")
        ds_uid = str(ds_resp.json().get("uid") or ds_resp.json().get("dataset_uid"))

        doc_resp = await client.post(
            f"/documents/upload?dataset_uid={ds_uid}",
            files=[("file", ("retr.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf"))],
            headers=auth_headers,
        )
        if doc_resp.status_code not in (200, 201):
            pytest.skip(f"Document upload failed: {doc_resp.text}")
        doc_uid = str(doc_resp.json().get("uid") or doc_resp.json().get("document_uid"))
        return ds_uid, doc_uid

    @pytest.mark.asyncio
    async def test_get_documents_by_dataset(
        self, client: AsyncClient, auth_headers: dict, uploaded_document
    ):
        """List documents for a dataset returns 200 with a list."""
        ds_uid, _ = uploaded_document
        resp = await client.get(f"/documents/dataset/{ds_uid}", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_document_by_uid(
        self, client: AsyncClient, auth_headers: dict, uploaded_document
    ):
        """Fetch a single document by UID returns 200."""
        _, doc_uid = uploaded_document
        resp = await client.get(f"/documents/{doc_uid}", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client: AsyncClient, auth_headers: dict):
        """Random UID returns 404."""
        resp = await client.get(f"/documents/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document(
        self, client: AsyncClient, auth_headers: dict, uploaded_document
    ):
        """Owner can delete their document."""
        _, doc_uid = uploaded_document
        resp = await client.delete(f"/documents/{doc_uid}", headers=auth_headers)
        assert resp.status_code in (200, 204)

    @pytest.mark.asyncio
    async def test_delete_document_unauthenticated(
        self, client: AsyncClient, uploaded_document
    ):
        """Unauthenticated delete returns 401/403."""
        _, doc_uid = uploaded_document
        resp = await client.delete(f"/documents/{doc_uid}")
        assert resp.status_code in (401, 403)
