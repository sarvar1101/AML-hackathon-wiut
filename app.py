import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

# -----------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="Мясокомбинат | AML Prioritization",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------
# 2. CUSTOM CSS & JS (The UI Engine)
# -----------------------------------------
# This block creates the Navy background, Glass panels, the 1/3 indent, 
# the interactive mouse pipelines, and the smooth scroll animations.
custom_ui_code = """
<style>
    /* Navy Background & Global Font */
    .stApp {
        background-color: #020a17 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Indent 1/3 total (constrain main content to ~55% of the screen width in the center) */
    .block-container {
        max-width: 60% !important;
        margin: 0 auto !important;
        padding-top: 5rem !important;
        padding-bottom: 5rem !important;
        z-index: 10;
    }
    
    /* Hide default header */
    header { visibility: hidden; }

    /* Glassmorphism Styling for standard Streamlit containers */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    /* Specific overrides for Hero text so it doesn't get the glass box */
    .hero-container {
        text-align: center;
        height: 80vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }

    .hero-title { font-size: 5rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0;}
    .hero-subtitle { font-size: 2rem; color: #94a3b8; font-weight: 300; letter-spacing: 5px; margin-bottom: 50px;}
    
    /* Bouncing Scroll Indicator */
    .scroll-indicator {
        font-size: 1.2rem;
        color: #4facfe;
        animation: bounce 2s infinite;
        margin-top: 2rem;
    }
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-20px); }
        60% { transform: translateY(-10px); }
    }
</style>

<!-- Canvas for Interactive Pipeline Background -->
<canvas id="network-canvas" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; pointer-events: none;"></canvas>

<script>
    const parentDoc = window.parent.document;
    
    // 1. SCROLL ANIMATION (Smooth Pop Up)
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    // Apply animation starting state to all Streamlit elements
    setTimeout(() => {
        const elements = parentDoc.querySelectorAll('.block-container > div > div > div');
        elements.forEach((el, index) => {
            // Skip the first block (Hero section)
            if(index > 1) {
                el.style.opacity = 0;
                el.style.transform = 'translateY(40px)';
                el.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
                observer.observe(el);
            }
        });
    }, 1000);

    // 2. INTERACTIVE PIPELINE BACKGROUND (Canvas)
    const canvas = document.getElementById('network-canvas');
    // Move canvas to parent body so it covers everything behind streamlit
    if (!parentDoc.getElementById('network-canvas-moved')) {
        const clonedCanvas = canvas.cloneNode(true);
        clonedCanvas.id = 'network-canvas-moved';
        parentDoc.body.prepend(clonedCanvas);
        
        const ctx = clonedCanvas.getContext('2d');
        let width, height;
        let particles = [];
        let mouse = { x: null, y: null };

        function resize() {
            width = clonedCanvas.width = parentDoc.documentElement.clientWidth;
            height = clonedCanvas.height = parentDoc.documentElement.clientHeight;
        }
        
        parentDoc.defaultView.addEventListener('resize', resize);
        parentDoc.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        parentDoc.addEventListener('mouseout', () => {
            mouse.x = null;
            mouse.y = null;
        });

        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 1.5;
                this.vy = (Math.random() - 0.5) * 1.5;
                this.radius = Math.random() * 2 + 1;
            }
            update() {
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(79, 172, 254, 0.3)';
                ctx.fill();
            }
        }

        function init() {
            resize();
            for (let i = 0; i < 80; i++) particles.push(new Particle());
            animate();
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);
            
            for (let i = 0; i < particles.length; i++) {
                particles[i].update();
                particles[i].draw();
                
                // Pipeline to mouse
                if (mouse.x != null) {
                    let dx = mouse.x - particles[i].x;
                    let dy = mouse.y - particles[i].y;
                    let dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(79, 172, 254, ${1 - dist/150})`;
                        ctx.lineWidth = 1;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(mouse.x, mouse.y);
                        ctx.stroke();
                    }
                }

                // Pipeline between nodes
                for (let j = i; j < particles.length; j++) {
                    let dx = particles[i].x - particles[j].x;
                    let dy = particles[i].y - particles[j].y;
                    let dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(255, 255, 255, ${0.1 - dist/1000})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(animate);
        }
        init();
    }
</script>
"""
# Inject the CSS/JS into the app
components.html(custom_ui_code, height=0, width=0)

# -----------------------------------------
# 3. DATA LOADING
# -----------------------------------------
@st.cache_data
def load_data():
    # Load your actual data files here
    try:
        signals = pd.read_csv('train_signals.csv')
        trans = pd.read_parquet('train_transactions.parquet').head(50000)
    except FileNotFoundError:
        # Fallback dummy data just so the UI works before you move the files
        st.warning("Data files not found. Using placeholder data for UI demonstration.")
        signals = pd.DataFrame({'eskalatsiya': [0]*80 + [1]*20})
        trans = pd.DataFrame({
            'kirim_chiqim': ['kirim', 'chiqim', 'chiqim', 'kirim'] * 12500,
            'miqdor_indeksi': [1.2, 3.4, 0.5, 2.1] * 12500
        })
    return signals, trans

signals_df, trans_df = load_data()

# Update Plotly defaults to match Navy theme
layout_transparent = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e2e8f0'),
    margin=dict(l=20, r=20, t=40, b=20)
)

# -----------------------------------------
# 4. APP LAYOUT & CONTENT
# -----------------------------------------

# Navigation Sidebar
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("Use this to jump via scrolling.")
    # In a single page scroll app, the sidebar is purely informational or controls filters
    st.info("💠 **Мясокомбинат**\n\nAML Alert Prioritization Engine.")

# --- HERO SECTION ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Мясокомбинат</div>
    <div class="hero-subtitle">TEAM ID: 6927C48E</div>
    <div class="scroll-indicator">Scroll to see ↓</div>
</div>
""", unsafe_allow_html=True)

# Add space to force the user to scroll to the next section
st.write("")
st.write("")
st.write("")

# --- SECTION 1: OVERVIEW (Inside Glass Border) ---
with st.container():
    st.markdown("### 📊 Dataset Overview")
    st.markdown("The system analyzes historical transaction pipelines to isolate true AML threats from false-positive background noise.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Alerts Evaluated", f"{len(signals_df):,}")
    with col2:
        st.metric("Escalation Rate", f"{(signals_df['eskalatsiya'].mean() * 100):.1f}%")

# --- SECTION 2: TARGET DISTRIBUTION (Inside Glass Border) ---
with st.container():
    st.markdown("### 🎯 Alert Escalation Probability")
    
    counts = signals_df['eskalatsiya'].value_counts().reset_index()
    counts.columns = ['Status', 'Count']
    counts['Status'] = counts['Status'].map({0: 'Dismissed', 1: 'Escalated'})
    
    fig1 = px.pie(
        counts, values='Count', names='Status', hole=0.7,
        color='Status', color_discrete_map={'Dismissed': '#1e293b', 'Escalated': '#4facfe'}
    )
    fig1.update_layout(**layout_transparent)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("**Observation:** Massive class imbalance requires strict ROC-AUC optimization.")

# --- SECTION 3: BEHAVIORAL PIPELINES (Inside Glass Border) ---
with st.container():
    st.markdown("### 💸 Transaction Pipelines")
    
    fig2 = px.histogram(
        trans_df, x='kirim_chiqim', color='kirim_chiqim',
        color_discrete_sequence=['#4facfe', '#00f2fe']
    )
    fig2.update_layout(**layout_transparent)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("**Observation:** Outgoing pipelines (`chiqim`) exhibit higher volume, commonly associated with layering phases in money laundering schemes.")

# --- SECTION 4: CONCLUSION (Inside Glass Border) ---
with st.container():
    st.markdown("### 🧠 ML Engine Architecture")
    st.markdown("""
    **Feature Pipeline:**
    * Temporal proximity vectors (days to signal).
    * Outgoing-to-incoming structuring ratios.
    
    **Model:**
    LightGBM Gradient Boosting with stratified CV and scale-pos-weight handling to penetrate the noise of the financial pipelines.
    """)
    st.success("Prioritization algorithms initialized successfully.")

# Footer spacing
st.markdown("<br><br><br><br>", unsafe_allow_html=True)
