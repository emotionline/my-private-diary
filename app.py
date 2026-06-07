import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection, execute_query
from datetime import datetime
import pytz

# --- [1] 페이지 기본 세팅 ---
st.set_page_config(page_title="My Music Diary", page_icon="📝", layout="centered")

# --- [2] 아일릿 감성 배경 + 가독성 확보 CSS ---
st.markdown("""
    <style>
    /* 전체 배경에 아일릿 이미지 적용 및 센터 정렬 */
    .stApp {
        background-image: url("https://i.ytimg.com/vi/Me9tTDOfCOE/maxresdefault.jpg`");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    # /* 글씨 가독성을 위한 반투명 화이트 패널 */
    # .block-container {
    #     background: rgba(255, 255, 255, 0.85);
    #     padding: 3rem 2rem !important;
    #     border-radius: 20px;
    #     box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    #     backdrop-filter: blur(4px);
    #     -webkit-backdrop-filter: blur(4px);
    #     margin-top: 2rem;
    #     margin-bottom: 2rem;
    # }
    
    h1, h2, h3, label, p {
        color: #2c3e50 !important;
        font-family: 'Pretendard', sans-serif;
        font-weight: 600;
    }
    
    div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- [3] 🎵 내 다이어리 배경음악(BGM) 설정 🎵 ---
# 웹 브라우저 정책상 '음소거(muted)'가 아니면 자동 재생이 기본 차단되지만, 
# 사용자가 화면을 한 번 클릭하거나 로그인 버튼을 누르는 순간 자물쇠가 풀리며 오디오가 재생됩니다!
AUDIO_URL = "https://www.youtube.com/watch?v=Ai6FLQmajaI&list=RDAi6FLQmajaI&start_radio=1" # ◀ 예시 오디오 파일 주소

st.markdown(f"""
    <audio autoplay loop id="bgm-audio" style="display:none;">
        <source src="{AUDIO_URL}" type="audio/mp3">
    </audio>
    <script>
    // 브라우저 자동재생 제한을 우회하기 위해 사용자가 화면을 클릭하면 소리가 나도록 유도하는 스크립트
    document.body.addEventListener('click', function() {{
        var audio = document.getElementById('bgm-audio');
        if (audio && audio.paused) {{
            audio.play();
        }}
    }});
    </script>
""", unsafe_allow_html=True)


# --- [4] Supabase DB 연결 ---
st_supabase = st.connection(
    name="supabase",
    type=SupabaseConnection,
    url=st.secrets["supabase"]["SUPABASE_URL"],
    key=st.secrets["supabase"]["SUPABASE_KEY"]
)

# --- [5] DB에서 유저 정보 불러오기 ---
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

# --- [6] 로그인 시스템 설정 ---
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

# --- [7] 로그인 성공 이후 대시보드 ---
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

    # 입력창 초기화 로직
    if "diary_title_key" not in st.session_state:
        st.session_state["diary_title_key"] = ""
    if "diary_content_key" not in st.session_state:
        st.session_state["diary_content_key"] = ""

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
            execute_query(st_supabase.table("diaries").insert(row))
            st.success("클라우드 데이터베이스에 실시간 동기화되었습니다!")
            st.balloons()
            
            st.session_state["diary_title_key"] = ""
            st.session_state["diary_content_key"] = ""
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
