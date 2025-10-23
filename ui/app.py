import os, time
import httpx
import streamlit as st
from urllib.parse import urlparse

DEFAULT_API = os.getenv('API_URL', 'http://127.0.0.1:8000')

st.set_page_config(page_title='AI Recipe Recommender', page_icon='🥑', layout='centered')
st.title('🥑 AI Recipe Recommender')
st.caption('Personalized recipe recommendations based on ingredients & diets')

def normalize_base(url_text: str) -> str:
    raw = (url_text or '').strip()
    if not raw:
        return DEFAULT_API
    parsed = urlparse(raw)
    if not parsed.scheme:
        raw = 'http://' + raw
        parsed = urlparse(raw)
    return (parsed.scheme + '://' + parsed.netloc + (parsed.path or '')).rstrip('/')

with st.sidebar:
    st.header('Settings')
    api_url_in = st.text_input('API URL', DEFAULT_API)
    api_base = api_url_in.rstrip('/')
    
    model = st.selectbox('Model', ['kw', 'tfidf'], index=0, help='kw = keyword baseline; tfidf = cosine similarity')
    k = st.slider('Top-K', 1, 10, 5)
    
    diet_labels = {
        'none': 'none',
        'keto': 'keto',
        'vegan': 'vegan',
        'vegetarian': 'vegetarian',
        'gluten_free': 'gluten_free',
    }
    diet_label = st.selectbox('Diet', list(diet_labels.keys()), index=0)
    diet_value = diet_labels[diet_label]
    
    must = st.text_input('Must-include ingredients (comma-separated)', '')
    
col1, col2 = st.columns([1, 3])
with col1:
    if st.button('Check API'):
        url = f'{api_base}/health'
        try:
            r = httpx.get(url, timeout=3.0)
            st.success('GET {url} → {r.status_code} {r.text[:100]}')
        except Exception as e:
            st.error(f'Health check failed for {url!r}: {e!r}')
    
q = st.text_input('Your query (EN or ES)', 'quick vegan pasta with tomatoes')
run = st.button('Search')

def call_api():
    payload = {
        'query': q.strip(),
        'diet': diet_value,
        'must_include': [m.strip() for m in must.split(',') if m.strip()],
        'k': k,
        'model': model,
        'language': 'auto',
    }
    url = f'{api_base}/recommend'
    t0 = time.perf_counter()
    with httpx.Client(timeout=5.0) as client:
        r = client.post(f'{url}/recommend', json=payload)
    dt_ms = int((time.perf_counter() - t0) * 1000)
    return r, dt_ms, payload

if run:
    if not q.strip():
        st.warning('Please enter a query.')
    else:
        try:
            r, dt_ms, payload = call_api()
            if r.status_code == 200:
                data = r.json()
                st.success(f"{len(data['results'])} results • server {data['latency_ms']} ms • client {dt_ms} ms • model {data['used_model']}")
                for i, rec in enumerate(data['results'], start=1):
                    with st.container(border=True):
                        st.markdown(f"**{i}. {rec['title']}** \nScore: `{rec['score']:.3f}`")
                        if rec.get('url'):
                            st.write(rec['url'])
                        if rec.get('reasons'):
                            st.caption(" • ".join(rec["reasons"]))
            else:
                try:
                    err = r.json()
                except Exception:
                    err = {'details': r.text}
                st.error(f'Error {r.status_code}: {err}')
        except Exception as e:
            st.error(f'Request failed: {e}')
            st.caption('is the API running at the URL provided?')
            