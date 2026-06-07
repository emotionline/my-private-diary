import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection, execute_query

# --- [1] 페이지 기본 세팅 ---
st.set_page_config(page_title="My Private Diary", page_icon="📝", layout="centered")

# --- [2] Supabase DB 연결 (Secrets 경로 수정 반영) ---
st_supabase = st.connection(
    name="supabase",
    type=SupabaseConnection,
    url=st.secrets["supabase"]["SUPABASE_URL"],  # ["supabase"] 그룹 추가!
    key=st.secrets["supabase"]["SUPABASE_KEY"]   # ["supabase"] 그룹 추가!
)

# --- [3] 로그인 시스템 세팅 ---
# 초기 테스트용 계정 (ID: admin / PW: 1234)
credentials = {
    "usernames": {
        "admin": {
            "email": "admin@example.com",
            "name": "Tiger Focus",
            "password": "1234"  
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="diary_session",
    key="secret_signature_key",
    cookie_expiry_days=7
)

name, authentication_status, username = authenticator.login()

# --- [4] 화면 렌더링 분기 ---
if authentication_status == False:
    st.error("비밀번호가 올바르지 않습니다.")

elif authentication_status == None:
    st.warning("로그인이 필요합니다. 아이디(admin)와 비밀번호(1234)를 입력해주세요.")

elif authentication_status:
    # 로그인 성공 시 대시보드 진입
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"✨ {name}님의 단단한 기록 공간")
    with col2:
        authenticator.logout("로그아웃", "main")
        
    st.divider()

    # 인터페이스 1: 일기 쓰기
    st.title("📝 오늘의 기록")
    diary_date = st.date_input("날짜 선택")
    diary_title = st.text_input("제목", placeholder="오늘을 관통하는 한 마디")
    diary_content = st.text_area("내용", placeholder="생각과 감정을 차분히 정돈해 보세요.", height=250)

    if st.button("일기 저장하기", type="primary"):
        if diary_title and diary_content:
            row = {
                "username": username,
                "diary_date": str(diary_date),
                "title": diary_title,
                "content": diary_content
            }
            # Supabase에 실시간 insert
            execute_query(st_supabase.table("diaries").insert(row))
            st.success("클라우드 데이터베이스에 동기화되었습니다!")
            st.balloons()
        else:
            st.warning("제목과 내용을 모두 입력해 주세요.")

    st.divider()

    # 인터페이스 2: 일기 피드 불러오기 (PC/모바일 실시간 연동 확인용)
    st.subheader("📂 지난 기록 들여다보기")
    
    try:
        response = execute_query(
            st_supabase.table("diaries")
            .select("*")
            .eq("username", username)
            .order("diary_date", desc=True)
        )
        
        if response.data:
            for diary in response.data:
                with st.expander(f"📅 {diary['diary_date']} | {diary['title']}"):
                    st.write(diary['content'])
        else:
            st.info("아직 저장된 일기가 없습니다. 첫 기록을 남겨보세요!")
    except Exception as e:
        st.error("데이터를 불러오는 중 오류가 발생했습니다. DB 설정을 확인해 주세요.")
