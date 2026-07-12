import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="광운대 수강신청 추천", page_icon="📚")

@st.cache_resource
def get_session() -> requests.Session:
    return requests.Session()

@st.cache_data
def load_departments() -> list[str]:
    resp = get_session().get(f"{BACKEND_URL}/departments", timeout=5)
    resp.raise_for_status()
    return resp.json()

st.title("📚 광운대 수강신청 추천")
st.caption("2026학년도 1학기 - 학과/학년/학점을 입력하면 시간표를 생성해드려요.")

try:
    departments = load_departments()
except Exception as e:
    st.error(f"백엔드({BACKEND_URL})에 연결할 수 없습니다: {e}")
    st.stop()

with st.form("recommend_form"):
    department = st.selectbox("학과", departments)
    grade = st.selectbox("학년", [1, 2, 3, 4, 5])
    target_credits = st.slider("수강신청 학점", min_value=12, max_value=22, value=18)
    prefer_remote = st.toggle("원격수업 우선 담기", value=False, help="후보 중 원격수업을 우선적으로 채웁니다.")
    prefer_required = st.toggle("전필 우선 담기", value=False, help="후보 중 전공필수 과목을 우선적으로 채웁니다.")
    submitted = st.form_submit_button("추천받기", type="primary", use_container_width=True)

if submitted:
    payload = {
        "department": department,
        "grade": grade,
        "target_credits": target_credits,
        "prefer_remote": prefer_remote,
        "prefer_required": prefer_required,
    }
    try:
        resp = get_session().post(f"{BACKEND_URL}/recommend", json=payload, timeout=10)
        resp.raise_for_status()
        st.session_state["result"] = resp.json()
    except Exception as e:
        st.error(f"추천 요청에 실패했습니다: {e}")

result = st.session_state.get("result")
if result:
    st.subheader(f"{result['department']} {result['grade']}학년 추천 결과")
    st.metric("추천 학점", f"{result['total_credits']} / {result['target_credits']}학점")
    st.info(result["message"])

    if result["courses"]:
        df = pd.DataFrame(result["courses"])[
            ["course_name", "course_code", "category", "course_type", "credits",
             "professor", "class_time", "section", "remarks"]
        ]
        df.columns = ["과목명", "학정번호", "구분", "이수구분", "학점",
                      "담당교수", "강의시간", "분반", "비고"]
        df = df.fillna("-")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("추천할 수 있는 과목이 없습니다.")
