from context_sieve.text import estimate_tokens, fingerprint_similarity, normalize, simhash


def test_normalize_collapses_case_unicode_and_whitespace() -> None:
    assert normalize("  \uff28ello\nWORLD  ") == "hello world"


def test_token_estimate_counts_words_and_punctuation() -> None:
    assert estimate_tokens("Hello, world!") == 4


def test_simhash_is_stable() -> None:
    text = "retrieval augmented generation needs clean context chunks"
    assert simhash(text) == simhash(text)


def test_similar_text_has_higher_score_than_unrelated_text() -> None:
    base = simhash("the model retrieves relevant passages before generating an answer")
    similar = simhash("the model retrieves relevant documents before generating an answer")
    unrelated = simhash("database migrations require ordered reversible schema changes")
    assert fingerprint_similarity(base, similar) > fingerprint_similarity(base, unrelated)
