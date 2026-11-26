import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="5D BIM Executive Dashboard | PEA Academy",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def parse_revit_boq_csv(file_source, kind: str) -> pd.DataFrame:
    """อ่านและแปลงไฟล์ CSV ที่ Export จาก Revit Schedule (รองรับเครื่องหมาย ฿ และลูกน้ำในตัวเลขเงิน)"""
    if isinstance(file_source, str):
        with open(file_source, "r", encoding="utf-8-sig") as f:
            raw_text = f.read()
    else:
        raw_bytes = file_source.getvalue()
        raw_text = raw_bytes.decode("utf-8-sig", errors="replace")

    lines = [line.rstrip("\r\n") for line in raw_text.splitlines()]
    records = []

    for line in lines[2:]:
        stripped = line.strip()
        if not stripped or set(stripped) == {","}:
            continue
        if stripped.startswith("Grand total"):
            continue

        parts = line.split(",")
        if kind == "piping" and len(parts) >= 6:
            building = parts[0].strip()
            room = parts[1].strip()
            length = float(parts[2].strip())
            diameter = parts[3].strip()
            unit_raw = parts[4].strip()
            total_str = ",".join(parts[5:]).replace("฿", "").replace(",", "").strip()
            total_price = float(total_str)
            unit_price = (
                round(total_price / length, 2)
                if unit_raw == "<varies>" and length > 0
                else float(unit_raw)
            )
            records.append(
                {
                    "โครงการ": "โครงการอาคารสถาบันวิชาการ (PEA Academy)",
                    "อาคาร": building,
                    "ชั้น": "ชั้น 1 (FL.01)",
                    "ระบบงาน": "ระบบดับเพลิง (Fire Protection)",
                    "หมวดวัสดุ": "ท่อ (Piping)",
                    "รายการ": f"ท่อเหล็กดำ Sch.40 ({diameter})",
                    "ขนาด": diameter,
                    "ห้อง": room,
                    "ปริมาณ": length,
                    "หน่วย": "เมตร",
                    "ราคาต่อหน่วย": unit_price,
                    "ราคารวม": total_price,
                }
            )
        elif kind == "fitting" and len(parts) >= 7:
            building = parts[0].strip()
            room = parts[1].strip()
            desc = parts[2].strip()
            size = parts[3].strip()
            qty = int(float(parts[4].strip()))
            unit_raw = parts[5].strip()
            total_str = ",".join(parts[6:]).replace("฿", "").replace(",", "").strip()
            total_price = float(total_str)
            unit_price = (
                round(total_price / qty, 2)
                if unit_raw == "<varies>" and qty > 0
                else float(unit_raw)
            )
            records.append(
                {
                    "โครงการ": "โครงการอาคารสถาบันวิชาการ (PEA Academy)",
                    "อาคาร": building,
                    "ชั้น": "ชั้น 1 (FL.01)",
                    "ระบบงาน": "ระบบดับเพลิง (Fire Protection)",
                    "หมวดวัสดุ": "ข้อต่อ (Fitting)",
                    "รายการ": desc,
                    "ขนาด": size,
                    "ห้อง": room,
                    "ปริมาณ": float(qty),
                    "หน่วย": "ชิ้น",
                    "ราคาต่อหน่วย": unit_price,
                    "ราคารวม": total_price,
                }
            )

    return pd.DataFrame(records)


@st.cache_data
def load_default_data() -> pd.DataFrame:
    df_pipe = parse_revit_boq_csv("BOQ_Piping.csv", "piping")
    df_fit = parse_revit_boq_csv("BOQ_Fitting.csv", "fitting")
    return pd.concat([df_pipe, df_fit], ignore_index=True)


def expand_to_21_floors_mockup(df_base: pd.DataFrame) -> pd.DataFrame:
    """จำลองข้อมูล 21 ชั้นจากต้นแบบชั้น 1 สำหรับพรีเซนต์ภาพรวมโครงการให้ผู้บริหาร"""
    frames = []
    for floor_num in range(1, 22):
        df_floor = df_base.copy()
        df_floor["ชั้น"] = f"ชั้น {floor_num} (FL.{floor_num:02d})"
        # ชั้น 2-21 ปรับสัดส่วนพื้นที่สำนักงานมาตรฐาน (ตัดโซนโรงอาหารชั้น 1 ออกเพื่อความสมจริง)
        if floor_num > 1:
            df_floor = df_floor[df_floor["ห้อง"] != "โรงอาหาร"].copy()
        frames.append(df_floor)
    return pd.concat(frames, ignore_index=True)


# --- Header ---
st.title("🏗️ 5D BIM Executive Material & Cost Dashboard")
st.caption(
    "ระบบติดตามปริมาณวัสดุและงบประมาณประมาณการจากโมเดล Revit (BIM Data-Driven BOQ) | สำหรับ Director และ Project Manager"
)

# --- Sidebar: Data Source & Filters ---
with st.sidebar:
    st.header("📂 แหล่งข้อมูลจาก Revit")
    uploaded_pipe = st.file_uploader(
        "อัปโหลด BOQ_Piping.csv (ถ้ามีไฟล์ใหม่)", type=["csv"]
    )
    uploaded_fit = st.file_uploader(
        "อัปโหลด BOQ_Fitting.csv (ถ้ามีไฟล์ใหม่)", type=["csv"]
    )

    if uploaded_pipe is not None or uploaded_fit is not None:
        df_p = (
            parse_revit_boq_csv(uploaded_pipe, "piping")
            if uploaded_pipe
            else parse_revit_boq_csv("BOQ_Piping.csv", "piping")
        )
        df_f = (
            parse_revit_boq_csv(uploaded_fit, "fitting")
            if uploaded_fit
            else parse_revit_boq_csv("BOQ_Fitting.csv", "fitting")
        )
        df_raw = pd.concat([df_p, df_f], ignore_index=True)
    else:
        df_raw = load_default_data()

    st.divider()
    st.header("🎛️ ตัวกรองข้อมูล (Filters)")

    mockup_21 = st.toggle(
        "จำลองข้อมูลครบ 21 ชั้น (Mockup Presentation)",
        value=False,
        help="เปิดเพื่อจำลองปริมาณงานและงบประมาณทั้ง 21 ชั้นจากชุดข้อมูลต้นแบบชั้น 1",
    )
    df = expand_to_21_floors_mockup(df_raw) if mockup_21 else df_raw.copy()

    projects = ["ทั้งหมด"] + sorted(df["โครงการ"].unique().tolist())
    sel_project = st.selectbox("โครงการ (Project)", projects)
    if sel_project != "ทั้งหมด":
        df = df[df["โครงการ"] == sel_project]

    buildings = ["ทั้งหมด"] + sorted(df["อาคาร"].unique().tolist())
    sel_building = st.selectbox("อาคาร (Building)", buildings)
    if sel_building != "ทั้งหมด":
        df = df[df["อาคาร"] == sel_building]

    floors = ["ทั้งหมด"] + list(dict.fromkeys(df["ชั้น"].tolist()))
    sel_floor = st.selectbox("ชั้น (Level)", floors)
    if sel_floor != "ทั้งหมด":
        df = df[df["ชั้น"] == sel_floor]

    systems = ["ทั้งหมด"] + sorted(df["ระบบงาน"].unique().tolist())
    sel_system = st.selectbox("ระบบงาน (Discipline)", systems)
    if sel_system != "ทั้งหมด":
        df = df[df["ระบบงาน"] == sel_system]

    categories = sorted(df["หมวดวัสดุ"].unique().tolist())
    sel_categories = st.multiselect(
        "หมวดวัสดุ (Category)", categories, default=categories
    )
    df = df[df["หมวดวัสดุ"].isin(sel_categories)]

    rooms = ["ทั้งหมด"] + sorted(df["ห้อง"].unique().tolist())
    sel_room = st.selectbox("ห้อง / โซน (Room)", rooms)
    if sel_room != "ทั้งหมด":
        df = df[df["ห้อง"] == sel_room]

    st.divider()
    st.header("⚙️ ตั้งค่าประมาณการราคา")
    waste_pct = st.slider(
        "เผื่อวัสดุสิ้นเปลือง / Waste (%)",
        min_value=0,
        max_value=20,
        value=0,
        step=5,
        help="แนะนำ 10% - 15% สำหรับลวดเชื่อม แก๊ส สีกันสนิม และเศษตัดท่อ (ยังไม่รวม VAT และค่าแรง)",
    )

if df.empty:
    st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก กรุณาปรับตัวกรองด้านซ้ายมือ")
    st.stop()

# Apply waste factor
multiplier = 1 + (waste_pct / 100.0)
df["ราคารวมสุทธิ"] = df["ราคารวม"] * multiplier

# --- KPI Metrics ---
total_cost = df["ราคารวมสุทธิ"].sum()
pipe_df = df[df["หมวดวัสดุ"] == "ท่อ (Piping)"]
fit_df = df[df["หมวดวัสดุ"] == "ข้อต่อ (Fitting)"]

pipe_cost = pipe_df["ราคารวมสุทธิ"].sum()
pipe_len = pipe_df["ปริมาณ"].sum()

fit_cost = fit_df["ราคารวมสุทธิ"].sum()
fit_qty = int(fit_df["ปริมาณ"].sum())

room_count = df["ห้อง"].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    label=f"งบประมาณวัสดุรวม {'(เผื่อ Waste ' + str(waste_pct) + '%)' if waste_pct > 0 else '(สุทธิจากแบบ)'}",
    value=f"฿{total_cost:,.2f}",
    delta=f"+฿{(total_cost - df['ราคารวม'].sum()):,.2f} Waste" if waste_pct > 0 else "ไม่รวม VAT และค่าแรง",
)
col2.metric(
    label="มูลค่างานท่อเหล็กดำ (Piping)",
    value=f"฿{pipe_cost:,.2f}",
    delta=f"ความยาวรวม {pipe_len:,.2f} เมตร",
)
col3.metric(
    label="มูลค่างานข้อต่อ (Fittings)",
    value=f"฿{fit_cost:,.2f}",
    delta=f"จำนวนรวม {fit_qty:,} ชิ้น",
)
col4.metric(
    label="พื้นที่ครอบคลุมในตัวกรอง",
    value=f"{room_count} ห้อง / โซน",
    delta=f"{len(df):,} รายการย่อย",
)

st.divider()

# --- Charts Section ---
chart_col1, chart_col2 = st.columns([1.35, 1])

with chart_col1:
    st.subheader("📊 งบประมาณวัสดุแยกตามห้อง / โซน (Top 10)")
    room_group = (
        df.groupby(["ห้อง", "หมวดวัสดุ"], as_index=False)["ราคารวมสุทธิ"]
        .sum()
    )
    top_rooms = (
        room_group.groupby("ห้อง")["ราคารวมสุทธิ"]
        .sum()
        .nlargest(10)
        .index.tolist()
    )
    room_top_df = room_group[room_group["ห้อง"].isin(top_rooms)].copy()
    room_order = (
        room_top_df.groupby("ห้อง")["ราคารวมสุทธิ"]
        .sum()
        .sort_values(ascending=True)
        .index.tolist()
    )
    fig_room = px.bar(
        room_top_df,
        x="ราคารวมสุทธิ",
        y="ห้อง",
        color="หมวดวัสดุ",
        orientation="h",
        category_orders={"ห้อง": room_order},
        labels={"ราคารวมสุทธิ": "มูลค่า (บาท)", "ห้อง": "ห้อง / โซน", "หมวดวัสดุ": "หมวดหมู่"},
        color_discrete_map={
            "ท่อ (Piping)": "#1E40AF",
            "ข้อต่อ (Fitting)": "#0D9488",
        },
        text_auto=",.0f",
    )
    fig_room.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_room, use_container_width=True)

with chart_col2:
    st.subheader("🥧 สัดส่วนงบประมาณแยกตามรายการวัสดุ")
    item_group = (
        df.groupby(["หมวดวัสดุ", "รายการ"], as_index=False)["ราคารวมสุทธิ"]
        .sum()
        .sort_values("ราคารวมสุทธิ", ascending=False)
    )
    fig_item = px.pie(
        item_group,
        values="ราคารวมสุทธิ",
        names="รายการ",
        hole=0.45,
        labels={"ราคารวมสุทธิ": "มูลค่า (บาท)", "รายการ": "รายการวัสดุ"},
    )
    fig_item.update_traces(textposition="inside", textinfo="percent+label")
    fig_item.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_item, use_container_width=True)

st.divider()

# --- Summary Table & Export ---
tab1, tab2 = st.tabs(["📋 ตารางสรุปรวมตามรายการวัสดุ (BOQ Summary)", "🔍 ตารางรายละเอียดแยกตามห้อง (Detailed List)"])

with tab1:
    summary_table = (
        df.groupby(["หมวดวัสดุ", "รายการ", "ขนาด", "หน่วย"], as_index=False)
        .agg(
            ปริมาณรวม=("ปริมาณ", "sum"),
            ราคาต่อหน่วยเฉลี่ย=("ราคาต่อหน่วย", "mean"),
            ราคารวมสุทธิ=("ราคารวมสุทธิ", "sum"),
        )
        .sort_values(["หมวดวัสดุ", "ราคารวมสุทธิ"], ascending=[True, False])
    )
    st.dataframe(
        summary_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ปริมาณรวม": st.column_config.NumberColumn("ปริมาณรวม", format="%.2f"),
            "ราคาต่อหน่วยเฉลี่ย": st.column_config.NumberColumn("ราคาต่อหน่วย (บาท)", format="฿%.2f"),
            "ราคารวมสุทธิ": st.column_config.NumberColumn("ราคารวม (บาท)", format="฿%,.2f"),
        },
    )

with tab2:
    display_cols = ["อาคาร", "ชั้น", "ห้อง", "หมวดวัสดุ", "รายการ", "ขนาด", "ปริมาณ", "หน่วย", "ราคาต่อหน่วย", "ราคารวมสุทธิ"]
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "ปริมาณ": st.column_config.NumberColumn("ปริมาณ", format="%.2f"),
            "ราคาต่อหน่วย": st.column_config.NumberColumn("ราคาต่อหน่วย (บาท)", format="฿%.2f"),
            "ราคารวมสุทธิ": st.column_config.NumberColumn("ราคารวม (บาท)", format="฿%,.2f"),
        },
    )

# Download CSV Button
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️ ดาวน์โหลดรายงาน BOQ ชุดนี้เป็นไฟล์ CSV (สำหรับ Excel / จัดซื้อ)",
    data=csv_buffer.getvalue().encode("utf-8-sig"),
    file_name="5D_BIM_BOQ_Export.csv",
    mime="text/csv",
)
