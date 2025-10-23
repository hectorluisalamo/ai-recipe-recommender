from app.ranker.baselines import _tokenize

def test_tokenize_basic():
    assert _tokenize('Vegan pasta, rápido!') == ['vegan','pasta','rápido']
    
def test_tokenize_numbers_and_accents():
    assert _tokenize('Aji-amarillo 2x') == ['aji','amarillo','2x']
