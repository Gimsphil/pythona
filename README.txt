PythonA Runner 사용법

작성자 : PHIL JK
e-Mail : kacang@nate.com
H/P : +62 812 8094 3179

1) 실행
- D:\PythonA\run_pythona.bat

2) 주요 기능
- 파일 메뉴: 파일 불러오기, 저장, 다른 이름으로 저장
- 폴더 불러오기: 폴더 구조(.py 중심) 트리 표시
- 폴더 오픈 시 main.py/app.py/run.py/start.py/launcher.py 우선 자동 오픈
- 실행(F5): 현재 파일 저장 후 실행
- 중지(Shift+F5): 실행 중 프로세스 종료
- 버그 > 버그내용: 최근 오류(Traceback) 요약 보기
- 도움말 > 작성자 정보: 작성자 연락처 확인

3) 실행 실패 사유 안내
- 실행 실패 시 사유 팝업 표시
- 최근 STDERR/출력 요약 제공
- 로그 창에 단계별 진행상황 실시간 표시

4) 누락 모듈 자동 설치
- 실행 전 import 분석으로 필요한 모듈 누락 탐지
- 누락 모듈 리스트를 보여주고 사용자 승인 시 자동 pip 설치
- 설치 완료 후 자동으로 실행 재시도

5) Python 미설치 PC에서 실행
- 권장: PythonA_Runner.exe 사용
- EXE 빌드: D:\PythonA\build_standalone.bat
- run_pythona.bat는 PythonA_Runner.exe가 있으면 우선 실행

6) 더블클릭 연동(.py)
- D:\PythonA\register_py_click.bat 실행
- 이후 .py 파일 더블클릭 시 PythonA Runner가 파일 자동 로드/실행

7) 연동 해제
- D:\PythonA\unregister_py_click.bat 실행
