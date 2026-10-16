def test_create_ticket_returns_201_with_defaults(client, sample_ticket):
    response = client.post("/api/tickets", json=sample_ticket)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["subject"] == sample_ticket["subject"]
    assert body["status"] == "OPEN"
    assert body["assignee"] is None
    assert body["comment_count"] == 0
    assert body["resolved_at"] is None


def test_create_ticket_rejects_invalid_payload(client):
    response = client.post("/api/tickets", json={"subject": "x", "requester": ""})
    assert response.status_code == 422


def test_create_ticket_rejects_unknown_priority(client, sample_ticket):
    response = client.post("/api/tickets", json={**sample_ticket, "priority": "WHENEVER"})
    assert response.status_code == 422


def test_list_tickets_newest_first(client, sample_ticket):
    client.post("/api/tickets", json=sample_ticket)
    client.post("/api/tickets", json={**sample_ticket, "subject": "VPN keeps disconnecting"})
    response = client.get("/api/tickets")
    assert response.status_code == 200
    subjects = [t["subject"] for t in response.json()]
    assert subjects == ["VPN keeps disconnecting", "Laptop will not boot"]


def test_list_tickets_filters_by_status_and_priority(client, sample_ticket):
    client.post("/api/tickets", json=sample_ticket)  # HIGH / OPEN
    created = client.post("/api/tickets", json={**sample_ticket, "priority": "LOW"}).json()
    client.put(f"/api/tickets/{created['id']}", json={"status": "RESOLVED"})

    assert len(client.get("/api/tickets", params={"status": "OPEN"}).json()) == 1
    assert len(client.get("/api/tickets", params={"priority": "LOW"}).json()) == 1
    assert len(client.get("/api/tickets", params={"status": "CLOSED"}).json()) == 0


def test_list_tickets_search_by_subject(client, sample_ticket):
    client.post("/api/tickets", json=sample_ticket)
    client.post("/api/tickets", json={**sample_ticket, "subject": "Printer out of toner"})
    results = client.get("/api/tickets", params={"q": "printer"}).json()
    assert [t["subject"] for t in results] == ["Printer out of toner"]


def test_get_ticket_by_id(client, sample_ticket):
    created = client.post("/api/tickets", json=sample_ticket).json()
    response = client.get(f"/api/tickets/{created['id']}")
    assert response.status_code == 200
    assert response.json()["requester"] == sample_ticket["requester"]


def test_get_missing_ticket_returns_404(client):
    response = client.get("/api/tickets/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_ticket_assigns_and_sets_resolved_at(client, sample_ticket):
    created = client.post("/api/tickets", json=sample_ticket).json()
    response = client.put(
        f"/api/tickets/{created['id']}",
        json={"assignee": "ravi.k", "status": "IN_PROGRESS"},
    )
    assert response.status_code == 200
    assert response.json()["assignee"] == "ravi.k"
    assert response.json()["resolved_at"] is None

    resolved = client.put(f"/api/tickets/{created['id']}", json={"status": "RESOLVED"}).json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_at"] is not None

    reopened = client.put(f"/api/tickets/{created['id']}", json={"status": "OPEN"}).json()
    assert reopened["resolved_at"] is None


def test_update_with_empty_body_is_rejected(client, sample_ticket):
    created = client.post("/api/tickets", json=sample_ticket).json()
    response = client.put(f"/api/tickets/{created['id']}", json={})
    assert response.status_code == 422


def test_delete_ticket(client, sample_ticket):
    created = client.post("/api/tickets", json=sample_ticket).json()
    assert client.delete(f"/api/tickets/{created['id']}").status_code == 204
    assert client.get(f"/api/tickets/{created['id']}").status_code == 404
    assert client.delete(f"/api/tickets/{created['id']}").status_code == 404


def test_stats_aggregates_by_status_and_category(client, sample_ticket):
    client.post("/api/tickets", json=sample_ticket)
    client.post("/api/tickets", json={**sample_ticket, "priority": "URGENT", "category": "NETWORK"})
    third = client.post("/api/tickets", json={**sample_ticket, "assignee": "ravi.k"}).json()
    client.put(f"/api/tickets/{third['id']}", json={"status": "CLOSED"})

    stats = client.get("/api/tickets/stats").json()
    assert stats["total"] == 3
    assert stats["open"] == 2
    assert stats["closed"] == 1
    assert stats["urgent_open"] == 1
    assert stats["unassigned"] == 2
    assert stats["by_category"] == {"HARDWARE": 2, "NETWORK": 1}
