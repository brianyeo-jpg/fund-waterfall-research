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
    ["Research Document", "Exit Decision Calculator", "About"]
)

if page == "Research Document":
    st.title("Asset Exit Timing in European Waterfall Funds: Beyond the Pref Rate")

    # Option 1: Embed the HTML directly
    with open("fund_waterfall_research_v2.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Display in iframe with scrolling
    components.html(html_content, height=800, scrolling=True)

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
    st.markdown("**Quick tool to evaluate whether to hold or exit an asset**")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Asset Inputs")
        forward_irr = st.number_input("Asset Forward IRR (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
        asset_equity = st.number_input("Asset Equity ($M)", min_value=0.0, max_value=500.0, value=10.0, step=1.0)
        hold_period = st.number_input("Expected Hold Period (years)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

        st.subheader("Fund Context")
        pref_rate = st.number_input("Fund Pref Rate (%)", min_value=0.0, max_value=15.0, value=8.0, step=0.5)
        alternative_irr = st.number_input("Alternative Deployment IRR (%)", min_value=0.0, max_value=30.0, value=12.0, step=0.5)
        transaction_cost = st.number_input("Transaction Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5)

        fund_position = st.selectbox(
            "Fund Waterfall Position",
            ["Below Pref", "In Catch-Up", "Past Catch-Up"]
        )

        raising_soon = st.checkbox("Raising next fund within 18 months?")
        if raising_soon:
            current_fund_irr = st.number_input("Current Fund IRR (%)", min_value=0.0, max_value=40.0, value=19.0, step=0.5)
            target_quartile_cutoff = st.number_input("Target Quartile Cutoff (%)", min_value=0.0, max_value=40.0, value=18.0, step=0.5)

        peak_market = st.checkbox("Market at peak with cap rate expansion risk?")

    with col2:
        st.subheader("Decision Analysis")

        # Convert to decimals
        forward_irr_dec = forward_irr / 100
        pref_rate_dec = pref_rate / 100
        alternative_irr_dec = alternative_irr / 100
        transaction_cost_dec = transaction_cost / 100

        # Calculate thresholds
        transaction_adjusted = pref_rate_dec + (transaction_cost_dec / hold_period)

        # Capture rate
        if fund_position == "Below Pref":
            capture_rate = 0.0
        elif fund_position == "In Catch-Up":
            capture_rate = 0.5
        else:
            capture_rate = 0.2

        # Calculate metrics
        incremental_profit = asset_equity * forward_irr_dec * hold_period
        incremental_pref = asset_equity * pref_rate_dec * hold_period
        net_profit = incremental_profit - incremental_pref
        gp_carry = net_profit * capture_rate

        st.markdown("### Threshold Analysis")

        # Question 1: Below pref?
        if forward_irr_dec < pref_rate_dec:
            st.error(f"❌ **EXIT** - Forward IRR ({forward_irr:.1f}%) < Pref Rate ({pref_rate:.1f}%)")
            st.markdown("**Destroying value.** Asset return below economic baseline.")
            decision = "EXIT"

        # Question 2: IRR preservation
        elif raising_soon and current_fund_irr > target_quartile_cutoff:
            st.warning(f"⚠️ **CHECK** - Fundraising within 18 months")
            st.markdown(f"Current fund IRR: {current_fund_irr:.1f}% (above {target_quartile_cutoff:.1f}% target)")
            st.markdown("Consider whether asset would drag IRR below target quartile")
            decision = "CHECK IRR IMPACT"

        # Question 3: Peak market
        elif peak_market:
            st.warning(f"⚠️ **CONSIDER EXIT** - Market at peak")
            st.markdown("Cap rate expansion risk may outweigh forward IRR")
            if forward_irr_dec < 0.12:
                st.markdown("→ **Recommend EXIT** given market timing concerns")
                decision = "EXIT (Market Timing)"
            else:
                st.markdown("→ Strong asset fundamentals may justify holding")
                decision = "HOLD (but monitor closely)"

        # Question 4: Opportunity cost
        elif alternative_irr_dec > forward_irr_dec + 0.03:
            spread = alternative_irr - forward_irr
            st.error(f"❌ **EXIT** - Alternative IRR ({alternative_irr:.1f}%) > Asset + 3%")
            st.markdown(f"**Opportunity cost:** {spread:.1f}% spread = ${asset_equity * spread/100 * hold_period:.2f}M foregone profit")
            decision = "EXIT (Redeploy)"

        # Question 5: Hold
        else:
            st.success(f"✅ **HOLD** - Forward IRR ({forward_irr:.1f}%) clears all thresholds")
            decision = "HOLD"

        st.markdown("---")
        st.markdown("### Economic Impact")

        metrics = {
            "Incremental Profit": f"${incremental_profit:.2f}M",
            "Less: Incremental Pref": f"-${incremental_pref:.2f}M",
            "Net to Post-Pref Pool": f"${net_profit:.2f}M",
            "GP Capture Rate": f"{capture_rate:.0%}",
            "Marginal GP Carry": f"${gp_carry:.2f}M"
        }

        for label, value in metrics.items():
            st.markdown(f"**{label}:** {value}")

        st.markdown("---")
        st.markdown(f"### Final Recommendation: **{decision}**")

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
