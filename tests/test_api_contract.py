from http import HTTPStatus

def test_health(client):
    r = client.get('/health')
    assert r.status_code == HTTPStatus.OK
    assert r.json()['status'] == 'ok'

def test_recommend_kw_happy_path(client):
    body = {'query':'quick vegan pasta with tomatoes','diet':'vegan','k':5,'model':'kw'}
    r = client.post('/recommend', json=body)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert 'results' in data and isinstance(data['results'], list)
    assert data['used_model'].startswith('kw')

def test_recommend_bad_diet(client):
    body = {'query':'x','diet':'pizza','k':5,'model':'kw'}
    r = client.post('/recommend', json=body)
    assert r.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY)

def test_recommend_large_k_rejected(client):
    body = {'query':'peruvian','diet':'none','k':999,'model':'kw'}
    r = client.post('/recommend', json=body)
    assert r.status_code in (HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.BAD_REQUEST)
