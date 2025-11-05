from pipeline.normalizer import normalize

def test_normalize_minimal():
    raw = {"timestamp":"t","source":"s","event_type":"e","payload":{"ip":"1.2.3.4"}}
    out = normalize(raw)
    assert out['ip'] == '1.2.3.4'
    assert out['type'] == 'e'
