# Evidence Pipeline

이 문서는 `YSD` 공개 저장소에 실제로 노출된 파일럿 파생 흐름을 설명합니다. 전체 연구 작업실에는 전 코퍼스 thin RAG 단계가 존재하지만, 이 공개본은 **reviewed annotation 이후의 파일럿 구현 사슬**을 중심으로 구성하고, reviewed chunk 재생성을 위해 Hangzhou gold set 10건의 seed entry chunk만 추가로 포함합니다.

## 1. 공개본의 파이프라인 원칙

- 원문은 별도 source text로 보존한다.
- reviewed annotation이 파생 흐름의 출발점이다.
- graph는 언제나 semantic assertion의 파생층으로만 생성된다.
- provenance, `translation_basis`, `certainty`, `review_status`는 가능한 범위에서 다음 층으로 계승된다.
- 결과물은 `edge -> assertion -> entry -> 원문` 경로로 역추적 가능해야 한다.

## 2. 공개본에 포함된 흐름

```text
texts/plain/yunshanriji_fulltext.txt
  -> reviewed annotation 10건
  -> seed entry chunk 10건
  -> authority subset
  -> reviewed entry chunk 10건
  -> entity dossier chunk 8건
  -> semantic assertion 27건
  -> graph node 26건 / edge 27건
  -> demo query 5건
```

이 공개본은 full corpus coverage보다 **reviewed pilot precision**을 우선합니다. seed entry chunk는 reviewed entry chunk를 다시 생성하기 위한 최소 기반일 뿐, 전 코퍼스 thin RAG 전체를 다시 노출하는 층이 아닙니다.

## 3. 단계별 설명

### 3.1 Reviewed annotation -> authority

annotation에서 식별된 person, place, office, institution을 authority로 누적합니다. 공개 저장소에서는 전체 authority를 다 싣지 않고, 최종 산출물에서 실제로 참조되는 subset만 남깁니다.

### 3.2 Reviewed annotation -> reviewed entry chunk

reviewed entry chunk는 엔트리 단위의 근거 응답층입니다.

- `translation_revised`가 있으면 그 번역을 사용
- `translation_basis`는 실제 사용한 번역 출처를 정직하게 표시
- `review_status = reviewed`
- 개체 목록, place 목록, certainty를 annotation에서 반영

### 3.3 Authority -> entity dossier

selected entity에 대해 누적 설명 카드를 만듭니다. 이 층은 “누가 누구인가” 같은 질문에 대응합니다.

### 3.4 Annotation + authority -> semantic assertion

annotation의 행위와 authority의 관계를 이용해 주어-술어-목적어 형태의 assertion을 생성합니다. assertion은 graph보다 한 단계 앞선 의미 단위입니다.

### 3.5 Assertion -> graph

graph는 assertion 압축층입니다.

- edge는 assertion에서만 생성
- `source_assertion_ids` 필수
- certainty는 source assertion에서 계승

### 3.6 Reviewed chunk + dossier + assertion -> demo query

demo query는 질문, 기대 chunk, 샘플 답변, 원문 근거를 한 묶음으로 보여주는 시연층입니다.

## 4. 공개본에 포함하지 않은 것

이 공개본은 아래 항목을 의도적으로 제외합니다.

- 전 코퍼스 thin RAG 전체
- review 원본 JSON
- 리뷰 웹 도구
- imported original/translation 읽기본
- spec 문서와 운영 보조 자료

즉 이 파이프라인 문서는 작업실 전체 흐름이 아니라, **논문 부속 공개본에서 실제로 확인 가능한 파생 사슬**만 설명합니다.
