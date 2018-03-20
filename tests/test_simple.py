from time import sleep

from sample_app.simple import app


def test_throttling_simple_app():
    request, response = app.test_client.get('/write')
    assert response.status == 200
    request, response = app.test_client.get('/write')
    assert response.status == 429
    sleep(1)
    request, response = app.test_client.get('/')
    assert response.status == 200
    request, response = app.test_client.get('/')
    assert response.status == 429
    sleep(2)
    request, response = app.test_client.get('/')
    assert response.status == 200

