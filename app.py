# Form to edit notes for selected strategy (updated layout)
with st.form("notes_form"):

    # Single tag for entire strategy
    strategy_data = data.get(selected_strategy, {})
    current_strategy_tag = "Neutral"
    if strategy_data:
        for ind_data in strategy_data.values():
            if "strategy_tag" in ind_data:
                current_strategy_tag = ind_data["strategy_tag"]
                break

    strategy_tag = st.selectbox(
        f"Strategy '{selected_strategy}' tag:", 
        options=["Neutral", "Buy", "Sell"], 
        index=["Neutral","Buy","Sell"].index(current_strategy_tag if current_strategy_tag in ["Neutral","Buy","Sell"] else "Neutral"),
        key="strategy_tag"
    )

    # Strategy type
    current_strategy_type = "Momentum"
    if strategy_data:
        for ind_data in strategy_data.values():
            if "momentum" in ind_data:
                current_strategy_type = ind_data["momentum"]
                break

    strategy_type = st.selectbox(
        f"Strategy '{selected_strategy}' type:", 
        options=["Momentum", "Extreme"], 
        index=0 if current_strategy_type == "Momentum" else 1,
        key="strategy_type"
    )
    st.markdown("---")

    # Organize indicators in columns (3 per row)
    indicators = STRATEGIES[selected_strategy]
    n_cols = 3
    rows = [indicators[i:i+n_cols] for i in range(0, len(indicators), n_cols)]

    for row in rows:
        cols = st.columns(len(row))
        for col, ind in zip(cols, row):
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"

            existing = data.get(selected_strategy, {}).get(ind, {})
            default_note = existing.get("note", "")
            default_status = existing.get("status", "Open")

            with col:
                with st.expander(ind, expanded=False):
                    st.text_area(f"Analysis — {ind}", value=default_note, key=key_note, height=120)
                    st.selectbox("Status", options=["Open", "Done"], index=0 if default_status=="Open" else 1, key=key_status)

    # Submit button
    submitted = st.form_submit_button("💾 Save all notes for this strategy")
    if submitted:
        if selected_strategy not in data:
            data[selected_strategy] = {}

        strategy_tag_val = st.session_state.get("strategy_tag", "Neutral")
        strategy_type_val = st.session_state.get("strategy_type", "Momentum")

        for ind in indicators:
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            note_val = st.session_state.get(key_note, "")
            status_val = st.session_state.get(key_status, "Open")

            data[selected_strategy][ind] = {
                "note": note_val,
                "status": status_val,
                "momentum": strategy_type_val,
                "strategy_tag": strategy_tag_val,
                "analysis_date": analysis_date.strftime('%Y-%m-%d'),
                "last_modified": datetime.utcnow().isoformat() + "Z"
            }
        save_data(data)
        st.success(f"Analyses saved for strategy '{selected_strategy}' with tag '{strategy_tag_val}'.")
