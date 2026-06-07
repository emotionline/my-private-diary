import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection, execute_query
from datetime import datetime
import pytz

# --- [1] 페이지 기본 세팅 ---
st.set_page_config(page_title="My Video Diary", page_icon="✨", layout="centered")

# --- [2] 비디오 배경 주입 + 필름 제거 + 가독성 확보 CSS ---
# ⚠️ 아래 "민주_영상_링크.mp4" 부분에 실제 mp4 파일 주소를 넣으시면 됩니다!
VIDEO_URL = "https://assets.mixkit.co/videos/preview/mixkit-starry-outer-space-background-40019-large.mp4" # 예시 몽환적인 영상

st.markdown(f"""
    <style>
    /* 1. 영상 위에 올라가는 스트림릿 기본 배경을 투명하게 만듭니다. */
    .stApp {{
        background: transparent;
    }}
    
    /* 2. 기존의 불투명했던 반투명 카드 필름을 완전히 삭제하고 투명하게 오픈 */
    .block-container {{
        background: transparent !important;
        padding: 3rem 2rem !important;
        margin-top: 2rem;
    }}
    
    /* 3. 흰색 글씨가 영상 배경에 묻히지 않도록 글자 뒤에 쨍한 검은색 그림자 주입 */
    h1, h2, h3, label, p, .stMarkdown {{
        color: #ffffff !important;
        font-family: 'Pretendard', sans-serif;
        font-weight: 700 !important;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.9), -2px -2px 8px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* 4. 화면 전체를 덮는 비디오 태그 스타일 정의 */
    #bg-video {{
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100%;
        min-height: 100%;
        width: auto;
        height: auto;
        z-index: -100; /* 맨 뒤로 보내기 */
        background-size: cover;
        object-fit: cover; /* 영상 비율 깨짐 방지 */
    }}
    </style>
    
    <video autoplay loop muted playsinline id="bg-video">
        <source src="{VIDEO_URL}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

# --- [3] Supabase DB 연결 ---
st_supabase = st.connection(
    name="supabase",
    type=SupabaseConnection,
    url=st.secrets["supabase"]["SUPABASE_URL"],
    key=st.secrets["supabase"]["SUPABASE_KEY"]
)

# --- [4] DB에서 유저 정보 불러오기 ---
def fetch_users():
    try:
        res = execute_query(st_supabase.table("users").select("*"), ttl=0)
        credentials = {"usernames": {}}
        if res.data:
            for user in res.data:
                credentials["usernames"][user["username"]] = {
                    "email": user["email"],
                    "name": user["name"],
                    "password": str(user["password"])
                }
        return credentials
    except Exception as e:
        return {"usernames": {}}

credentials = fetch_users()

# --- [5] 로그인 시스템 설정 (v0.2.3 규격) ---
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
                hashed_passwords = stauth.Hasher([new_password]).encoded_passwords
                hashed_password = hashed_passwords[0]
                
                new_user = {
                    "username": new_username,
                    "email": new_email,
                    "name": new_name,
                    "password": hashed_password
                }
                execute_query(st_supabase.table("users").insert(new_user))
                st.success("회원가입이 완료되었습니다! 로그인 탭에서 접속하세요.")
                st.balloons()
                st.rerun()
        else:
            st.warning("모든 항목을 입력해 주세요.")

# --- [6] 로그인 성공 이후 대시보드 ---
if authentication_status == False:
    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

elif authentication_status == None:
    st.info("로그인이 필요합니다. 나만의 단단한 기록 공간을 시작해 보세요.")

elif authentication_status:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"✨ {name}님의 기록 공간")
    with col2:
        authenticator.logout("로그아웃", "main")
        
    st.divider()

    # [핵심] 입력창 동적 초기화를 위한 세션 상태 등록
    if "input_title" not in st.session_state:
        st.session_state["input_title"] = ""
    if "input_content" not in st.session_state:
        st.session_state["input_content"] = ""

    # 일기 작성 영역 (value와 key를 세션 상태에 완전 밀착시켰습니다)
    st.title("📝 오늘의 기록")
    diary_date = st.date_input("날짜 선택")
    
    diary_title = st.text_input("제목", key="diary_title_key", placeholder="오늘을 관통하는 한 마디")
    diary_content = st.text_area("내용", key="diary_content_key", placeholder="생각과 감정을 차분히 정돈해 보세요.", height=200)

    if st.button("일기 저장하기", type="primary"):
        if diary_title and diary_content:
            row = {
                "username": username,
                "diary_date": str(diary_date),
                "title": diary_title,
                "content": diary_content
            }
            # Supabase 저장
            execute_query(st_supabase.table("diaries").insert(row))
            st.success("클라우드 데이터베이스에 실시간 동기화되었습니다!")
            st.balloons()
            
            # [치트키] 입력창 전용 컴포넌트의 내부 state를 강제로 날려버립니다.
            st.session_state["diary_title_key"] = ""
            st.session_state["diary_content_key"] = ""
            
            # 화면 리프레시로 초기화 100% 반영
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
                time_str = ""
                if "created_at" in diary and diary["created_at"]:
                    try:
                        utc_time = datetime.fromisoformat(diary["created_at"].replace("Z", "+00:00"))
                        kst_time = utc_time.astimezone(pytz.timezone("Asia/Seoul"))
                        time_str = kst_time.strftime(" %H:%M")
                    except:
                        time_str = ""

                with st.expander(f"📅 {diary['diary_date']}{time_str} | {diary['title']}"):
                    st.write(diary['content'])
        else:
            st.info("아직 저장된 일기가 없습니다. 첫 기록을 남겨보세요!")
    except Exception as e:
        st.error("데이터를 불러오는 중 오류가 발생했습니다.")
