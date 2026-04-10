import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import charts
import storage
from vision import analyze_image

st.set_page_config(page_title="Fruit Snack Counter", page_icon="🍇", layout="wide")
st.title("Welch's Fruit Snack Counter")

tab_upload, tab_totals, tab_history = st.tabs(["Upload", "Totals", "History"])


# ── Upload tab ────────────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("Analyze a handful")
    uploaded = st.file_uploader(
        "Take a photo of a handful of fruit snacks and upload it here",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded:
        st.image(uploaded, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze with Claude", type="primary"):
            with st.spinner("Counting snacks..."):
                # Save to a temp file so vision.py can open it
                suffix = os.path.splitext(uploaded.name)[-1] or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getbuffer())
                    tmp_path = tmp.name

                counts, notes = analyze_image(tmp_path)
                os.unlink(tmp_path)

            st.session_state["pending_counts"] = counts
            st.session_state["pending_filename"] = uploaded.name
            st.session_state["pending_notes"] = notes

    if "pending_counts" in st.session_state:
        st.divider()
        st.subheader("Review counts before saving")
        st.caption("Correct any misidentifications by editing the table, then click Save.")

        if st.session_state.get("pending_notes"):
            st.warning(st.session_state["pending_notes"])

        counts_data = [
            {
                "Flavor": storage.FLAVOR_LABELS[f],
                "key": f,
                "Count": st.session_state["pending_counts"].get(f, 0),
            }
            for f in storage.FLAVORS
        ]

        edited = st.data_editor(
            counts_data,
            column_config={
                "Flavor": st.column_config.TextColumn(disabled=True),
                "key": None,  # hidden
                "Count": st.column_config.NumberColumn(min_value=0, step=1),
            },
            hide_index=True,
            use_container_width=True,
        )

        total_shown = sum(row["Count"] for row in edited)
        st.metric("Total pieces", total_shown)

        if st.button("Save session", type="primary"):
            final_counts = {row["key"]: int(row["Count"]) for row in edited}
            storage.save_session(
                final_counts,
                st.session_state["pending_filename"],
                st.session_state.get("pending_notes", ""),
            )
            del st.session_state["pending_counts"]
            del st.session_state["pending_filename"]
            del st.session_state["pending_notes"]
            st.success("Session saved!")
            st.rerun()


# ── Totals tab ────────────────────────────────────────────────────────────────
with tab_totals:
    totals = storage.get_totals()
    grand_total = storage.get_grand_total()
    session_count = len(storage.get_sessions())

    st.subheader("Cumulative totals")
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("Total pieces counted", grand_total)
    col_metric2.metric("Sessions recorded", session_count)

    if grand_total == 0:
        st.info("No data yet — upload a photo in the Upload tab to get started.")
    else:
        totals_display = [
            {
                "Flavor": storage.FLAVOR_LABELS[f],
                "Count": totals[f],
                "Percentage": f"{totals[f] / grand_total * 100:.1f}%" if grand_total else "0%",
            }
            for f in storage.FLAVORS
            if totals[f] > 0
        ]
        st.dataframe(totals_display, hide_index=True, use_container_width=True)

        col_pie, col_bar = st.columns(2)
        with col_pie:
            st.pyplot(charts.pie_chart(totals))
        with col_bar:
            st.pyplot(charts.bar_chart(totals))


# ── History tab ───────────────────────────────────────────────────────────────
with tab_history:
    sessions = storage.get_sessions()
    st.subheader(f"Session history ({len(sessions)} sessions)")

    if not sessions:
        st.info("No sessions recorded yet.")
    else:
        st.pyplot(charts.history_chart(sessions))
        st.divider()

        for session in reversed(sessions):
            with st.expander(f"{session['id']}  —  {session['total']} pieces  ({session['image_filename']})"):
                counts_display = [
                    {"Flavor": storage.FLAVOR_LABELS[f], "Count": session["counts"].get(f, 0)}
                    for f in storage.FLAVORS
                    if session["counts"].get(f, 0) > 0
                ]
                st.dataframe(counts_display, hide_index=True, use_container_width=True)
                if session.get("notes"):
                    st.caption(session["notes"])

                if st.button("Delete this session", key=f"del_{session['id']}"):
                    storage.delete_session(session["id"])
                    st.rerun()
