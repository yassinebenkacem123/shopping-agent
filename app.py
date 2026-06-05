import streamlit as st
import sqlite3
import json
import uuid
import unicodedata
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from shopping_agent import agent_invoke
from product_api import search_products, get_product_details, get_product_price
from review_api import get_product_rating

# Set Page Config
st.set_page_config(
    page_title="Shop Agent Conversational Shopping Agent",
    layout="wide",
    page_icon="https://cdn-icons-png.flaticon.com/512/1162/1162499.png",
    initial_sidebar_state="collapsed"
)

# ----------------- Helper Functions -----------------

def get_db_path() -> Path:
    return Path(__file__).parent.absolute() / "store.db"

def clean_emojis(text: str) -> str:
    """Strips all unicode emojis from the response text using character classification."""
    # Emojis are classified as 'So' (Symbol, other) in Unicode database.
    # Checkmarks might be categorized as 'So', but since we use FontAwesome, we want a clean output.
    # Normal currency symbols ($: Sc), math symbols (+: Sm) are retained.
    return "".join(c for c in text if unicodedata.category(c) not in ('So',))

def extract_message_text(message) -> str:
    """Safely extracts text content from LangChain messages (handles strings and list blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts)
    return ""

def get_categories():
    """Queries all distinct product categories from the database."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products")
        cats = [r[0] for r in cursor.fetchall()]
        conn.close()
        return sorted(cats)
    except Exception:
        return []

def get_db_price_bounds():
    """Gets the minimum and maximum price from the products database to set slider bounds."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(price), MAX(price) FROM products")
        min_p, max_p = cursor.fetchone()
        conn.close()
        return float(min_p or 0.0), float(max_p or 100.0)
    except Exception:
        return 0.0, 100.0

def get_orders():
    """Queries all placed orders from the database."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, product_id, product_name, quantity, total_price, ordered_at FROM orders ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

# ----------------- Styles & CDNs -----------------

# Inject FontAwesome CDN and Custom Premium CSS
# st.markdown(
#     """
#     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
#     html, body, [class*="css"] {
#         font-family: 'Outfit', sans-serif;
#     }
    
#     /* Elegant Chat Message Styles */
#     .stChatMessage {
#         background-color: rgba(255, 255, 255, 0.03);
#         border-radius: 16px;
#         padding: 16px;
#         margin-bottom: 12px;
#         border: 1px solid rgba(255, 255, 255, 0.06);
#         box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
#         backdrop-filter: blur(8px);
#         -webkit-backdrop-filter: blur(8px);
#     }
    
#     .stChatMessage[data-testid="chat-avatar-user"] {
#         background: linear-gradient(135deg, #0f172a, #1e293b);
#         border: 1px solid rgba(0, 173, 181, 0.25);
#     }
    
#     /* Product card highlights matching standard markdown blockquotes */
#     blockquote {
#         border-left: 4px solid #00adb5 !important;
#         background-color: rgba(0, 173, 181, 0.04) !important;
#         padding: 12px 18px !important;
#         margin: 14px 0 !important;
#         border-radius: 6px;
#         color: #e2e8f0 !important;
#         font-style: italic;
#         line-height: 1.5;
#     }
    
#     /* Gradient Dividers for Product listings */
#     hr {
#         margin: 1.5rem 0 !important;
#         border: 0 !important;
#         height: 1px !important;
#         background-image: linear-gradient(to right, rgba(0, 173, 181, 0), rgba(0, 173, 181, 0.6), rgba(0, 173, 181, 0)) !important;
#     }
    
#     h3 {
#         color: #00adb5 !important;
#         font-weight: 600 !important;
#         font-size: 1.25rem !important;
#         margin-top: 18px !important;
#         margin-bottom: 8px !important;
#     }
    
#     /* Showroom grid cards */
#     .product-card {
#         background: linear-gradient(145deg, #1e293b, #0f172a);
#         border-radius: 12px;
#         padding: 16px;
#         border: 1px solid rgba(255, 255, 255, 0.05);
#         transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
#         height: 250px;
#         display: flex;
#         flex-direction: column;
#         justify-content: space-between;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#     }
    
#     .product-card:hover {
#         transform: translateY(-5px);
#         border-color: rgba(0, 173, 181, 0.5);
#         box-shadow: 0 12px 24px rgba(0, 173, 181, 0.15);
#     }
    
#     .product-name {
#         font-size: 1.05rem;
#         font-weight: 600;
#         color: #f8fafc;
#         margin-top: 4px;
#         overflow: hidden;
#         text-overflow: ellipsis;
#         white-space: nowrap;
#     }
    
#     .product-price {
#         font-size: 1.25rem;
#         font-weight: 700;
#         color: #00adb5;
#     }
    
#     .product-desc {
#         font-size: 0.88rem;
#         color: #94a3b8;
#         display: -webkit-box;
#         -webkit-line-clamp: 3;
#         -webkit-box-orient: vertical;
#         overflow: hidden;
#         text-overflow: ellipsis;
#         line-height: 1.4;
#         margin-bottom: 8px;
#     }
    
#     /* Receipt Order Items styling */
#     .order-item {
#         background-color: rgba(255, 255, 255, 0.02);
#         border-radius: 10px;
#         padding: 14px;
#         margin-bottom: 10px;
#         border-left: 4px solid #10b981;
#         border-top: 1px solid rgba(255, 255, 255, 0.04);
#         border-right: 1px solid rgba(255, 255, 255, 0.04);
#         border-bottom: 1px solid rgba(255, 255, 255, 0.04);
#     }
    
#     /* Streamlit overrides for premium dark-slate background */
#     .stApp {
#         background-color: #0b0f19;
#     }
    
#     /* Tables in markdown */
#     table {
#         width: 100% !important;
#         border-collapse: collapse !important;
#         margin: 15px 0 !important;
#         font-size: 0.9rem !important;
#     }
#     th {
#         background-color: rgba(0, 173, 181, 0.15) !important;
#         color: #00adb5 !important;
#         font-weight: 600 !important;
#         padding: 10px !important;
#         border-bottom: 2px solid rgba(0, 173, 181, 0.3) !important;
#         text-align: left !important;
#     }
#     td {
#         padding: 10px !important;
#         border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
#     }
    
#     /* Custom Scrollbars */
#     ::-webkit-scrollbar {
#         width: 6px;
#         height: 6px;
#     }
#     ::-webkit-scrollbar-track {
#         background: rgba(255, 255, 255, 0.02);
#     }
#     ::-webkit-scrollbar-thumb {
#         background: rgba(0, 173, 181, 0.3);
#         border-radius: 4px;
#     }
#     ::-webkit-scrollbar-thumb:hover {
#         background: rgba(0, 173, 181, 0.5);
#     }
#     </style>
#     """
# )

# ----------------- Session Init -----------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": '<i class="fa-solid fa-handshake" style="color: #ffb703; margin-right: 5px;"></i> Hello! I am a shop agent, your conversational shopping assistant. I can help you search the store, compare ratings, filter by organic, and place orders. What would you like to find today?'
        }
    ]

# ----------------- Dashboard Layout -----------------

# Layout columns: Left Column (Chat Area) and Right Column (Control Panel)
col_chat, col_showroom = st.columns([7, 5], gap="large")

# ==================== LEFT COLUMN: CHAT INTERFACE ====================
with col_chat:
    # App Title & Header
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background-color: #00adb5; padding: 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0, 173, 181, 0.4);">
                    <i class="fa-solid fa-robot" style="color: #ffffff; font-size: 26px;"></i>
                </div>
                <div>
                    <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #f8fafc; letter-spacing: -0.5px;">SHOP AGENT</h1>
                    <p style="margin: 0; font-size: 13px; color: #94a3b8;">Conversational AI Shopping Assistant</p>
                </div>
            </div>
            <div style="font-size: 0.8rem; color: #64748b; background-color: rgba(255,255,255,0.02); padding: 6px 12px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.04);">
                <i class="fa-solid fa-circle" style="color: #10b981; font-size: 8px; margin-right: 5px; vertical-align: middle;"></i> Active Session
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)
                
    # Chat input and execution flow
    if user_input := st.chat_input("Ask shop agent to search, describe, or order products..."):
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
                
        # Invoke Agent
        with st.chat_message("assistant"):
            with st.spinner("shop agent is thinking..."):
                try:
                    # Execute agent in venv context
                    res = agent_invoke(
                        [HumanMessage(content=user_input)], 
                        config={"configurable": {"thread_id": st.session_state.thread_id}}
                    )
                    
                    # Search backward for the last non-empty AIMessage text
                    final_msg = None
                    for m in reversed(res.get("messages", [])):
                        if isinstance(m, AIMessage) and extract_message_text(m).strip():
                            final_msg = m
                            break
                    
                    if final_msg:
                        response_text = extract_message_text(final_msg)
                    else:
                        response_text = "I processed your request, but did not generate a text response. Can I help you search for another product?"
                        
                    # Apply sanity emoji filter to ensure clean response
                    clean_response_text = clean_emojis(response_text)
                    
                except Exception as e:
                    clean_response_text = f'<i class="fa-solid fa-triangle-exclamation" style="color: #f44336; margin-right: 5px;"></i> I encountered an error running the assistant: {str(e)}'
                
                # Render Response
                st.markdown(clean_response_text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": clean_response_text})
                st.rerun()

# ==================== RIGHT COLUMN: CONTROL PANEL & SHOWROOM ====================
with col_showroom:
    # Sidebar control buttons inside the panel
    st.markdown(
        """
        <div style="margin-bottom: 15px;">
            <h2 style="margin: 0 0 5px 0; font-size: 20px; font-weight: 600; color: #f8fafc;">Control Center</h2>
            <p style="margin: 0; font-size: 13px; color: #94a3b8;">Browse items and check transaction summaries</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Tabs
    tab_showroom, tab_orders = st.tabs([
        " Showroom", 
        " Receipt History"
    ])
    
    # Fill Tab 1: Product Showroom
    with tab_showroom:
        # Search & Filter widgets
        col_s1, col_s2 = st.columns([3, 2])
        with col_s1:
            search_query = st.text_input(
                "Filter by keyword", 
                placeholder="honey, tea, organic...",
                label_visibility="collapsed"
            )
        with col_s2:
            categories_list = ["All Categories"] + get_categories()
            category = st.selectbox(
                "Category Selection",
                categories_list,
                label_visibility="collapsed"
            )
            
        # Advanced Collapsible Filters
        with st.expander(" Advanced Filters", expanded=False):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                min_p_bound, max_p_bound = get_db_price_bounds()
                price_range = st.slider(
                    "Price Range ($)",
                    min_value=min_p_bound,
                    max_value=max_p_bound,
                    value=(min_p_bound, max_p_bound),
                    step=0.5
                )
            with col_f2:
                min_rating = st.slider(
                    "Min Average Rating",
                    min_value=0.0,
                    max_value=5.0,
                    value=0.0,
                    step=0.5
                )
            organic_only = st.checkbox("Show Organic Products Only", value=False)
            
        # Fetch filtered products
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            sql_query = """
                SELECT p.id, p.name, p.category, p.price, p.description, p.is_organic, AVG(r.rating) as avg_rating 
                FROM products p 
                LEFT JOIN reviews r ON p.id = r.product_id 
                WHERE 1=1
            """
            params = []
            
            if search_query:
                sql_query += " AND (p.name LIKE ? OR p.description LIKE ?)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])
            if category != "All Categories":
                sql_query += " AND p.category = ?"
                params.append(category)
            if organic_only:
                sql_query += " AND p.is_organic = 1"
                
            sql_query += " AND p.price BETWEEN ? AND ?"
            params.extend([price_range[0], price_range[1]])
            
            sql_query += " GROUP BY p.id"
            
            if min_rating > 0:
                sql_query += " HAVING avg_rating >= ?"
                params.append(min_rating)
                
            sql_query += " ORDER BY avg_rating DESC, p.name ASC"
            
            cursor.execute(sql_query, params)
            products = cursor.fetchall()
            conn.close()
        except Exception as e:
            products = []
            st.error(f"Error fetching products: {str(e)}")
            
        # Display Grid
        if not products:
            st.markdown(
                """
                <div style="text-align: center; padding: 40px 10px; color: #64748b;">
                    <i class="fa-solid fa-magnifying-glass" style="font-size: 36px; margin-bottom: 10px; color: #475569;"></i>
                    <p style="margin: 0; font-size: 1rem; font-weight: 500;">No products match your criteria</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.82rem;">Try clearing the search query or loosening filter limits.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(f'<div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 10px;">Showing <b>{len(products)}</b> items found:</div>', unsafe_allow_html=True)
            
            # Display items in a two-column grid
            grid_cols = st.columns(2)
            for idx, item in enumerate(products):
                pid, name, cat, price, desc, organic, rating = item
                col_cell = grid_cols[idx % 2]
                
                # Rating stars generator
                stars_html = ""
                if rating is not None:
                    full_stars = int(rating)
                    half_star = 1 if rating - full_stars >= 0.5 else 0
                    empty_stars = 5 - full_stars - half_star
                    stars_html = (
                        '<i class="fa-solid fa-star" style="color: #ffb703; font-size: 0.8rem;"></i>' * full_stars +
                        '<i class="fa-solid fa-star-half-stroke" style="color: #ffb703; font-size: 0.8rem;"></i>' * half_star +
                        '<i class="fa-regular fa-star" style="color: #475569; font-size: 0.8rem;"></i>' * empty_stars
                    )
                    rating_str = f"{rating:.1f}"
                else:
                    stars_html = '<i class="fa-regular fa-star" style="color: #475569; font-size: 0.8rem;"></i>' * 5
                    rating_str = "No rating"
                    
                organic_badge = (
                    '<span style="background-color: rgba(16, 185, 129, 0.12); color: #10b981; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px; font-weight: 500; margin-left: 6px;">'
                    '<i class="fa-solid fa-leaf" style="font-size: 0.7rem; margin-right: 2px;"></i>Organic</span>' if organic else ""
                )
                
                with col_cell:
                    st.markdown(
                        f"""
                        <div class="product-card">
                            <div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: #00adb5; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{cat}</span>
                                    <span style="color: #475569; font-size: 0.7rem;">ID: #{pid}</span>
                                </div>
                                <div class="product-name" title="{name}">{name} {organic_badge}</div>
                                <div style="margin: 4px 0 8px 0; display: flex; align-items: center; gap: 4px;">
                                    {stars_html} <span style="font-size: 0.75rem; color: #64748b; margin-left: 2px;">({rating_str})</span>
                                </div>
                                <div class="product-desc">{desc}</div>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.05); margin-top: auto;">
                                <div class="product-price">${price:.2f}</div>
                                <div style="font-size: 0.75rem; color: #475569;">
                                    <i class="fa-solid fa-barcode"></i> UPC-{1000 + pid}
                                </div>
                            </div>
                        </div>
                        <div style="margin-bottom: 12px;"></div>
                        """,
                        unsafe_allow_html=True
                    )
                    
    # Fill Tab 2: Order Receipts History
    with tab_orders:
        orders = get_orders()
        
        # Summary KPI cards if orders exist
        if orders:
            total_spent = sum(order[4] for order in orders)
            total_items = sum(order[3] for order in orders)
            
            kpi_col1, kpi_col2 = st.columns(2)
            with kpi_col1:
                st.metric(label="Total Expenses", value=f"${total_spent:.2f}")
            with kpi_col2:
                st.metric(label="Units Ordered", value=total_items)
                
            st.markdown(
                """
                <div style="font-size: 0.85rem; color: #94a3b8; margin: 15px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">
                    <i class="fa-solid fa-receipt"></i> Placed Orders (DB records):
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Print list of orders
            for ord_row in orders:
                oid, pid, pname, qty, total, date = ord_row
                unit_price = total / qty if qty > 0 else 0
                
                st.markdown(
                    f"""
                    <div class="order-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600; color: #f1f5f9; font-size: 0.9rem;">{pname}</span>
                            <span style="font-weight: 700; color: #10b981; font-size: 1rem;">${total:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 0.78rem; color: #64748b;">
                            <span>Qty: {qty} &bull; Unit: ${unit_price:.2f}</span>
                            <span><i class="fa-solid fa-calendar-day" style="font-size: 0.75rem; margin-right: 3px;"></i> {date}</span>
                        </div>
                        <div style="font-size: 0.72rem; color: #475569; margin-top: 4px;">
                            Receipt Ref: REC-{oid:04d} &bull; Item Ref: #{pid}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div style="text-align: center; padding: 50px 20px; color: #64748b;">
                    <div style="font-size: 40px; margin-bottom: 12px; color: #334155;">
                        <i class="fa-solid fa-file-invoice-dollar"></i>
                    </div>
                    <p style="margin: 0; font-size: 1.05rem; font-weight: 500;">Receipt Drawer Empty</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.82rem;">Ask Shop agent to place an order, e.g.:<br><i>"I want to order 2 units of organic honey"</i></p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # General Action footer for clearing history
    st.markdown('<div style="margin-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("Reset Conversation Memory", use_container_width=True, type="secondary"):
        # Regenerate Thread ID for fresh Agent context
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": '<i class="fa-solid fa-arrows-spin" style="color: #00adb5; margin-right: 5px;"></i> Conversation thread reset! How can I help you find new products today?'
            }
        ]
        st.rerun()
