# Creator Control Center

멀티 채널 크리에이터와 관리자, 플랫폼 운영자를 위한 통합 분석 웹 애플리케이션입니다. 인스타그램, 쓰레드, 유튜브, 트위터/X, 틱톡, 페이스북과 메타 광고 계정의 성장 현황을 한 화면에서 확인할 수 있는 대시보드를 제공합니다.

## 기능

- 이메일 기반 회원가입 및 로그인 (크리에이터, 관리자, 제작자 권한)
- 무료 계정 1개 + 구독 티어별 추가 채널 관리
- 관리자 승인 기반의 크리에이터-관리자 연결 워크플로우
- 최근 게시물, 구독자 증가율, 참여율 등 채널별 요약 스냅샷
- 플랫폼 제작자를 위한 슈퍼 관리자 제어판
- 한국어/영어/일본어 로컬라이제이션 파일 분리 관리
- 스타트업 감성의 반응형 UI

## 실행 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`으로 접속합니다.

## Docker & Google Cloud Run 배포

```bash
docker build -t creator-control-center .
docker run -p 8080:8080 creator-control-center
```

Cloud Run에 배포 시 `Dockerfile`을 그대로 사용하면 됩니다.
