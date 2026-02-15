"""
Fund Waterfall Research - Interactive Streamlit App
Displays the research document with optional interactive calculators
"""
import streamlit as st
import streamlit.components.v1 as components
import os

# Page config
st.set_page_config(
    page_title="Asset Exit Timing in European Waterfall Funds",
    page_icon="📊",
    layout="wide"
)

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Research Findings", "Exit Decision Calculator", "About"]
)

if page == "Research Findings":
    # Read HTML content with absolute path
    html_path = os.path.join(os.path.dirname(__file__), "fund_waterfall_research_v2.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Display with large fixed height - browser's native scroll will work
    # Set height large enough to contain full document (~15000px)
    st.components.v1.html(html_content, height=15000, scrolling=False)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 Download")
    st.sidebar.download_button(
        label="Download as HTML",
        data=html_content,
        file_name="fund_waterfall_research.html",
        mime="text/html"
    )

    st.sidebar.markdown("### 🔗 GitHub")
    st.sidebar.markdown("[View on GitHub Pages](https://brianyeo-jpg.github.io/fund-waterfall-research/fund_waterfall_research_v2.html)")

elif page == "Exit Decision Calculator":
    st.title("Exit Decision Calculator")
    st.markdown("**Five-question framework to evaluate hold vs. exit decisions**")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("Asset & Fund Context")

        # Question 0: Leverage/debt maturity pre-condition
        st.markdown("**Pre-Condition Check**")
        debt_maturity = st.checkbox(
            "Debt maturing within 12 months (unrefin anceable)?",
            value=False,
            help="If yes, exit is mandatory regardless of forward IRR - structural constraint"
        )

        st.markdown("---")

        # Asset
        forward_irr = st.number_input("Asset Forward IRR (%)", min_value=0.0, max_value=30.0, value=11.0, step=0.5)

        st.markdown("**Economic Threshold Inputs**")
        current_equity = st.number_input(
            "Current Asset Equity ($M)",
            min_value=0.1,
            max_value=1000.0,
            value=40.0,
            step=5.0,
            help="Current market value of the asset equity"
        )
        unreturned_capital = st.number_input(
            "Unreturned Capital ($M)",
            min_value=0.1,
            max_value=1000.0,
            value=40.0,
            step=5.0,
            help="Original equity invested minus distributions. Set equal to Current Equity for fresh assets (no distributions)."
        )

        st.markdown("---")

        # Fund structure
        fund_type = st.radio(
            "Fund Structure",
            ["Commingled Fund", "Separate Account"],
            help="Separate accounts have reduced IRR preservation pressure"
        )

        fund_stage = st.selectbox(
            "Fund Lifecycle Stage",
            ["Early (Years 1-4)", "Mid (Years 5-7)", "Late (Years 8-10)"]
        )

        pref_rate = st.number_input("Fund Pref Rate (%)", min_value=0.0, max_value=15.0, value=8.0, step=0.5)

        st.markdown("---")

        # Alternative opportunities
        has_alternatives = st.checkbox("Strong alternative deployment opportunities available?", value=False)
        if has_alternatives:
            alternative_irr = st.number_input("Alternative Deployment IRR (%)", min_value=0.0, max_value=30.0, value=15.0, step=0.5)
        else:
            alternative_irr = 0.0

        st.markdown("---")

        # Fundraising context
        if fund_type == "Commingled Fund":
            raising_soon = st.checkbox("Raising next fund within 18 months?")
            if raising_soon:
                current_fund_irr = st.number_input("Current Fund IRR (%)", min_value=0.0, max_value=40.0, value=19.0, step=0.5)
                target_quartile_cutoff = st.number_input("Target Quartile Cutoff (%)", min_value=0.0, max_value=40.0, value=18.0, step=0.5)
                fund_nav = st.number_input("Fund NAV ($M)", min_value=1.0, max_value=10000.0, value=400.0, step=10.0, help="Total fund net asset value for materiality calculation")
                would_drag_irr = st.checkbox("Holding this asset would drag fund below target quartile?")
            else:
                raising_soon = False
                would_drag_irr = False
                fund_nav = 0
        else:
            raising_soon = False
            would_drag_irr = False
            fund_nav = 0

        st.markdown("---")

        # Market conditions
        peak_market = st.checkbox("Market at peak with cap rate expansion risk?")
        if peak_market:
            downside_risk = st.slider("Estimated downside from cap rate expansion (%)", 0, 50, 20, 5)

    with col2:
        st.subheader("Five-Question Framework")

        # Calculate economic threshold using corrected formula
        economic_threshold = pref_rate * (unreturned_capital / current_equity)

        # ==========================================
        # PRE-CALCULATE DECISION FOR SUMMARY BOX
        # ==========================================
        decision = None
        decision_driver = None
        decision_question = None

        # Question 0: Debt maturity pre-condition
        if debt_maturity:
            decision = "EXIT"
            decision_driver = "Debt Maturity (Structural Constraint)"
            decision_question = 0

        # Question 1: Below economic threshold?
        if decision is None:
            if forward_irr < economic_threshold:
                decision = "EXIT"
                decision_driver = "Below Economic Threshold"
                decision_question = 1

        # Question 2: IRR preservation (only for commingled funds)
        if decision is None:
            if fund_type == "Commingled Fund" and raising_soon and would_drag_irr:
                # Apply materiality threshold: >10% of NAV or >25 bps IRR drag
                asset_pct_of_nav = (current_equity / fund_nav) * 100 if fund_nav > 0 else 0
                # Simplified IRR drag calculation (rough approximation)
                irr_drag_bps = abs(current_fund_irr - target_quartile_cutoff) * 100

                is_material = (asset_pct_of_nav > 10) or (irr_drag_bps > 25)

                if is_material:
                    decision = "EXIT"
                    decision_driver = "IRR Preservation (Material Impact)"
                    decision_question = 2

        # Question 3: Peak market
        if decision is None:
            if peak_market:
                # Use simple 2x for rough heuristic (compounded would be ((1 + forward_irr/100)^2 - 1) * 100)
                # But per research, simple 2x is acceptable approximation for typical REPE IRRs
                two_year_gains = forward_irr * 2
                if downside_risk > two_year_gains:
                    decision = "EXIT"
                    decision_driver = "Market Timing"
                    decision_question = 3

        # Question 4: Opportunity cost
        if decision is None:
            if has_alternatives:
                spread = alternative_irr - forward_irr
                # CORRECTED LOGIC: Early stage should have HIGHER threshold (more friction tolerance)
                # Early: exit if spread > 5% (aggressive capital deployment)
                # Mid/Late: exit if spread > 3% (less friction, easier to exit)
                if fund_stage == "Early (Years 1-4)":
                    if spread > 5:
                        decision = "EXIT"
                        decision_driver = "Opportunity Cost"
                        decision_question = 4
                elif fund_stage in ["Mid (Years 5-7)", "Late (Years 8-10)"]:
                    if spread > 3:
                        decision = "EXIT"
                        decision_driver = "Opportunity Cost"
                        decision_question = 4

        # Question 5: Default decision
        if decision is None:
            decision = "HOLD"
            decision_driver = "Asset fundamentals solid"
            decision_question = 5

        # ==========================================
        # DISPLAY DECISION SUMMARY AT TOP
        # ==========================================
        st.markdown("---")
        if decision == "EXIT":
            st.error(f"### 🔴 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Decision Driver:** {decision_driver} (Question {decision_question})")
        elif decision == "HOLD":
            st.success(f"### 🟢 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Rationale:** {decision_driver}")
        else:
            st.warning(f"### 🟡 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Context:** {decision_driver}")
        st.markdown("---")

        # ==========================================
        # DETAILED QUESTIONS (with expanders)
        # ==========================================

        # Question 0: Debt maturity pre-condition
        with st.expander("Question 0: Debt Maturity Pre-Condition", expanded=(decision_question == 0)):
            if debt_maturity:
                st.error("❌ **MANDATORY EXIT** - Debt maturing within 12 months, refinancing unavailable")
                st.markdown("This is a structural constraint, not an economic optimization. Proceed to disposition planning immediately.")
            else:
                st.success("✅ No near-term debt maturity forcing exit")

        # Question 1: Below economic threshold?
        with st.expander("Question 1: Forward IRR vs Economic Threshold", expanded=(decision_question == 1 or decision_question == 5)):
            # Determine asset type for display
            if unreturned_capital < current_equity:
                asset_type = "Mature (Distributed)"
            elif unreturned_capital > current_equity:
                asset_type = "Underwater (Distressed)"
            else:
                asset_type = "Fresh (No Distributions)"

            st.markdown(f"**Economic Threshold Calculation:**")
            st.code(f"Threshold = {pref_rate:.1f}% × (${unreturned_capital:.1f}M / ${current_equity:.1f}M) = {economic_threshold:.1f}%")
            st.markdown(f"*Asset Type: {asset_type}*")

            if forward_irr < economic_threshold:
                st.error(f"❌ **{forward_irr:.1f}% < {economic_threshold:.1f}%** → EXIT (Destroying value)")
                st.markdown(f"Annual pref accrual (${unreturned_capital:.1f}M × {pref_rate:.1f}% = ${unreturned_capital * pref_rate / 100:.2f}M) exceeds profit from holding (${current_equity:.1f}M × {forward_irr:.1f}% = ${current_equity * forward_irr / 100:.2f}M)")
            else:
                st.success(f"✅ {forward_irr:.1f}% > {economic_threshold:.1f}% (Pass)")
                st.markdown(f"Profit from holding (${current_equity * forward_irr / 100:.2f}M) exceeds pref accrual (${unreturned_capital * pref_rate / 100:.2f}M)")

        # Question 2: IRR preservation (only for commingled funds)
        with st.expander("Question 2: IRR Preservation (Fundraising)", expanded=(decision_question == 2)):
            if fund_type == "Separate Account":
                st.info("⊘ **N/A** - Separate accounts have minimal IRR preservation pressure")
            elif not raising_soon:
                st.info("⊘ **N/A** - No near-term fundraise")
            elif would_drag_irr:
                # Show materiality calculation
                asset_pct_of_nav = (current_equity / fund_nav) * 100 if fund_nav > 0 else 0
                irr_drag_bps = abs(current_fund_irr - target_quartile_cutoff) * 100

                st.markdown(f"**Materiality Check:**")
                st.code(f"Asset % of NAV: {asset_pct_of_nav:.1f}% (threshold: >10%)\nIRR Drag: {irr_drag_bps:.0f} bps (threshold: >25 bps)")

                is_material = (asset_pct_of_nav > 10) or (irr_drag_bps > 25)

                if is_material:
                    st.error(f"❌ **EXIT** - Would drag fund below {target_quartile_cutoff:.1f}% target quartile (material impact)")
                    st.markdown(f"Current IRR: {current_fund_irr:.1f}% → Protect fundraising capacity")
                else:
                    st.warning(f"⚠️ Would drag IRR but impact is **immaterial** ({asset_pct_of_nav:.1f}% of NAV, {irr_drag_bps:.0f} bps drag)")
                    st.markdown("Proceed to Question 3")
            else:
                st.success(f"✅ Maintains fund at {current_fund_irr:.1f}% (above {target_quartile_cutoff:.1f}% target)")

        # Question 3: Peak market
        with st.expander("Question 3: Market Timing Risk", expanded=(decision_question == 3)):
            if not peak_market:
                st.info("⊘ **N/A** - No peak market signals")
            else:
                # Rule: if downside risk > 2 years of forward returns, exit
                # Using simple 2x heuristic (compound would be ((1 + IRR/100)^2 - 1) * 100, but difference is small for typical IRRs)
                two_year_gains = forward_irr * 2
                if downside_risk > two_year_gains:
                    st.error(f"❌ **EXIT** - Downside risk ({downside_risk}%) > 2yr forward gains ({two_year_gains:.1f}%)")
                    st.markdown("→ Market timing risk outweighs forward IRR")
                    st.markdown("*Peak indicators: cap spreads to Treasuries at lows, high transaction volume, Fed tightening*")
                else:
                    st.success(f"✅ Downside manageable ({downside_risk}% < {two_year_gains:.1f}% 2yr gains)")

        # Question 4: Opportunity cost
        with st.expander("Question 4: Alternative Deployment", expanded=(decision_question == 4)):
            if not has_alternatives:
                st.info("⊘ **N/A** - No strong deployment alternatives")
            else:
                spread = alternative_irr - forward_irr

                # CORRECTED LOGIC: Early stage has HIGHER threshold (more friction)
                if fund_stage == "Early (Years 1-4)":
                    st.markdown(f"**Early Stage:** Higher friction tolerance (5% threshold)")
                    st.markdown(f"Spread: {spread:.1f}% = Alternative ({alternative_irr:.1f}%) - Asset ({forward_irr:.1f}%)")

                    if spread > 5:
                        st.error(f"❌ **EXIT** - {spread:.1f}% spread exceeds 5% early-stage threshold")
                        st.markdown("Aggressive capital deployment justified")
                    else:
                        st.success(f"✅ {spread:.1f}% spread < 5% threshold - transaction friction favors holding")

                elif fund_stage in ["Mid (Years 5-7)", "Late (Years 8-10)"]:
                    st.markdown(f"**{fund_stage.split('(')[0].strip()} Stage:** Lower friction tolerance (3% threshold)")
                    st.markdown(f"Spread: {spread:.1f}% = Alternative ({alternative_irr:.1f}%) - Asset ({forward_irr:.1f}%)")

                    if spread > 3:
                        st.error(f"❌ **EXIT** - {spread:.1f}% spread exceeds 3% {fund_stage.split('(')[0].strip().lower()}-stage threshold")
                        st.markdown("Lower friction in mature fund justifies exit")
                    else:
                        st.success(f"✅ {spread:.1f}% spread < 3% threshold - hold to avoid unnecessary transaction costs")

        # Question 5: Default decision
        with st.expander("Question 5: Default Decision", expanded=(decision_question == 5)):
            if decision == "HOLD":
                st.success(f"✅ **HOLD** - Asset clears all thresholds")
            else:
                st.info("⊘ **N/A** - Decision made at earlier threshold")

        st.markdown("---")

        # Summary of thresholds
        with st.expander("📊 View Threshold Summary"):
            # Determine asset type
            if unreturned_capital < current_equity:
                asset_type_desc = "Mature (Distributed)"
            elif unreturned_capital > current_equity:
                asset_type_desc = "Underwater (Distressed)"
            else:
                asset_type_desc = "Fresh (No Distributions)"

            # Calculate applicable thresholds
            asset_pct_nav = (current_equity / fund_nav) * 100 if raising_soon and fund_nav > 0 else 0
            opp_cost_threshold = 5 if fund_stage == "Early (Years 1-4)" else 3

            summary_text = f"""
            **Pre-Condition:**
            - Debt Maturity: {"YES - Mandatory Exit" if debt_maturity else "No"}

            **Economic Threshold (Question 1):**
            - Formula: {pref_rate:.1f}% × (${unreturned_capital:.1f}M / ${current_equity:.1f}M) = **{economic_threshold:.1f}%**
            - Asset Type: {asset_type_desc}
            - Asset Forward IRR: {forward_irr:.1f}%

            **IRR Preservation (Question 2):**
            - Fund Type: {fund_type}
            - Raising Soon: {"Yes" if raising_soon else "No"}
            """

            if raising_soon and fund_type == "Commingled Fund":
                summary_text += f"""- Fund NAV: ${fund_nav:.0f}M
            - Asset % of NAV: {asset_pct_nav:.1f}% (materiality: >10%)
            - Current Fund IRR: {current_fund_irr:.1f}%
            - Target Quartile: {target_quartile_cutoff:.1f}%
            """

            summary_text += f"""
            **Market Timing (Question 3):**
            - Peak Market: {"Yes" if peak_market else "No"}
            """

            if peak_market:
                two_year_gains = forward_irr * 2
                summary_text += f"""- Downside Risk: {downside_risk}%
            - 2-Year Forward Gains: {two_year_gains:.1f}%
            """

            summary_text += f"""
            **Opportunity Cost (Question 4):**
            - Alternatives Available: {"Yes" if has_alternatives else "No"}
            - Fund Stage: {fund_stage}
            - Threshold: {opp_cost_threshold}% spread
            """

            if has_alternatives:
                spread = alternative_irr - forward_irr
                summary_text += f"""- Alternative IRR: {alternative_irr:.1f}%
            - Spread: {spread:.1f}%
            """

            st.markdown(summary_text)

else:  # About page
    st.title("About This Research")

    st.markdown("""
    ## Purpose

    This research addresses a critical gap in private equity and real estate fund management:
    **How should fund-level preferred return accrual affect asset-level exit timing decisions?**

    ## Key Findings

    1. **Economic Baseline:** Exit when Asset Forward IRR < Fund Pref Rate (typically 8%)

    2. **Five-Threshold Framework:** In practice, the decision requires comparing against:
       - Pref Rate (8%)
       - Alternative Deployment IRR (10-15%)
       - Transaction-Adjusted Threshold (9-10%)
       - Market Timing Threshold (10-15%)
       - IRR Preservation Threshold (12-16%)

    3. **IRR Preservation Often Dominates:** For funds approaching fundraising, protecting vintage rankings
       often matters more than current carry maximization

    4. **GP Incentive Distortions:** 50/50 catch-up structures create 2.5× higher marginal carry during
       catch-up phase, biasing hold/exit decisions

    ## Author

    Internal Research - Portfolio & Fund Management
    February 2026

    ## Links

    - [GitHub Repository](https://github.com/brianyeo-jpg/fund-waterfall-research)
    - [GitHub Pages (HTML)](https://brianyeo-jpg.github.io/fund-waterfall-research/fund_waterfall_research_v2.html)

    ## Citation

    If referencing this framework in presentations or internal memos:

    > "Asset Exit Timing in European Waterfall Funds: Beyond the Pref Rate" (Internal Research, Feb 2026)
    """)
