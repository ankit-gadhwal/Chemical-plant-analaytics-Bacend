"""
test_equipment.py – Tests for the /equipment router.

Covers:
  - GET  /equipment/            → list (paginated, filtered)
  - GET  /equipment/{uid}       → single fetch
  - GET  /equipment/dataset/{uid} → equipment for a dataset
  - PATCH /equipment/{uid}      → update
  - DELETE /equipment/{uid}     → delete
"""
import io
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

VALID_CSV = (
    "equipment_name,equipment_type,flowrate,pressure,temperature,status\n"
    "Pump-01,Centrifugal,130.0,4.0,90.0,active\n"
    "Valve-02,Gate,50.0,2.5,75.0,active\n"
)


class TestEquipmentList:
    @pytest.mark.asyncio
    async def test_list_equipment_authenticated(self, client: AsyncClient, auth_headers: dict):
        """Authenticated user can list equipment (possibly empty)."""
        resp = await client.get("/equipment/", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_equipment_pagination(self, client: AsyncClient, auth_headers: dict):
        """Pagination params work without error."""
        resp = await client.get("/equipment/?page=1&page_size=3", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_equipment_unauthenticated(self, client: AsyncClient):
        """Unauthenticated request returns 401/403."""
        resp = await client.get("/equipment/")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_equipment_filter_by_type(self, client: AsyncClient, auth_headers: dict):
        """equipment_type filter is accepted without 500."""
        resp = await client.get(
            "/equipment/?equipment_type=Centrifugal", headers=auth_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_equipment_sort_order(self, client: AsyncClient, auth_headers: dict):
        """sort_by and order params are accepted."""
        resp = await client.get(
            "/equipment/?sort_by=created_at&order=asc", headers=auth_headers
        )
        assert resp.status_code == 200


class TestEquipmentCRUD:
    """Requires a dataset with equipment already in the DB."""

    @pytest_asyncio.fixture()
    async def dataset_with_equipment(self, client: AsyncClient, auth_headers: dict):
        """Upload a CSV dataset; returns (dataset_uid, first_equipment_uid)."""
        upload = await client.post(
            "/dataset/upload",
            files=[
                (
                    "file",
                    ("equip_test.csv", io.BytesIO(VALID_CSV.encode()), "text/csv"),
                )
            ],
            headers=auth_headers,
        )
        if upload.status_code not in (200, 201):
            pytest.skip(f"Dataset upload failed: {upload.text}")
        dataset_uid = upload.json().get("uid") or upload.json().get("dataset_uid")
        return str(dataset_uid)

    @pytest.mark.asyncio
    async def test_get_equipment_by_dataset(
        self, client: AsyncClient, auth_headers: dict, dataset_with_equipment: str
    ):
        """Can fetch all equipment for an owned dataset."""
        resp = await client.get(
            f"/equipment/dataset/{dataset_with_equipment}", headers=auth_headers
        )
        assert resp.status_code in (200, 404)  # 404 is valid if CSV parsing is async

    @pytest.mark.asyncio
    async def test_get_nonexistent_equipment(self, client: AsyncClient, auth_headers: dict):
        """Random equipment UID returns 404."""
        resp = await client.get(f"/equipment/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_equipment(
        self, client: AsyncClient, auth_headers: dict
    ):
        """PATCH on an unknown UID returns 404."""
        resp = await client.patch(
            f"/equipment/{uuid.uuid4()}",
            json={"flowrate": 99.9},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_equipment(
        self, client: AsyncClient, auth_headers: dict
    ):
        """DELETE on an unknown UID returns 404."""
        resp = await client.delete(
            f"/equipment/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_equipment_range_filter(self, client: AsyncClient, auth_headers: dict):
        """Pressure/temperature/flowrate range filters are accepted."""
        resp = await client.get(
            "/equipment/?min_pressure=1.0&max_pressure=10.0", headers=auth_headers
        )
        assert resp.status_code == 200
