import streamlit as st
import plotly.graph_objects as go

def render_sidebar():
    """Renders the sidebar for user inputs."""
    with st.sidebar:
        st.title("💼 Portfolio Settings")
        st.markdown("---")
        
        st.subheader("1. Current Holdings")
        qty_gold = st.number_input("Gold Holdings (oz)", min_value=0.0, value=0.0, step=0.1, format="%.4f")
        qty_silver = st.number_input("Silver Holdings (oz)", min_value=0.0, value=0.0, step=1.0, format="%.4f")
        cash_dca = st.number_input("Cash / DCA Amount ($)", min_value=0.0, value=1000.0, step=100.0)
        
        st.markdown("---")
        st.subheader("2. Strategy Targets")
        target_gold_pct = st.slider("Target Gold (%)", 0, 100, 50)
        target_silver_pct = 100 - target_gold_pct
        st.info(f"Target: Gold {target_gold_pct}% | Silver {target_silver_pct}%")
        
        st.markdown("---")
        st.subheader("3. Portfolio Cap (Cash Out)")
        port_cap = st.number_input("Target Cap ($)", value=20000.0)

    return qty_gold, qty_silver, cash_dca, target_gold_pct, target_silver_pct, port_cap

def render_main_dashboard(df, p_gold, p_silver, prev_gold, prev_silver, z_score, latest_spread, prev_spread):
    """Renders the main dashboard with metrics and charts."""
    st.title("📈 Smart Portfolio: Z-Score System")
    st.markdown("ระบบบริหารพอร์ตอัตโนมัติ DCA + Rebalance ตามสถิติ")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gold Price", f"${p_gold:,.2f}", f"{p_gold-prev_gold:.2f}")
    col2.metric("Silver Price", f"${p_silver:,.2f}", f"{p_silver-prev_silver:.2f}")
    col3.metric("Spread (Ag*100-Au)", f"{latest_spread:.2f}", f"{latest_spread-prev_spread:.2f}")

    z_color = "off"
    z_state = "Neutral"
    if z_score > 2.0: 
        z_color = "inverse"
        z_state = "Silver Expensive (SELL)"
    elif z_score < -2.0: 
        z_color = "normal"
        z_state = "Silver Cheap (BUY)"

    col4.metric("Z-Score Status", f"{z_score:.2f}", z_state, delta_color=z_color)

    st.subheader("📊 Market Analysis (90-Day Z-Score)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], mode='lines', name='Z-Score', line=dict(color='blue', width=2)))
    fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Sell Zone (+2 SD)")
    fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="Buy Zone (-2 SD)")
    fig.add_hline(y=0, line_color="gray", annotation_text="Mean")
    fig.add_hrect(y0=2, y1=5, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_hrect(y0=-5, y1=-2, line_width=0, fillcolor="green", opacity=0.1)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, width='stretch')

def render_help_section():
    """Renders the help section."""
    with st.expander("📘 How to Use This Dashboard"):
        st.markdown("""
        This dashboard helps you manage a Gold and Silver portfolio using a Z-score-based strategy. Here's how to use it:

        1.  **Enter Your Holdings:** In the sidebar, input your current holdings of Gold (in ounces), Silver (in ounces), and the amount of cash you wish to invest (DCA).

        2.  **Set Your Targets:** Define your desired portfolio allocation between Gold and Silver using the slider. The system will use this as a baseline for rebalancing.

        3.  **Set a Portfolio Cap:**  Enter a target portfolio value. If your total portfolio value exceeds this cap, the system will signal to cash out the profits.

        4.  **Review the Analysis:**
            *   The **Z-Score Chart** shows the current Z-score of the Gold/Silver spread. A high Z-score suggests Silver is overvalued compared to Gold, and a low Z-score suggests it's undervalued.
            *   The **AI Recommendation** provides a clear action based on the Z-score. It will tell you whether to prioritize buying Gold or Silver, or to simply rebalance to your target allocation.

        5.  **Execute the Action Plan:**
            *   The **Action Plan** calculates the exact amounts to buy or sell to align your portfolio with the AI's recommendation.
            *   If the Z-score is within the normal range, the plan will aim to rebalance your portfolio to your target percentages.
            *   If the Z-score is high or low, the plan will prioritize buying the undervalued asset with your available cash.
        """)

def render_recommendation(advice_msg, alert_type):
    """Renders the AI recommendation message."""
    st.markdown("---")
    st.header("🤖 AI Recommendation & Execution")
    if alert_type == "success":
        st.success(advice_msg)
    elif alert_type == "error":
        st.error(advice_msg)
    else:
        st.info(advice_msg)

def render_order_sheet(total_val, val_gold, val_silver, cash_dca, port_cap, diff_gold, diff_silver, p_gold, p_silver):
    """Renders the order sheet with portfolio summary and action plan."""
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.subheader("📋 Portfolio Summary")
        st.write(f"Total Portfolio Value: **${total_val:,.2f}**")
        
        if port_cap > 0 and total_val > port_cap:
            profit = total_val - port_cap
            st.warning(f"💰 **CASH OUT SIGNAL:** Profit exceeds target! Consider taking out **${profit:,.2f}**")
        else:
            st.write(f"Distance to Cap: ${port_cap - total_val:,.2f}")

        labels = ['Gold', 'Silver', 'Cash']
        values = [val_gold, val_silver, cash_dca]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
        fig_pie.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, width='stretch')

    with col_res2:
        st.subheader("🛒 Action Plan (Buy/Sell Orders)")
        
        def make_card(asset, diff, price):
            action = "BUY" if diff > 0 else "SELL"
            color = "green" if diff > 0 else "red"
            units = abs(diff) / price if price > 0 else 0
            
            if abs(diff) < 10: return

            st.metric(label=f"{asset} Action", value=action)
            st.metric(label="Amount", value=f"${abs(diff):,.2f}")
            st.metric(label="Units", value=f"{units:.4f} oz")


        make_card("Gold", diff_gold, p_gold)
        make_card("Silver", diff_silver, p_silver)
        
        if abs(diff_gold) < 10 and abs(diff_silver) < 10:
            st.info("✅ Portfolio is balanced (No Action Needed)")

def render_footer():
    """Renders the footer."""
    st.markdown("---")
    st.caption("Auto-generated by Smart Portfolio AI | Data Source: Yahoo Finance")