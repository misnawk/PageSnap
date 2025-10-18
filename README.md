# 📚 E-book 자동 텍스트 추출기

e-book의 페이지를 자동으로 감지하여 스크린샷을 캡처하고 텍스트를 추출하는 프로그램입니다.

## 주요 기능

###  마우스로 캡처 영역 선택
- 드래그로 쉽게 캡처 영역 설정
- 설정 자동 저장 및 불러오기
- 전체 화면, 중앙 영역 등 빠른 설정

###  자동 페이지 변화 감지
- 페이지가 변할 때 자동으로 감지하여 캡처
- 민감도 조절 가능 (권장: 3-7%)
- 실시간 변화율 표시

###  실시간 미리보기
- 캡처된 스크린샷을 즉시 확인
- 페이지 번호와 크기 정보 표시

###  PDF 내보내기
- 캡처한 모든 스크린샷을 하나의 PDF로 정리
- A4 크기로 자동 최적화
- 페이지 번호 자동 추가

###  텍스트 추출 (OCR)
- Tesseract OCR을 이용한 텍스트 추출
- 한글+영문 동시 지원
- 추출된 텍스트 자동 저장

## 설치 방법

### 1. 필수 프로그램 설치

#### Python (3.8 이상)
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드

#### Tesseract OCR
- Windows: [Tesseract 설치 파일](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드
- 설치 후 경로를 `ebook_ocr_gui.py` 파일에서 설정:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 1. 프로그램 실행
```bash
python ebook_ocr_gui.py
```

### 2. 캡처 영역 설정
1. "마우스로 영역 선택" 버튼 클릭
2. 3초 후 화면이 반투명하게 변함
3. e-book 영역을 마우스로 드래그하여 선택
4. 영역이 자동으로 저장됨

### 3. 자동 감지 시작
1. 설정 조정:
   - 확인 간격: 화면을 확인하는 주기 (기본 0.5초)
   - 민감도: 낮을수록 작은 변화도 감지 (권장 3-7%)
2. "자동 페이지 변화 감지 시작" 버튼 클릭
3. e-book을 열고 준비되면 확인 클릭
4. 페이지를 넘기면 자동으로 캡처됨

### 4. PDF로 내보내기
1. "PDF로 내보내기" 버튼 클릭
2. 저장 위치와 파일명 선택
3. PDF 자동 생성

## 폴더 구조

```
독서도우미/
├── ebook_ocr_gui.py        # 메인 프로그램
├── README.md               # 사용 설명서
├── requirements.txt        # 필요한 패키지 목록
├── config/                 # 설정 파일
│   └── capture_config.json # 캡처 영역 설정
├── output/                 # 출력 파일
│   ├── screenshots/        # 캡처된 이미지
│   ├── text/              # 추출된 텍스트
│   └── pdf/               # 생성된 PDF
└── archive/               # 사용하지 않는 파일
```

## 문제 해결

### 페이지가 감지되지 않을 때
1. 상태창에서 변화율 확인
2. 변화율이 낮으면 민감도 값을 낮춤 (예: 3 또는 2)
3. 캡처 영역이 올바른지 확인

### Tesseract 오류가 날 때
1. Tesseract가 설치되어 있는지 확인
2. 코드에서 Tesseract 경로 설정:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'설치경로\tesseract.exe'
   ```

### 한글이 인식되지 않을 때
1. Tesseract 설치 시 한글 언어 팩 선택
2. 또는 별도로 설치:
   - [한글 언어 데이터](https://github.com/tesseract-ocr/tessdata/blob/main/kor.traineddata) 다운로드
   - `Tesseract-OCR\tessdata` 폴더에 복사

## 단축키

- **ESC**: 영역 선택 취소
- **중지 버튼**: 자동 감지 중지

## 라이선스

이 프로젝트는 개인적인 용도로 자유롭게 사용 가능합니다.

## 업데이트 내역

### v1.0 (2025-10-12)
- 초기 버전 출시
- 마우스 드래그 영역 선택 기능
- 자동 페이지 변화 감지
- 실시간 미리보기
- PDF 내보내기
- 텍스트 추출 (OCR)
