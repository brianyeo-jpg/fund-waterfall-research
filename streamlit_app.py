"""
Fund Waterfall Research - Interactive Streamlit App
Displays the research document with optional interactive calculators
"""
import streamlit as st
import streamlit.components.v1 as components

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
    # Read HTML content
    with open("fund_waterfall_research_v2.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Display the HTML content directly using markdown (no iframe, no internal scrolling)
    # This allows the browser's native scroll to work
    st.components.v1.html(html_content, height=None, scrolling=False)

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

        # Asset
        forward_irr = st.number_input("Asset Forward IRR (%)", min_value=0.0, max_value=30.0, value=11.0, step=0.5)

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
        has_alternatives = st.checkbox("Strong alternative deployment opportunities available?", value=True)
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
                would_drag_irr = st.checkbox("Holding this asset would drag fund below target quartile?")
            else:
                raising_soon = False
                would_drag_irr = False
        else:
            raising_soon = False
            would_drag_irr = False

        st.markdown("---")

        # Market conditions
        peak_market = st.checkbox("Market at peak with cap rate expansion risk?")
        if peak_market:
            downside_risk = st.slider("Estimated downside from cap rate expansion (%)", 0, 50, 20, 5)

    with col2:
        st.subheader("Five-Question Framework")

        # Convert to decimals
        forward_irr_dec = forward_irr / 100
        pref_rate_dec = pref_rate / 100
        alternative_irr_dec = alternative_irr / 100 if has_alternatives else 0.0

        decision = None
        decision_driver = None

        # Question 1: Below pref?
        st.markdown("#### Question 1: Forward IRR vs Pref Rate")
        if forward_irr < pref_rate:
            st.error(f"❌ **{forward_irr:.1f}% < {pref_rate:.1f}%** → EXIT (Destroying value)")
            decision = "EXIT"
            decision_driver = "Below Pref"
        else:
            st.success(f"✅ {forward_irr:.1f}% > {pref_rate:.1f}% (Pass)")

        st.markdown("---")

        # Question 2: IRR preservation (only for commingled funds)
        if decision is None:
            st.markdown("#### Question 2: IRR Preservation (Fundraising)")
            if fund_type == "Separate Account":
                st.info("⊘ **N/A** - Separate accounts have minimal IRR preservation pressure")
            elif not raising_soon:
                st.info("⊘ **N/A** - No near-term fundraise")
            elif would_drag_irr:
                st.error(f"❌ **EXIT** - Would drag fund below {target_quartile_cutoff:.1f}% target quartile")
                st.markdown(f"Current IRR: {current_fund_irr:.1f}% → Protect fundraising capacity")
                decision = "EXIT"
                decision_driver = "IRR Preservation"
            else:
                st.success(f"✅ Maintains fund at {current_fund_irr:.1f}% (above {target_quartile_cutoff:.1f}% target)")

        st.markdown("---")

        # Question 3: Peak market
        if decision is None:
            st.markdown("#### Question 3: Market Timing Risk")
            if not peak_market:
                st.info("⊘ **N/A** - No peak market signals")
            else:
                # Rule: if downside risk > 2 years of forward returns, exit
                two_year_gains = forward_irr * 2
                if downside_risk > two_year_gains:
                    st.error(f"❌ **EXIT** - Downside risk ({downside_risk}%) > 2yr forward gains ({two_year_gains:.1f}%)")
                    st.markdown("→ Market timing risk outweighs forward IRR")
                    decision = "EXIT"
                    decision_driver = "Market Timing"
                else:
                    st.success(f"✅ Downside manageable ({downside_risk}% < {two_year_gains:.1f}% 2yr gains)")

        st.markdown("---")

        # Question 4: Opportunity cost
        if decision is None:
            st.markdown("#### Question 4: Alternative Deployment")
            if not has_alternatives:
                st.info("⊘ **N/A** - No strong deployment alternatives")
            elif fund_stage == "Early (Years 1-4)" and alternative_irr > forward_irr + 3:
                spread = alternative_irr - forward_irr
                st.error(f"❌ **EXIT** - Alternative ({alternative_irr:.1f}%) > Asset + 3% ({forward_irr + 3:.1f}%)")
                st.markdown(f"**Opportunity cost:** {spread:.1f}% spread")
                decision = "EXIT"
                decision_driver = "Opportunity Cost"
            elif fund_stage in ["Mid (Years 5-7)", "Late (Years 8-10)"] and alternative_irr > forward_irr + 3:
                spread = alternative_irr - forward_irr
                st.warning(f"⚠️ **CONSIDER EXIT** - Alternative ({alternative_irr:.1f}%) > Asset + 3%")
                st.markdown(f"Spread: {spread:.1f}%. In {fund_stage.split('(')[0].strip()} stage, balance opportunity cost vs transaction friction")
                if spread > 5:
                    st.error(f"❌ **EXIT** - {spread:.1f}% spread too large to ignore")
                    decision = "EXIT"
                    decision_driver = "Opportunity Cost"
                else:
                    st.success(f"✅ {spread:.1f}% spread modest - transaction friction may favor holding")
            else:
                st.success(f"✅ No compelling alternatives (Alternative: {alternative_irr:.1f}% vs Asset: {forward_irr:.1f}%)")

        st.markdown("---")

        # Question 5: Default decision
        if decision is None:
            st.markdown("#### Question 5: Default Decision")
            st.success(f"✅ **HOLD** - Asset clears all thresholds")
            decision = "HOLD"
            decision_driver = "Asset fundamentals solid"

        st.markdown("---")
        st.markdown("---")

        # Final recommendation
        if decision == "EXIT":
            st.error(f"### 🔴 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Decision Driver:** {decision_driver}")
        elif decision == "HOLD":
            st.success(f"### 🟢 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Rationale:** {decision_driver}")
        else:
            st.warning(f"### 🟡 RECOMMENDATION: **{decision}**")
            st.markdown(f"**Context:** {decision_driver}")

        st.markdown("---")

        # Summary of thresholds
        with st.expander("📊 View Threshold Summary"):
            st.markdown(f"""
            **Thresholds Evaluated:**
            - Pref Rate: {pref_rate:.1f}%
            - Asset Forward IRR: {forward_irr:.1f}%
            - Alternative Deployment: {alternative_irr:.1f}% (if applicable)
            - Fund Type: {fund_type}
            - Fund Stage: {fund_stage}

            **Key Context:**
            - {"Raising next fund soon" if raising_soon else "No near-term fundraise"}
            - {"Peak market conditions" if peak_market else "Normal market conditions"}
            - {"Strong alternatives available" if has_alternatives else "Limited alternatives"}
            """)

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
