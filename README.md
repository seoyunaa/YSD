# YSD

YSD는 Yunshan Diary 연구를 위한 **논문 부속 최소 공개 저장소**입니다. 이 저장소는 전체 연구 작업실을 그대로 공개하는 것이 아니라, **사료비판적 온톨로지 설계**와 **Hangzhou gold set 파일럿 구현**을 확인할 수 있는 최소한의 문서와 결과물만 제공합니다.

이 공개본의 목적은 두 가지입니다.

- 연구 설계가 어떤 개념어와 계층 구조를 전제로 하는지 보여주기
- Hangzhou 파일럿에서 reviewed annotation -> semantic assertion -> graph가 실제로 작동함을 확인 가능하게 하기

전체 작업실에서 사용된 thin RAG 전체, 리뷰 원본 JSON, 리뷰 웹 도구, imported 읽기본, spec 문서는 이 공개본에 포함하지 않습니다.

## 포함 범위

- 기준 문서: `README.md`, `docs/repository-handbook.md`
- 핵심 설계 문서: `docs/data-model.md`, `docs/evidence-pipeline.md`, `docs/ontology-rationale.md`
- 스키마: `schemas/`
- source text pointer 유지를 위한 원문: `texts/plain/yunshanriji_fulltext.txt`
- Hangzhou gold set annotation `10`
- reviewed entry chunk `10`
- entity dossier chunk `8`
- semantic assertion `27`
- graph node `26`
- graph edge `27`
- demo query `5`
- reviewed chunk 재생성을 위한 seed entry chunk `10`
- 결과물에서 실제로 참조되는 authority subset
  - person `13`
  - place `16`
  - office `6`
  - institution `5`
- annotation부터 결과물을 다시 생성하는 최소 Python 스크립트

## 문서 안내

- [저장소 안내서](docs/repository-handbook.md)
- [데이터 모델](docs/data-model.md)
- [파이프라인 개요](docs/evidence-pipeline.md)
- [온톨로지 설계 근거](docs/ontology-rationale.md)

## 공개본의 성격

이 저장소는 전체 연구 작업실의 mirror가 아닙니다. 전체 corpus thin RAG나 리뷰 운영 도구를 포함한 작업 환경은 별도로 유지되며, 여기에는 **논문에서 직접 확인 가능한 파일럿 결과와 그 근거 구조**만 남깁니다. 다만 reviewed chunk를 다시 생성할 수 있도록 Hangzhou gold set 10건에 해당하는 seed entry chunk만 최소 입력으로 포함합니다.

## 라이선스 및 이용 안내

이 저장소의 코드에는 MIT 라이선스가 적용됩니다. 다만 문서, 번역, annotation, authority, assertion, graph를 포함한 비코드 연구 자료는 MIT 적용 대상이 아니며, 정식 논문 출판 전까지 재사용이 허용되지 않습니다.

- 코드 라이선스: [LICENSE](LICENSE)
- 비코드 자료 이용 안내: [DATA_AND_DOCS_NOTICE.md](DATA_AND_DOCS_NOTICE.md)
