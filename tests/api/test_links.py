def create_sample_link(client, url="https://example.com/a"):
    response = client.post("/links", json={"original_url": url})
    assert response.status_code == 200
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_link(client):
    created = create_sample_link(client, "https://example.com/very/long/url")
    link_id = created["id"]

    response = client.get(f"/links/{link_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == "https://example.com/very/long/url"
    assert "short_code" in data


def test_update_link(client):
    created = create_sample_link(client, "https://old.example.com")
    link_id = created["id"]

    response = client.put(
        f"/links/{link_id}",
        json={"original_url": "https://new.example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == "https://new.example.com/"


def test_delete_link(client):
    created = create_sample_link(client, "https://delete-me.example.com")
    link_id = created["id"]

    response = client.delete(f"/links/{link_id}")
    assert response.status_code == 204

    response = client.get(f"/links/{link_id}")
    assert response.status_code == 404


def test_redirect_by_code(client):
    created = create_sample_link(client, "https://python.org")
    code = created["short_code"]

    response = client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://python.org/"