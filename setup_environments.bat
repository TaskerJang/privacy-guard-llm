 
@echo off
echo 🔧 모델별 가상환경 설치 시작...
echo.

REM 현재 위치 확인
if not exist "envs" (
    echo ❌ envs 폴더가 없습니다. privacy_guard_project 폴더에서 실행해주세요.
    pause
    exit /b 1
)

echo 📦 1/5 BERT 환경 설치 중...
cd envs\bert_env
python -m venv .
call Scripts\activate.bat
pip install --upgrade pip
pip install transformers torch tensorflow
pip freeze > ..\..\requirements\bert_requirements.txt
call Scripts\deactivate.bat
cd ..\..
echo ✅ BERT 환경 완료!

echo.
echo 📦 2/5 RoBERTa 환경 설치 중...
cd envs\roberta_env
python -m venv .
call Scripts\activate.bat
pip install --upgrade pip
pip install transformers torch
pip install fairseq
pip freeze > ..\..\requirements\roberta_requirements.txt
call Scripts\deactivate.bat
cd ..\..
echo ✅ RoBERTa 환경 완료!

echo.
echo 📦 3/5 KoBERT 환경 설치 중...
cd envs\kobert_env
python -m venv .
call Scripts\activate.bat
pip install --upgrade pip
pip install torch
pip install git+https://git@github.com/SKTBrain/KoBERT.git@master
pip install gluonnlp
pip install mxnet
pip freeze > ..\..\requirements\kobert_requirements.txt
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoBERT 환경 완료!

echo.
echo 📦 4/5 KoELECTRA 환경 설치 중...
cd envs\koelectra_env
python -m venv .
call Scripts\activate.bat
pip install --upgrade pip
pip install transformers torch
pip freeze > ..\..\requirements\koelectra_requirements.txt
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoELECTRA 환경 완료!

echo.
echo 📦 5/5 기존 툴들 환경 설치 중...
cd envs\existing_tools_env
python -m venv .
call Scripts\activate.bat
pip install --upgrade pip
pip install presidio-analyzer presidio-anonymizer
pip install spacy
python -m spacy download ko_core_news_sm
pip freeze > ..\..\requirements\existing_requirements.txt
call Scripts\deactivate.bat
cd ..\..
echo ✅ 기존 툴 환경 완료!

echo.
echo 🎉 모든 가상환경 설치 완료!
echo.
echo 📋 설치된 환경들:
echo   1. BERT: envs\bert_env
echo   2. RoBERTa: envs\roberta_env
echo   3. KoBERT: envs\kobert_env
echo   4. KoELECTRA: envs\koelectra_env
echo   5. 기존툴들: envs\existing_tools_env
echo.
echo 🚀 사용법:
echo   cd envs\kobert_env
echo   call Scripts\activate.bat
echo   python ..\..\tests\test_kobert.py
echo.
pause