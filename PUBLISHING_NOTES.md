# Minimal Public Release Notes

이 폴더는 `YSD` GitHub 저장소에 올릴 **논문 부속 최소 공개본**입니다.

## 포함한 것

- 공개용 기준 문서
- 핵심 스키마 전체
- Hangzhou gold set annotation 10건
- reviewed chunk 재생성을 위한 seed entry chunk 10건
- reviewed chunk 10건
- dossier 8건
- assertion 27건
- graph node 26건 / edge 27건
- demo query 5건
- 결과물에서 실제로 참조되는 authority subset
  - person 13
  - place 16
  - office 6
  - institution 5
- 최소 재현 스크립트 (`phase_d_pipeline.py`, `run_public_pilot.py`)

## 제외한 것

- 전 코퍼스 thin RAG 전체
- review 원본 JSON
- 리뷰 웹 도구
- imported 읽기본
- spec 문서
- drafts, screenshots, 보조·정비 스크립트

## 공개 전 확인 포인트

- README와 handbook 수치가 실제 파일 수와 일치하는지 확인
- `LICENSE`와 `DATA_AND_DOCS_NOTICE.md`가 함께 존재하는지 확인
- GitHub 첫 화면에서 저장소가 “논문 부속 최소 공개본”으로 읽히는지 확인
