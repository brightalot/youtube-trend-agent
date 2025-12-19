import streamlit as st
import requests
import pandas as pd
import time
import os

# Backend URL (Docker service name 'backend')
# When running locally outside docker, use localhost:8000
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="YouTube Trend Agent", layout="wide")

st.title("🚀 YouTube Trend Agent")
st.markdown("---")

# 1. Input Section
st.subheader("1. 분석 요청 (Analysis Request)")
focus_point = st.text_input(
    "분석 집중 포인트 (Focus Point)",
    placeholder="예: 20대 여성이 좋아할 만한 뷰티 쇼츠 트렌드 알려줘"
)

if st.button("트렌드 수집 및 분석 시작 (Start Analysis)"):
    if not focus_point:
        st.warning("분석 포인트를 입력해주세요.")
    else:
        with st.spinner("요청을 백엔드로 전송 중입니다..."):
            try:
                response = requests.post(f"{BACKEND_URL}/run-analysis", json={"focus_point": focus_point})
                if response.status_code == 200:
                    st.success("✅ 분석 요청이 성공적으로 시작되었습니다! 잠시 후 결과를 확인해주세요.")
                else:
                    st.error(f"요청 실패: {response.text}")
            except Exception as e:
                st.error(f"백엔드 연결 오류 (Docker 연결 확인 필요): {e}")

st.markdown("---")

# 2. Results Section
st.subheader("2. 분석 결과 (Results)")

if st.button("결과 새로고침 (Refresh Results)"):
    with st.spinner("데이터를 불러오는 중..."):
        try:
            response = requests.get(f"{BACKEND_URL}/get-results")
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    st.success(f"총 {len(data)}건의 데이터를 불러왔습니다.")
                else:
                    st.info("아직 분석 결과가 없습니다. 잠시 후 다시 시도해주세요.")
            else:
                st.error(f"결과 로드 실패: {response.text}")
        except Exception as e:
            st.error(f"백엔드 연결 오류: {e}")
