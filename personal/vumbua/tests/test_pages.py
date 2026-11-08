def test_home_has_program_story_and_enquiry_cta(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Turn data" in response.data
    assert b"SQL gets the data." in response.data
    assert b"Python shapes it." in response.data
    assert b"Power BI makes it clear." in response.data
    assert b"industry-experienced analytics professionals" in response.data
    assert b"Live, cohort-based classes meet three times a week" in response.data
    assert b"Next cohort starts in December." in response.data
    assert b"Enquire about the next cohort" in response.data
    assert b"mailto:info@vumbua.co.ke" in response.data
    assert b"tel:+254135831159" in response.data
    assert b"https://wa.me/254135831159" in response.data


def test_contact_page_has_direct_contact_options(client):
    response = client.get("/contact")

    assert response.status_code == 200
    assert b"info@vumbua.co.ke" in response.data
    assert b"+254 135 831 159" in response.data
    assert b"Chat with Vumbua" in response.data


def test_program_covers_four_months_and_price(client):
    response = client.get("/program")

    assert response.status_code == 200
    for phrase in (b"SQL for Data Analytics", b"Python for Data Analytics", b"Power BI", b"Real-World Analytics Project"):
        assert phrase in response.data
    assert b"Live, cohort-based classes meet three times a week" in response.data
    assert b"assignments give you practice between sessions" in response.data
    assert b"Next cohort starts in December." in response.data
    assert b"KES 20,000" in response.data
    assert b"KES 80,000" in response.data
    assert b"Program Investment" in response.data


def test_custom_not_found_page(client):
    response = client.get("/not-a-page")

    assert response.status_code == 404
    assert b"This page isn" in response.data


def test_search_discovery_files_list_public_pages(client):
    robots = client.get("/robots.txt")
    sitemap = client.get("/sitemap.xml")

    assert robots.status_code == 200
    assert b"https://vumbua.co.ke/sitemap.xml" in robots.data
    assert b"https://vumbua.co.ke/program" in sitemap.data
    assert b"https://vumbua.co.ke/market-insights" in sitemap.data


def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
