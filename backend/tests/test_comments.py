def test_add_and_list_comments(client, sample_ticket):
    ticket = client.post("/api/tickets", json=sample_ticket).json()

    first = client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "ravi.k", "body": "Tried a hard reset, no change."},
    )
    assert first.status_code == 201
    assert first.json()["ticket_id"] == ticket["id"]

    client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "asha.menon", "body": "Thanks, still black screen."},
    )

    comments = client.get(f"/api/tickets/{ticket['id']}/comments").json()
    assert [c["author"] for c in comments] == ["ravi.k", "asha.menon"]

    assert client.get(f"/api/tickets/{ticket['id']}").json()["comment_count"] == 2
    listed = client.get("/api/tickets").json()
    assert listed[0]["comment_count"] == 2


def test_comment_on_missing_ticket_returns_404(client):
    response = client.post("/api/tickets/404/comments", json={"author": "x", "body": "hello"})
    assert response.status_code == 404


def test_comment_requires_body(client, sample_ticket):
    ticket = client.post("/api/tickets", json=sample_ticket).json()
    response = client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "x", "body": ""})
    assert response.status_code == 422


def test_deleting_ticket_removes_comments(client, sample_ticket):
    ticket = client.post("/api/tickets", json=sample_ticket).json()
    client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "x", "body": "note"})
    client.delete(f"/api/tickets/{ticket['id']}")
    assert client.get(f"/api/tickets/{ticket['id']}/comments").status_code == 404
