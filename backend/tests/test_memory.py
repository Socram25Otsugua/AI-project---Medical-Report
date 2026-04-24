from app.memory import InMemorySessionStore


def test_session_store_append_get_and_clear():
    store = InMemorySessionStore()

    store.append("s1", "user", "hello")
    store.append("s1", "assistant", "world")

    turns = store.get("s1")
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[0].content == "hello"
    assert turns[1].role == "assistant"
    assert turns[1].content == "world"

    store.clear("s1")
    assert store.get("s1") == []


def test_session_store_get_returns_copy():
    store = InMemorySessionStore()
    store.append("s1", "user", "immutable")

    turns = store.get("s1")
    turns.append("mutation-attempt")

    assert len(store.get("s1")) == 1
