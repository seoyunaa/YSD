# Repository Handbook

이 문서는 `YSD` 공개 저장소를 설명하는 기준 문서입니다. 이 저장소는 **사료비판적 온톨로지 설계의 핵심 문서와 Hangzhou gold set 파일럿 결과만 공개한 논문 부속 최소 공개본**입니다.

## 1. 저장소의 목적

이 공개본의 목적은 완전한 서비스 제공이 아니라, 다음 두 가지를 독자가 직접 확인할 수 있게 하는 데 있습니다.

1. 고전 일기 사료를 **계층형 연구데이터셋**으로 구조화하는 방법
2. Hangzhou gold set 파일럿에서 reviewed annotation -> semantic assertion -> graph가 실제로 작동하는 방식

즉 이 저장소는 “전체 작업 환경”보다 “논문에서 주장하는 설계와 구현을 검증 가능한 형태로 압축한 companion repo”에 가깝습니다.

## 2. 방법론적 위치

YSD는 고전 일기 사료를 단순 텍스트나 단순 그래프로 다루지 않습니다. 이 저장소의 중심 개념은 다음과 같습니다.

- **사료비판적 온톨로지 설계**
- **계층형 연구데이터셋**
- **원문 보존층 / 인간 교정층 / 파생층**
- **역추적 가능성**
- **불확실성의 구조적 보존**

여기서 graph는 최종 산출물일 뿐 출발점이 아닙니다. graph는 언제나 **semantic assertion의 파생층**으로만 생성됩니다.

## 3. 공개본에 포함된 계층

이 공개본은 전체 연구 작업실 가운데 아래 계층만 노출합니다.

| 계층 | 경로 | 공개 이유 |
| --- | --- | --- |
| source text | `texts/plain/` | source pointer와 원문 근거 확인 |
| work descriptor | `data/work/` | 텍스트와 연구 맥락 설명 |
| reviewed annotation | `data/annotations/entries/` | 사람 교정이 반영된 핵심 해석층 |
| authority subset | `data/annotations/entities/` | 파일럿 결과에서 실제로 참조되는 대표 개체만 공개 |
| seed entry chunk | `data/rag/chunks/entry_chunks.jsonl` | reviewed chunk 재생성을 위한 10건짜리 최소 기반 |
| reviewed chunk | `data/rag/chunks/reviewed_entry_chunks.jsonl` | RAG용 근거 단위 |
| entity dossier | `data/rag/chunks/entity_dossier_chunks.jsonl` | 개체별 누적 요약 카드 |
| semantic assertion | `data/semantic/assertions/assertions.jsonl` | 진술 단위 |
| graph | `data/graph/` | assertion 파생 지식그래프 |
| demo query | `data/rag/demo_queries.json` | 실제 시연 질문 |

## 4. 현재 공개된 파일럿 수치

Hangzhou gold set 범위는 `entry-0019 ~ entry-0028`입니다.

- annotation: `10`
- reviewed entry chunk: `10`
- entity dossier chunk: `8`
- semantic assertion: `27`
- graph node: `26`
- graph edge: `27`
- demo query: `5`

이 수치는 전체 연구가 아니라, **Hangzhou gold set 파일럿 구현 결과**를 뜻합니다.

공개된 authority subset:

- person `13`
- place `16`
- office `6`
- institution `5`

## 5. 공개본에서 제외한 것

이 공개본은 최소 공개 원칙에 따라 아래 항목을 의도적으로 제외합니다.

- 전 코퍼스 thin RAG 전체 산출물
- 리뷰 원본 JSON과 리뷰 운영 자료
- 리뷰 웹 도구
- imported 읽기본
- 구현 명세 spec 문서
- drafts, screenshots, 보조·정비용 스크립트

즉 이 저장소는 “모든 작업 흔적”이 아니라, **논문에서 직접 확인 가능한 설계와 결과만 남긴 최소 공개본**입니다.

## 6. 재현 가능한 최소 실행선

이 공개본에는 annotation 이후 결과를 다시 생성할 수 있는 최소 Python 스크립트만 포함합니다.

- `scripts/phase_d_pipeline.py`
- `scripts/run_public_pilot.py`

`run_public_pilot.py`는 포함된 reviewed annotation, authority subset, seed entry chunk를 입력으로 하여 reviewed chunk, dossier, assertion, graph, demo query를 다시 생성하고, 마지막에 공개본에서 실제로 참조되는 authority subset만 남기도록 정리합니다.

## 7. 이용 안내

이 저장소의 코드는 MIT 라이선스로 공개합니다. 다만 비코드 자료는 별도 이용 조건을 따릅니다.

- `LICENSE`: 코드용 MIT
- `DATA_AND_DOCS_NOTICE.md`: 문서, 번역, annotation, assertion, graph 등 비코드 자료 이용 제한 안내
