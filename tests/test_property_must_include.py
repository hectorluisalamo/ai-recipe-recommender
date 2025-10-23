from hypothesis import given, strategies as st
from app.ranker.baselines import recommend_keyword

@given(
    query=st.sampled_from(['peruvian spicy chicken', 'vegan pasta tomatoes', 'gluten free tacos']),
    must=st.sampled_from([['chicken'], ['tomato'], ['onion'], []]),
)
def test_must_include_keeps_matching_items(query, must):
    base = recommend_keyword(query, diet='none', must_include=[], k=5)
    with_filter = recommend_keyword(query, diet='none', must_include=must, k=5)
    
    base_ids = {
        r['id'] for r in base if all(
            (m in r['title'].lower()) or 
            any(m in reason.lower() for reason in r.get('reasons', []))
            for m in must
        )
    }
    filt_ids = {r['id'] for r in with_filter}
    assert base_ids.issubset(filt_ids)