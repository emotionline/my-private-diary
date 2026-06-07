import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection, execute_query

# --- [1] 페이지 설정 ---
st.set_page_config(page_title="My Web Diary", page_icon="📝", layout="centered")

# --- [2] DB 연결 ---
st_supabase = st.connection(
    name="supabase",
    type=SupabaseConnection,
    url=st.secrets["supabase"]["SUPABASE_URL"],
    key=st.secrets["supabase"]["SUPABASE_KEY"]
)

# --- [3] DB에서 유저 정보 불러오기 함수 ---
def fetch_users():
    res = execute_query(st_supabase.table("users").select("*"))
    credentials = {"usernames": {}}
    for user in res.data:
        credentials["usernames"][user["username"]] = {
            "email": user["email"],
            "name": user["name"],
            "password": user["password"]
        }
    return credentials

# 현재 DB에 있는 유저들 가져오기
credentials = fetch_users()

# --- [4] 로그인/회원가입 시스템 ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="diary_session",
    key="secret_signature_key",
    cookie_expiry_days=7
)

# 사이드바나 메인화면에 탭으로 분리
tab1, tab2 = st.tabs(["로그인", "회원가입"])

with tab1:
    name, authentication_status, username = authenticator.login('로그인', 'main')

with tab2:
    st.subheader("새 계정 만들기")
    new_email = st.text_input("이메일")
    new_username = st.text_input("아이디(ID)")
    new_name = st.text_input("이름(닉네임)")
    new_password = st.text_input("비밀번호", type="password")
    
    if st.button("가입하기"):
        if new_email and new_username and new_name and new_password:
            # 1. 아이디 중복 체크
            if new_username in credentials["usernames"]:
                st.error("이미 존재하는 아이디입니다.")
            else:
                # 2. 비밀번호 암호화(Hashing) - 보안의 핵심!
                hashed_password = stauth.Hasher([new_password]).generate()[0]
                
                # 3. DB에 저장
                new_user = {
                    "username": new_username,
                    "email": new_email,
                    "name": new_name,
                    "password": hashed_password
                }
                execute_query(st_supabase.table("users").insert(new_user))
                st.success("회원가입 성공! 로그인 탭에서 접속하세요.")
                st.balloons()
                st.rerun() # 새로고침해서 유저 정보 갱신
        else:
            st.warning("모든 정보를 입력해주세요.")

# --- [5] 로그인 성공 이후 로직 ---
if authentication_status == False:
    st.error("비밀번호가 올바르지 않습니다.")
elif authentication_status == None:
    st.info("기존 아이디로 로그인하거나 새로 가입해 보세요!")
elif authentication_status:
    # (이하 일기 쓰기/불러오기 로직은 동일합니다)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"✨ {name}님의 단단한 기록 공간")
    with col2:
        authenticator.logout("로그아웃", "main")
    
    st.divider()
    
    # 일기 작성 UI
    st.title("📝 오늘의 기록")
    diary_date = st.date_input("날짜 선택")
    diary_title = st.text_input("제목")
    diary_content = st.text_area("내용", height=200)

    if st.button("일기 저장하기", type="primary"):
        if diary_title and diary_content:
            row = {
                "username": username,
                "diary_date": str(diary_date),
                "title": diary_title,
                "content": diary_content
            }
            execute_query(st_supabase.table("diaries").insert(row))
            st.success("성공적으로 저장되었습니다!")
        else:
            st.warning("내용을 입력해주세요.")

    st.divider()
    st.subheader("📂 나의 지난 기록")
    response = execute_query(
        st_supabase.table("diaries").select("*").eq("username", username).order("diary_date", desc=True)
    )
    if response.data:
        for diary in response.data:
            with st.expander(f"📅 {diary['diary_date']} | {diary['title']}"):
                st.write(diary['content'])
