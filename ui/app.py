import os, time
import httpx
import streamlit as st

API = os.getenv('API_URL', 'http://127.0.0.1:8000')

st.set_page_config(page_title='AI Recipe Recommender', page_icon='🥑', layout='centered')
st.title('🥑 AI Recipe Recommender')
st.caption('Personalized recipe recommendations based on ingredients & diets')

with st.sidebar:
    st.header('Settings')
    api_url = st.text_input('API URL', API)
    api_url = api_url.rstrip('/')  # avoid //recommend
    model = st.selectbox('Model', ['kw', 'tfidf'], index=0, help='kw = keyword baseline; tfidf = cosine similarity')
    k = st.slider('Top-K', 1, 10, 5)
    diet = st.selectbox('Diet', ['none', 'keto', 'vegan', 'vegetarian', 'gluten_free'], index=0)
    must = st.text_input('Must-include ingredients (comma-separated)', '')

    if st.button('Check API'):
        url = f'{api_url}/health'
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url)
            st.success(f'GET {url} → {r.status_code} {r.text[:120]}')
        except Exception as e:
            st.error(f'Health check failed: {e}')

q = st.text_input('Your query (EN or ES)', 'quick vegan pasta with tomatoes')
run = st.button('Search')


def call_api():
    'Return (url, payload, httpx.Response, client_latency_ms)'
    payload = {
        'query': q.strip(),
        'diet': diet,
        'must_include': [m.strip() for m in must.split(',') if m.strip()],
        'k': k,
        'language': 'auto',
        'model': model,
    }
    url = f'{api_url}/recommend'
    t0 = time.perf_counter()
    with httpx.Client(timeout=8.0) as client:
        resp = client.post(url, json=payload)
    dt_ms = int((time.perf_counter() - t0) * 1000)
    return url, payload, resp, dt_ms   # <-- MUST return the Response object


if run:
    if not q.strip():
        st.warning('Type a query first.')
    else:
        try:
            url, payload, r, dt_ms = call_api()

            if not hasattr(r, 'status_code'):
                st.error(f'Internal UI bug: expected httpx.Response, got {type(r).__name__}')
                st.text(str(r)[:200])
                st.stop()

            st.info(f'POST {url} → {r.status_code}')

            with st.expander('Debug request', expanded=False):
                st.code(f'POST {url}\n\nPayload:\n{payload}', language='bash')
                st.write('Status:', r.status_code)
                st.text(r.text[:800])

            if r.status_code == 200:
                data = r.json()
                st.success(
                    f'{len(data["results"])} results • '
                    f'server {data["latency_ms"]} ms • client {dt_ms} ms • '
                    f'model {data["used_model"]}'
                )
                for i, rec in enumerate(data['results'], start=1):
                    with st.container(border=True):
                        st.markdown(f'**{i}. {rec["title"]}**  \nScore: `{rec["score"]:.3f}`')
                        if rec.get('url'):
                            st.write(rec['url'])
                        if rec.get('reasons'):
                            st.caption(' • '.join(rec['reasons']))
            else:
                st.error(f'Error {r.status_code}: {r.text[:160]}')

        except Exception as e:
            st.error(f'API request failed: {e}')
            st.caption('Is the API URL correct and running?')
