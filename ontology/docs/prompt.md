SNU Barrier-Free Ontology Service 구현 명세서

이 문서는 "서울대 지체 장애 학우를 위한 배리어프리 수강신청 도우미" 서비스를 구축하기 위한 AI 에이전트의 작업 지침서이다.
당신의 임무는 data/csv/ 내의 Raw Data를 읽어 논리적인 지식 그래프(RDF/Turtle)로 변환하고, 이를 기반으로 투명한 추론이 가능한 Text-to-SPARQL 웹 서비스를 구현하는 것이다.

1) 아키텍처 (Architecture)

Phase 1. Data Pipeline (ETL)
CSV Files (Nodes, Edges, Courses) ➜ build_graph.py ➜ knowledge_graph.ttl (Serialization)

Phase 2. Service Pipeline (Search)
User Query ➜ LLM (Schema Aware) ➜ SPARQL Generation ➜ RDFLib (Graph Engine) ➜ Result ➜ LLM (Natural Language Answer)

2) 기술 스택 (Tech Stack)

Language: Python 3.11

Graph Engine: rdflib (In-Memory Graph Database)

Data Handling: pandas (CSV Processing)

LLM: gemini-3-pro-preview (Logic Reasoning & SPARQL Gen)

UI Framework: Streamlit (Interactive Web Interface with Transparency)

3) 데이터 소스 명세 (Data Source)

작업 디렉토리 내 data/csv/ 위치에 다음 파일들이 존재한다.

안성재팀 - 온톨로지 - Nodes.csv: 객체 정의. (id, label, sort 컬럼)

sort='Class': 클래스 정의 (예: Building)

sort='Instance': 인스턴스 정의 (예: 43-1동)

안성재팀 - 온톨로지 - Edges.csv: 관계 정의. (sourceID, targetID, relation 컬럼)

안성재팀 - 온톨로지 - 교과목.csv: 강의 상세 속성. (ID 컬럼이 Nodes의 id와 매핑됨)

안성재팀 - 온톨로지 - Class_Relation_Attribute_Property.csv: 스키마 참고용.

4) 구현 마일스톤 (Milestones)

각 단계가 완료될 때마다 사용자에게 한글로 요약 보고를 수행하고 승인을 대기한다.

Step 0. 프로젝트 초기화 및 CQ 정의

프로젝트 구조 생성 (src/, data/, docs/).

[중요] 아래 **'Section 5. 핵심 역량 질문'**의 내용을 docs/competency_questions.md 파일로 저장한다. 이는 추후 쿼리 생성 로직의 기준이 된다.

.env 파일을 생성하고 Gemini API Key 입력을 안내한다.

Step 1. 온톨로지 그래프 구축기 (src/build_graph.py)

흩어진 CSV 데이터를 하나의 knowledge_graph.ttl로 변환하는 스크립트를 작성한다.

Namespace: Base URI http://snu.ac.kr/barrier-free/ (Prefix: :) 사용.

Nodes 변환:

Nodes.csv의 id를 URI로 변환.

sort가 'Class'면 a rdfs:Class, 'Instance'면 a :ClassName (label 컬럼 참조) 부여.

Properties 병합:

교과목.csv를 로드하여, 해당 ID를 가진 Course 인스턴스에 :startsAt, :endsAt, :dayOfWeek 등의 Data Property를 추가한다.

Edges 변환:

Edges.csv의 relation 컬럼 값을 Predicate로 사용하여 sourceID와 targetID를 연결한다.

예: :Course_10101 :isHeldAt :Room_43-1_403

Step 2. 그래프 엔진 및 검색 로직 구현 (src/graph_agent.py)

Graph Loader: 생성된 TTL 파일을 rdflib으로 로드.

Schema Extractor: LLM에게 그래프 구조(Classes, Relations)를 요약해주는 프롬프트 생성 함수 구현.

SPARQL Generator (핵심):

docs/competency_questions.md의 질문 패턴을 분석하여, LLM 프롬프트에 Few-shot Example로 포함시켜야 한다.

필수 로직:

시설 조회: ?bldg :hasFacility :Facility_Elevator

위험 회피: FILTER NOT EXISTS { ?bldg :hasHazard :Hazard_Curb }

시간 비교: ?course :startsAt ?time 활용.

Executor: 쿼리 실행 및 DataFrame 반환.

Step 3. 투명성 기반 웹 서비스 (src/app.py)

Streamlit 채팅 인터페이스 구현.

답변 구조화 (Transparency):

최종 답변: 자연어.

근거 데이터: st.expander 안에 DataFrame 표시.

SPARQL 쿼리: st.expander 안에 코드 표시.

해석: LLM의 쿼리 작성 의도 설명.

5) 핵심 역량 질문 (Competency Questions)

이 내용은 시스템이 반드시 해결해야 할 질문 리스트이다. docs/competency_questions.md로 저장하여 개발 시 참고하라.

기본 장소 조회: "'수학1' 수업은 어느 건물, 어느 강의실에서 열려?"

시설 보유 검증: "500동 건물에 휠체어용 엘리베이터가 있어?"

단일 과목 수강 가능성: "나 휠체어 타는데 '대학글쓰기1' 수강 신청해도 될까? (건물에 턱 없고 엘리베이터 있어?)"

위험 요소 경고: "43-1동 입구에 급경사나 턱 같은 거 있어?"

공강 시간 대피처: "지금 24동 근처인데, 장애인 화장실(WC) 있는 건물 어디야?"

필수 과목 연계 추천: "'대학글쓰기1' 분반 중 휠체어로 갈 수 있는 반 추천해줘."

시간-공간 복합 추천: "'베리타스 실천' 끝나고 바로 들을 수 있는 '수학1' 분반은?"

공강 활용 추천: "월요일 공강 때 휠체어로 갈 수 있는 건물 내의 다른 수업은?"

최적 수강 조합: "'대학글쓰기1'과 '수학연습1' 둘 다 들어야 해. 시간 안 겹치고 이동 가능한 조합 추천해줘."

6) 시나리오 예시 (Output Expectation)

사용자: "'대학글쓰기1' 수업 듣고 싶은데, 거기 휠체어 엘리베이터 있어?"

AI 화면 출력:

🤖 AI: 네, 수강 가능합니다. 해당 수업이 있는 500동에는 **엘리베이터(:Facility_Elevator)**가 설치되어 있습니다.

(▼ 근거 데이터 확인하기)

SPARQL:

SELECT ?bldgName ?facility
WHERE {
  ?course :title "대학글쓰기1" ;
          :isHeldAt ?room .
  ?room :locatedIn ?bldg .
  ?bldg :name ?bldgName ;
        :hasFacility :Facility_Elevator .
}


Raw Data: [("500동", "http://.../Facility_Elevator")]