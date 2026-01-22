# 🎓 Course_Registration_Supporter

**"안전하게 서울대를 재-빠르게: 모두를 위한 서울대 배리어 프리 서비스"**
<img width="1436" height="805" alt="image" src="https://github.com/user-attachments/assets/1146d350-f788-41d5-9b71-2660bce80755" />

이동 약자 학우를 위한 **지식 그래프 기반 배리어프리 수강신청 도우미**입니다. AI 에이전트를 활용하여 수강신청 관련 정보, 시설 접근성, 네비게이션 정보를 제공합니다.



## 📋 프로젝트 개요

### 목표
서울대학교 재학생 중 지체 장애 학우들의 수강신청 및 캠퍼스 이용을 돕기 위한 통합 정보 제공 시스템입니다.

### 주요 기능
- **🔍 수강신청 도우미 (Chat)**: AI 챗봇으로 장애 학우 맞춤형 정보 제공
- **🛠️ 시설 관리 (Maintenance)**: 캠퍼스 시설 접근성 정보 관리
- **📊 지식 그래프 시각화 (Visualization)**: RDF 기반 온톨로지 시각화

## 👥 Team 안성재

| 이름 | 소속 | 역할 |
|------|------|------|
| [남승빈(팀장)](https://github.com/namsb) | 서울시립대학교 통계학과 | 온톨로지 구축 & 자료 제작  |
| [김성희](https://github.com/dmseong) | 숙명여자대학교 컴퓨터과학전공 | 온톨로지 구축 & 지식그래프 구현 개발 |
| [김태운](https://github.com/Listro02) | 서울대학교 컴퓨터공학부 | 온톨로지 구축 & 서비스 개발 |
| [이나연](https://github.com/NayeonLeee) | 한국외국어대학교 ELLT/LAI | 온톨로지 구축 & 자료제작 & 발표 |

## 🔧 설치 및 실행

### 필수 요건
- Python 3.8+
- Google Generative AI API 키

### 설치 단계

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd Course_Registration_Supporter/ontology
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정**
   `.env` 파일 생성 후 API 키 설정:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

4. **애플리케이션 실행**
   ```bash
   cd src
   streamlit run app.py
   ```

---

## 📦 주요 의존성

| 패키지 | 용도 |
|--------|------|
| `rdflib>=7.0.0` | RDF/OWL 처리 및 SPARQL 쿼리 |
| `streamlit>=1.30.0` | 웹 UI 프레임워크 |
| `google-generativeai>=0.5.0` | LLM (Gemini) API |
| `python-dotenv>=1.0.0` | 환경 변수 관리 |

---

## 🤖 핵심 모듈

### `app.py` - Streamlit 메인 애플리케이션
- **페이지 1: 수강신청 도우미 (Chat)**
  - 자연어 질문 입력
  - AI 에이전트의 지식 그래프 기반 답변
  - SPARQL 쿼리 및 근거 데이터 시각화

- **페이지 2: 시설 관리 (Maintenance)**
  - 캠퍼스 시설 정보 관리

- **페이지 3: 지식 그래프 시각화 (Visualization)**
  - Pyvis를 이용한 인터랙티브 그래프 시각화

### `graph_agent.py` - AI 에이전트
- **자연어 처리**: 사용자 질문을 SPARQL 쿼리로 변환
- **지식 그래프 검색**: RDF 온톨로지에서 정보 추출
- **답변 생성**: LLM(Gemini)으로 자연스러운 답변 생성
- **추론**: 질문에 대한 논리적 근거 제시

### `build_graph.py` - 지식 그래프 구축
- CSV 데이터를 RDF/Turtle 형식으로 변환
- 온톨로지 기반 데이터 모델 생성

### `config.py` - 설정 관리
- 프로젝트 경로 설정
- 모델 설정
- 파일 경로 정의

---

## 📊 지식 그래프 구조
- **`knowledge_graph.html`**: [지식 그래프 시각화 보기](https://dmseong.github.io/Course_Registration_Supporter/)
<img width="500" height="480" alt="image" src="https://github.com/user-attachments/assets/91c0dd62-8096-48d0-903f-d7a839ae4123" />

### 온톨로지 개요
- **주체 (Classes)**: 교과목, 건물, 시설, 경로 등
- **관계 (Properties)**: 소속, 접근성, 위치 정보 등
- **속성 (Data Properties)**: 엘리베이터 유무, 휠체어 접근 가능 여부 등
<img width="1018" height="459" alt="image" src="https://github.com/user-attachments/assets/8af7c032-78f8-46ba-9d6a-659d5d3a98c9" />
<img width="1254" height="522" alt="image" src="https://github.com/user-attachments/assets/230f509f-843f-432d-8dec-1cda5062abad" />
<img width="1347" height="409" alt="image" src="https://github.com/user-attachments/assets/376dad8f-239f-4bd8-818f-171140af9c53" />
<img width="1081" height="461" alt="image" src="https://github.com/user-attachments/assets/e09b019a-02e4-4dac-a9c9-0ca3a33a3d85" />


### RDF 네임스페이스
```
http://snu.ac.kr/barrier-free/
```

---

## 🎯 사용 예시

### 질문 예시
- "500동에 엘리베이터 있어?"
- "지체 장애 학우가 접근 가능한 강의실은?"
- "장애인 화장실 위치가 어디야?"
- "500동에서 중앙도서관까지 휠체어로 갈 수 있는 경로 있어?"

### 예상 답변
- 자연스러운 한국어 답변
- SPARQL 쿼리 및 조회 근거 데이터 제시
- 시각화된 경로 또는 시설 정보

## 📝 문서

- **`competency_questions.md`**: 온톨로지가 답할 수 있는 질문들
- **`prompt.md`**: AI 에이전트의 시스템 프롬프트



