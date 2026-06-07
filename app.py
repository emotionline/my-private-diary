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
        # ttl=0 으로 실시간 동기화 강제
        res = execute_query(st_supabase.table("users").select("*"), ttl=0)
        credentials = {"usernames": {}}
        if res.data:
            for user in res.data:
                credentials["usernames"][user["username"]] = {
                    "email": user["email"],
                    "name": user["name"],
                    "password": str(user["password"])  # 확실하게 문자열로 변환
                }
        return credentials
    except Exception as e:
        return {"usernames": {}}

credentials = fetch_users()

# --- [4] 로그인 시스템 설정 (v0.2.3 공식 규격) ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="diary_session",
    key="secret_signature_key",
    cookie_expiry_days=7
)

tab1, tab2 = st.tabs(["🔒 로그인", "✍️ 회원가입"])

with tab1:
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
                # 0.2.3 버전에서 오류 없이 매칭되는 해시화 정석 문법입니다.
                hashed_passwords = stauth.Hasher([new_password]).encoded_passwords
                hashed_password = hashed_passwords[0]
                
                new_user = {
                    "username": new_username,
                    "email": new_email,
                    "name": new_name,
                    "password": hashed_password
                }
                
                # Supabase DB에 유저 삽입
                execute_query(st_supabase.table("users").insert(new_user))
                st.success("회원가입이 완료되었습니다! 로그인 탭에서 접속하세요.")
                st.balloons()
                st.rerun()
        else:
            st.warning("모든 항목을 입력해 주세요.")

# --- [5] 화면 렌더링 분기 ---
if authentication_status == False:
    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

elif authentication_status == None:
    st.info("로그인이 필요합니다. 기존 계정으로 로그인하거나 새로 가입해 주세요.")

elif authentication_status:
    # 로그인 성공 시 일기장 대시보드 진입
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"✨ {name}님의 단단한 기록 공간")
    with col2:
        authenticator.logout("로그아웃", "main")
        
    st.divider()

    # 일기 작성 영역
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
            st.rerun()
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
