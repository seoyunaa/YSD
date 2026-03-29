# Data Model

이 문서는 `YSD` 공개 저장소에 실제로 포함된 파일럿 데이터 구조를 설명합니다. 전체 연구 작업실에는 더 넓은 계층이 존재하지만, 이 공개본은 Hangzhou gold set 파일럿의 **reviewed 층과 파생층**만 노출합니다.

## 1. 기본 원칙

이 공개본의 데이터 모델은 다음 원칙을 유지합니다.

- 원문은 수정하지 않고 별도 source text로 보존한다.
- reviewed annotation이 모든 파생층의 출발점이 된다.
- `translation_basis`, `certainty`, `review_status`, provenance는 파생 단계마다 계승된다.
- graph는 annotation의 직접 산물이 아니라 **semantic assertion의 파생층**이다.
- 모든 파생 결과는 `edge -> assertion -> entry -> 원문` 경로로 역추적 가능해야 한다.

## 2. 공개본에 포함된 주요 파일

| 층 | 경로 | 역할 |
| --- | --- | --- |
| source text | `texts/plain/yunshanriji_fulltext.txt` | 원문 근거 확인 |
| work metadata | `data/work/work-yunshanriji.json` | 텍스트 메타데이터 |
| reviewed annotation | `data/annotations/entries/entry-0019.annotation.json` ~ `entry-0028.annotation.json` | 인간 교정층 |
| authority subset | `data/annotations/entities/` | 공개 결과에서 참조되는 대표 개체 |
| seed entry chunk | `data/rag/chunks/entry_chunks.jsonl` | reviewed chunk 재생성용 10건 입력 |
| reviewed chunk | `data/rag/chunks/reviewed_entry_chunks.jsonl` | 엔트리 기반 근거 단위 |
| entity dossier | `data/rag/chunks/entity_dossier_chunks.jsonl` | 개체별 누적 설명 단위 |
| semantic assertion | `data/semantic/assertions/assertions.jsonl` | 주어-술어-목적어 진술 단위 |
| graph | `data/graph/knowledge_graph_nodes.jsonl`, `data/graph/knowledge_graph_edges.jsonl` | assertion 파생 지식그래프 |
| demo query | `data/rag/demo_queries.json` | 시연 질문 묶음 |

## 3. Reviewed Annotation

reviewed annotation은 이 공개본의 핵심 입력층입니다.

핵심 필드군:

- 번역과 요약: `translation_revised`, `summary_ko`
- 개체: `persons`, `places`, `offices`, `institutions`, `documents`, `works`, `consumables`
- 행위: `interactions`, `exchanges`, `artworks`, `journey`
- 보조 해석: `topics`, `time_markers`, `notes`
- 상태와 provenance: `status`, `provenance`

이 층은 원문을 덮어쓰지 않고, 연구자의 판단을 구조적으로 남기는 역할을 합니다.

## 4. Authority Subset

공개본의 authority는 전체 작업실에서 생성된 모든 authority를 담지 않습니다. 대신 reviewed chunk, dossier, assertion, graph에서 실제로 참조되는 개체만 남깁니다.

authority가 유지하는 핵심 정보:

- `label_original`, `label_normalized`
- `aliases`
- `appointments`
- `relations`
- `place_info`, `institution_info`
- `external_ids`의 보류 상태

즉 authority subset은 최소 공개 원칙을 따르되, 파일럿 결과의 의미망이 끊기지 않도록 필요한 연결은 유지합니다.

## 5. Reviewed Chunk

`reviewed_entry_chunks.jsonl`은 gold set용 근거 chunk입니다.

핵심 속성:

- `chunk_type = entry`
- `text_lzh`, `text_ko`
- `translation_basis`
- `review_status = reviewed`
- `certainty`
- `entities`
- `places`
- `evidence_raw`
- `source_text_pointer`

이 chunk는 질문 응답과 근거 회수를 위한 최소 단위입니다.

## 6. Entity Dossier

`entity_dossier_chunks.jsonl`은 개체별 누적 카드입니다. 하나의 entry가 아니라 하나의 인물 또는 장소를 묻는 질문에 대응하기 위한 층입니다.

핵심 속성:

- `chunk_type = entity_dossier`
- `source_entity_id`
- `source_entry_ids`
- `text_ko`
- `evidence_raw`
- `entities`

## 7. Semantic Assertion

`assertions.jsonl`은 reviewed annotation과 authority를 바탕으로 만든 진술 단위입니다.

대표 예:

- `郭畀 -> visited -> 龔子敬`
- `郭畀 -> traveled_to -> 杭州`
- `龔子敬 -> held_office -> 山長`
- `施水坊橋 -> located_in -> 杭州`

모든 assertion은 `evidence_raw`, `source_entry_ids`, `certainty`, `provenance`를 가집니다.

## 8. Graph

그래프는 assertion을 압축한 파생층입니다.

- node는 assertion에 등장한 개체를 기반으로 생성
- edge는 assertion에서만 생성
- `source_assertion_ids`를 통해 근거 assertion을 역추적
- `certainty`, `review_status`는 source assertion에서 계승

즉 이 공개본에서 graph는 출발점이 아니라 **근거를 압축해 보여주는 마지막 층**입니다.
