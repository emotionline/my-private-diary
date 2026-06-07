import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 레이아웃 및 모바일 최적화 세팅
st.set_page_config(
    page_title="📦 공주대 기숙사 반띵(Ban-Thing)", 
    page_icon="📦", 
    layout="centered"
)

# 2. 로컬 서버 세션 데이터 저장소 (비밀번호 필드 추가)
if "posts" not in st.session_state:
    st.session_state.posts = [
        {
            "id": 1,
            "등록시간": "06-08 11:00",
            "모집품목": "쿠팡 우삼겹 1kg (두 팩 묶음)",
            "인당 금액": "6,500원",
            "픽업 장소": "은행사 상가 앞",
            "총인원": 2,
            "현재인원": 2,  
            "비밀번호": "0000", # 예시용
            "상품 링크": "https://www.coupang.com",
            "오픈채팅 주소": "https://open.kakao.com/o/demo1"
        },
        {
            "id": 2,
            "등록시간": "06-08 09:30",
            "모집품목": "햇반 발아현미밥 24개입",
            "인당 금액": "1,800원",
            "픽업 장소": "기숙사 비전관 로비",
            "총인원": 4,
            "현재인원": 1,  
            "비밀번호": "1234", # 예시용
            "상품 링크": "https://www.coupang.com",
            "오픈채팅 주소": "https://open.kakao.com/o/demo2"
        }
    ]

# 3. 상단 배너 및 이미지
st.title("🎤 쇼미더 반띵 : N분의 1 (Ban-Thing)")
st.markdown("### `\"우린 N분의 1, 생필품 짜치게 안 나눠~ 🍚\"`")

st.image("https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=1000", 
         caption="Drop the beat 🎧 우린 정확히 N분의 1만 해.", use_container_width=True)

st.info("""
🤝 **공주대 학우들을 위한 무수수료 순수 복지 웹입니다.**  
귀찮은 회원가입/로그인 없이, 나만의 **마감 비밀번호**만 설정해서 편하게 이용하세요!
""")

st.markdown("---")

# 4. 실시간 매칭 현황판 (카드 UI + 비밀번호 마감 기능)
st.subheader("🔥 지금 올라온 실시간 반띵 모집")

if st.session_state.posts:
    for post in st.session_state.posts:
        is_full = post["현재인원"] >= post["총인원"]
        
        with st.container(border=True):
            col1, col2 = st.columns([1.8, 1.2])
            
            with col1:
                if is_full:
                    st.markdown(f"### ~~{post['모집품목']}~~")
                else:
                    st.markdown(f"### {post['모집품목']}")
                    
                st.caption(f"⏰ 등록: {post['등록시간']} | 📍 장소: {post['픽업 장소']}")
                st.markdown(f"💰 **인당 금액:** {post['인당 금액']}")
                
                if post['상품 링크'] != "링크 없음":
                    st.markdown(f"🔗 [쿠팡/네이버 상품 확인하기]({post['상품 링크']})")
            
            with col2:
                if is_full:
                    st.success("✅ 모집 마감")
                    st.metric(label="인원 현황", value="🔥 만석")
                else:
                    st.info("⚡ 모집 중")
                    st.metric(label="인원 현황", value=f"{post['현재인원']} / {post['총인원']}")
                    st.link_button("💬 카톡 참여", post["오픈채팅 주소"], use_container_width=True)
                    
                    # 📌 무로그인 방장 마감 폼 (토글 형식)
                    with st.popover("🔒 방장 마감", use_container_width=True):
                        input_pw = st.text_input("글 만들 때 쓴 비밀번호 입력", type="password", key=f"pw_{post['id']}")
                        if st.button("마감 확정", key=f"btn_{post['id']}", use_container_width=True):
                            if input_pw == post["비밀번호"]:
                                post["현재인원"] = post["총인원"] # 인원 만석 처리
                                st.success("마감 완료! 새로고침 중...")
                                st.rerun()
                            else:
                                st.error("비밀번호가 틀렸습니다! 😡")
else:
    st.write("아직 올라온 소분 글이 없습니다. 첫 번째 글의 주인공이 되어보세요! 😎")

st.markdown("---")

# 5. 새로운 소분 모집 글 쓰기 폼 (비밀번호 입력 추가)
st.subheader("➕ 나도 같이 살 사람 모집하기")

with st.form("match_form", clear_on_submit=True):
    title = st.text_input("1. 어떤 물품을 나누실 건가요?", placeholder="예: 크리넥스 휴지 30롤, 세제 대용량 등")
    total_people = st.selectbox("2. 본인을 포함해서 총 몇 명이서 나눌 건가요?", [2, 3, 4, 5, 6, 7, 8, 9, 10], index=0)
    price = st.text_input("3. 인당 예상 금액은 얼마인가요?", placeholder="예: 인당 3,500원")
    place = st.selectbox("4. 선호하는 픽업 장소는?", ["기숙사 로비/벤치", "학교 정문 앞", "공주대 후문/대학가", "자취방 근처 (상세 기재)"])
    prod_link = st.text_input("🛒 쿠팡/네이버 상품 링크 (선택)", placeholder="물건 주소를 넣어주면 학우들이 더 잘 믿어요!")
    contact = st.text_input("🔗 카카오톡 오픈채팅방 링크 (필수)", placeholder="학우들이 타고 들어올 링크를 넣어주세요!")
    
    # 📌 방장 인증용 비밀번호 칸 추가!
    password = st.text_input("🔑 마감용 비밀번호 설정 (필수)", type="password", max_chars=4, placeholder="글을 마감할 때 쓸 숫자 4자리")
    
    submit = st.form_submit_button("🚀 반띵 모집 글 올리기")

if submit:
    if title and price and contact and password:
        current_time = datetime.now().strftime("%m-%d %H:%M")
        final_link = prod_link if prod_link else "링크 없음"
        
        new_post = {
            "id": len(st.session_state.posts) + 1,
            "등록시간": current_time,
            "모집품목": title,
            "인당 금액": price,
            "픽업 장소": place,
            "총인원": total_people,
            "현재인원": 1,  
            "비밀번호": password, # 입력한 비밀번호 저장
            "상품 링크": final_link,
            "오픈채팅 주소": contact
        }
        st.session_state.posts.insert(0, new_post)
        st.success("🎉 모집 글이 성공적으로 등록되었습니다!")
        st.balloons() 
        st.rerun() 
    else:
        st.warning("비밀번호를 포함한 모든 필수 칸을 채워주세요! 🥺")

st.markdown("---")
st.subheader("💬 빌더(Builder)에게 한마디")
st.write("“필요한 기능이나 버그 제보는 댓글이나 아래 오픈카톡으로 찔러주세요. 형이 심심할 때 업데이트해 줌.”")
st.caption("© 2026 공주대학교 능력자 학우가 만든 순수 복지 프로젝트 - Ban-Thing")
