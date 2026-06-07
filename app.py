import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection, execute_query

# --- [1] 페이지 기본 세팅 ---
st.set_page_config(page_title="My Private Diary", page_icon="📝", layout="centered")

# --- [2] Supabase DB 연결 ---
st_supabase = st.connection(
    name="supabase",
    type=SupabaseConnection,
    url=st.secrets["supabase"]["SUPABASE_URL"],
    key=st.secrets["supabase"]["SUPABASE_KEY"]
)

# --- [3] DB에서 유저 정보 불러오기 함수 ---
def fetch_users():
    try:
        res = execute_query(st_supabase.table("users").select("*"))
        credentials = {"usernames": {}}
        if res.data:
            for user in res.data:
                credentials["usernames"][user["username"]] = {
                    "email": user["email"],
                    "name": user["name"],
                    "password": user["password"]  # DB에 저장된 해시 비밀번호
                }
        return credentials
    except Exception as e:
        # 안전장치: 테이블이 비어있거나 에러 날 때 기본 계정 제공
        return {"usernames": {"admin": {"email": "admin@a.com", "name": "Tiger", "password": "1234"}}}

credentials = fetch_users()

# --- [4] 로그인 시스템 설정 (v0.2.3 규격) ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="diary_session",
    key="secret_signature_key",
    cookie_expiry_days=7
)

# 화면 인터페이스 분리 (탭 사용)
tab1, tab2 = st.tabs(["🔒 로그인", "✍️ 회원가입"])

with tab1:
    # 0.2.3 버전의 올바른 로그인 호출 및 변수 할당 방식
    name, authentication_status, username = authenticator.login('로그인', 'main')

with tab2:
    st.subheader("새 계정 만들기")
    new_email = st.text_input("이메일", key="reg_email")
    new_username = st.text_input("아이디(ID)", key="reg_id")
    new_name = st.text_input("이름(닉네임)", key="reg_name")
    new_password = st.text_input("비밀번호", type="password", key="reg_pw")
    
    if st.button("가입하기", type="secondary"):
        if new_email and new_username and new_name and new_password:
            if new_username in credentials["usernames"]:
                st.error("이미 존재하는 아이디입니다.")
            else:
                # 0.2.3 버전 라이브러리가 가장 찰떡같이 인식하는 암호화(Hasher) 구문입니다.
                hashed_password = stauth.Hasher([new_password]).generate()[0]
                
                new_user = {
                    "username": new_username,
                    "email": new_email,
                    "name": new_name,
                    "password": hashed_password
                }
                
                # Supabase DB에 유저 삽입
                execute_query(st_supabase.table("users").insert(new_user))
                st.success("회원가입이 완료되었습니다! 로그인 탭으로 이동해 접속하세요.")
                st.balloons()
                st.utility.rerun() if hasattr(st, "utility") else st.rerun()
        else:
            st.warning("모든 항목을 입력해 주세요.")

# --- [5] 화면 렌더링 분기 ---
if authentication_status == False:
    st.error("아이디 또는 비밀번호가 올바르지 않습니다. 다시 확인해 주세요.")

elif authentication_status == None:
    st.info("단단한 기록 공간에 오신 것을 환영합니다. 서비스를 이용하려면 로그인해 주세요.")

elif authentication_status:
    # 로그인 성공 시 대시보드 열림
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"✨ {name}님의 단단한 기록 공간")
    with col2:
        authenticator.logout("로그아웃", "main")
        
    st.divider()

    # 일기 쓰기 영역
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
            execute_query(st_supabase.table("diaries").insert(row))
            st.success("클라우드 데이터베이스에 실시간 동기화되었습니다!")
        else:
            st.warning("제목과 내용을 모두 입력해 주세요.")

    st.divider()
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
        st.error("데이터를 불러오는 중 오류가 발생했습니다.")
