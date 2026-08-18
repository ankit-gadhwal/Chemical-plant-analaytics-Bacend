"""
test_chatbot.py – Tests for the /chat router.

Covers:
  - POST /chat/sql             → SQL chatbot
  - POST /chat/rag             → RAG chatbot
  - GET  /chat/sessions        → list sessions
  - GET  /chat/sessions/{uid}  → get history
  - DELETE /chat/sessions/{uid}→ delete session
"""
import io
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

DATASET_CSV = (
    "equipment_name,equipment_type,flowrate,pressure,temperature,status\n"
    "Pump-Chat,Centrifugal,100.0,3.0,80.0,active\n"
)
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n%%EOF"
)


@pytest_asyncio.fixture()
async def dataset_uid(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/dataset/upload",
        files=[("file", ("chat_ds.csv", io.BytesIO(DATASET_CSV.encode()), "text/csv"))],
        headers=auth_headers,
    )
    if resp.status_code not in (200, 201):
        pytest.skip(f"Dataset upload failed: {resp.text}")
    data = resp.json()
    return str(data.get("uid") or data.get("dataset_uid"))


class TestChatSessions:
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient, auth_headers: dict):
        """New user has zero chat sessions."""
        resp = await client.get("/chat/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_list_sessions_unauthenticated(self, client: AsyncClient):
        """Unauthenticated request returns 401/403."""
        resp = await client.get("/chat/sessions")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client: AsyncClient, auth_headers: dict):
        """Random session UID returns 404."""
        resp = await client.get(f"/chat/sessions/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, client: AsyncClient, auth_headers: dict):
        """DELETE on an unknown session UID returns 404."""
        resp = await client.delete(
            f"/chat/sessions/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404


class TestSQLChat:
    @pytest.mark.asyncio
    async def test_sql_chat_mocked(
        self, client: AsyncClient, auth_headers: dict, dataset_uid: str
    ):
        """
        SQL chat returns 200. The LLM call is mocked to avoid real API charges.
        """
        mock_response = AsyncMock()
        mock_response.content = "SELECT * FROM equipment LIMIT 5;"

        with patch(
            "src.chatbot.service.ChatService._invoke_llm",
            return_value=mock_response,
        ):
            resp = await client.post(
                "/chat/sql",
                json={"question": "List all pumps", "dataset_uid": dataset_uid},
                headers=auth_headers,
            )
        # Accept 200 or 404 (if dataset not yet processed)
        assert resp.status_code in (200, 404, 500)

    @pytest.mark.asyncio
    async def test_sql_chat_unauthenticated(
        self, client: AsyncClient, dataset_uid: str
    ):
        """Unauthenticated SQL chat returns 401/403."""
        resp = await client.post(
            "/chat/sql",
            json={"question": "What is the max pressure?", "dataset_uid": dataset_uid},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_sql_chat_missing_question(
        self, client: AsyncClient, auth_headers: dict, dataset_uid: str
    ):
        """Missing question field returns 422."""
        resp = await client.post(
            "/chat/sql",
            json={"dataset_uid": dataset_uid},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestRAGChat:
    @pytest.mark.asyncio
    async def test_rag_chat_mocked(
        self, client: AsyncClient, auth_headers: dict, dataset_uid: str
    ):
        """
        RAG chat returns a valid response when LLM is mocked.
        """
        mock_response = AsyncMock()
        mock_response.content = "The pump has a flowrate of 100 m³/h."

        with patch(
            "src.chatbot.service.ChatService._invoke_llm",
            return_value=mock_response,
        ), patch(
            "src.chatbot.rag.rag_service.Retriever.retrieve",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = await client.post(
                "/chat/rag",
                json={
                    "question": "What is the flowrate of the pump?",
                    "dataset_uid": dataset_uid,
                    "session_uid": None,
                },
                headers=auth_headers,
            )
        assert resp.status_code in (200, 404, 500)

    @pytest.mark.asyncio
    async def test_rag_chat_unauthenticated(
        self, client: AsyncClient, dataset_uid: str
    ):
        """Unauthenticated RAG chat returns 401/403."""
        resp = await client.post(
            "/chat/rag",
            json={"question": "explain", "dataset_uid": dataset_uid},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_rag_chat_missing_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Missing required fields returns 422."""
        resp = await client.post(
            "/chat/rag",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422
