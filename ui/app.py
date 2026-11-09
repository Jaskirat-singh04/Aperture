"""Streamlit test UI for Aperture.

A thin client over the running API (no business logic here, see
docs/adr/ for why the API, not this UI, owns permissions). Lets you log in
as a seeded demo user via Dex, ingest a document, ask a question, and see
the answer with citations plus a reminder of who can see what.

Run with: uv run --extra ui streamlit run ui/app.py
Needs the docker compose stack up (make up) and the API on :8000.
"""

import os

import httpx
import streamlit as st

API_BASE = os.environ.get("APERTURE_API_BASE", "http://localhost:8000")
DEX_TOKEN_URL = os.environ.get("APERTURE_DEX_TOKEN_URL", "http://localhost:5556/dex/token")
DEX_CLIENT_ID = "aperture-api"
DEX_CLIENT_SECRET = "aperture-local-dev-secret"

# The seeded demo users (see deploy/dex/config.yaml), with a note on what
# each can see, so the permission behavior is easy to exercise by hand.
DEMO_USERS = {
    "alice@acme.test": "alice (tenant acme, group finance)",
    "bob@acme.test": "bob (tenant acme, group engineering)",
    "carol@globex.test": "carol (tenant globex, group finance)",
}
DEMO_PASSWORD = "password"


def get_token(email: str) -> str:
    response = httpx.post(
        DEX_TOKEN_URL,
        auth=(DEX_CLIENT_ID, DEX_CLIENT_SECRET),
        data={
            "grant_type": "password",
            "username": email,
            "password": DEMO_PASSWORD,
            "scope": "openid email groups profile",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["id_token"]


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state['token']}"}


st.set_page_config(page_title="Aperture", page_icon="🔭")
st.title("Aperture")
st.caption("Permission-aware knowledge assistant. This is a local test UI.")

with st.sidebar:
    st.header("Sign In")
    email = st.selectbox(
        "Demo user",
        options=list(DEMO_USERS.keys()),
        format_func=lambda e: DEMO_USERS[e],
    )
    if st.button("Sign in", type="primary"):
        try:
            st.session_state["token"] = get_token(email)
            st.session_state["email"] = email
            st.success(f"Signed in as {email}")
        except Exception as exc:  # noqa: BLE001  (surface any auth error to the user)
            st.error(f"Sign in failed: {exc}")

    if "email" in st.session_state:
        st.info(f"Signed in: {DEMO_USERS[st.session_state['email']]}")

if "token" not in st.session_state:
    st.warning("Sign in as a demo user in the sidebar to begin.")
    st.stop()

ingest_tab, ask_tab = st.tabs(["Ingest", "Ask"])

with ingest_tab:
    st.subheader("Ingest A Document")
    st.caption("Ingested into your own tenant. Grant access by group or by user.")
    title = st.text_input("Title", value="Finance Refund Policy")
    text = st.text_area(
        "Text",
        height=160,
        value=(
            "Our refund policy allows enterprise customers to request a full "
            "refund within 30 days of purchase. Standard customers get a "
            "refund within 14 days."
        ),
    )
    col1, col2 = st.columns(2)
    viewer_groups = col1.text_input("Viewer groups (comma-separated)", value="finance")
    direct_viewers = col2.text_input("Direct viewers (comma-separated usernames)", value="")

    if st.button("Ingest", type="primary"):
        payload = {
            "title": title,
            "text": text,
            "viewer_groups": [g.strip() for g in viewer_groups.split(",") if g.strip()],
            "direct_viewers": [v.strip() for v in direct_viewers.split(",") if v.strip()],
        }
        with st.spinner("Ingesting (embedding chunks, writing permissions)..."):
            response = httpx.post(
                f"{API_BASE}/ingest", json=payload, headers=auth_headers(), timeout=120.0
            )
        if response.status_code == 200:
            result = response.json()
            st.success(f"Ingested as {result['document_id']} ({result['chunk_count']} chunks).")
        else:
            st.error(f"Ingest failed ({response.status_code}): {response.text}")

with ask_tab:
    st.subheader("Ask A Question")
    st.caption("You only get answers grounded in documents you are permitted to read.")
    question = st.text_input(
        "Question", value="What is the refund policy for enterprise customers?"
    )

    if st.button("Ask", type="primary"):
        with st.spinner("Retrieving permitted documents and generating an answer..."):
            response = httpx.post(
                f"{API_BASE}/ask",
                json={"question": question},
                headers=auth_headers(),
                timeout=120.0,
            )
        if response.status_code == 200:
            result = response.json()
            st.markdown("### Answer")
            st.write(result["answer"])
            cited = result["cited_document_ids"]
            if cited:
                st.markdown("### Cited Documents")
                for doc_id in cited:
                    st.code(doc_id, language=None)
            else:
                st.info("No documents cited (you may not have access to anything relevant).")
        else:
            st.error(f"Ask failed ({response.status_code}): {response.text}")
