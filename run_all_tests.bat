@echo off
echo 🧪 모든 모델 테스트 자동 실행 시작 (7개 모델)...
echo.

REM 시작 시간 기록
echo 시작 시간: %date% %time%
echo.

echo 🔍 1/7 KoBERT 테스트 실행 중...
cd envs\kobert_env
call Scripts\activate.bat
python ..\..\tests\test_kobert.py > ..\..\results\kobert_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoBERT 테스트 완료!

echo.
echo 🔍 2/7 BERT 테스트 실행 중...
cd envs\bert_env
call Scripts\activate.bat
python ..\..\tests\test_bert.py > ..\..\results\bert_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ BERT 테스트 완료!

echo.
echo 🔍 3/7 RoBERTa 테스트 실행 중...
cd envs\roberta_env
call Scripts\activate.bat
python ..\..\tests\test_roberta.py > ..\..\results\roberta_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ RoBERTa 테스트 완료!

echo.
echo 🔍 4/7 KoELECTRA 테스트 실행 중...
cd envs\koelectra_env
call Scripts\activate.bat
python ..\..\tests\test_koelectra.py > ..\..\results\koelectra_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoELECTRA 테스트 완료!

echo.
echo 🔍 5/7 KoGPT 테스트 실행 중...
cd envs\kogpt_env
call Scripts\activate.bat
python ..\..\tests\test_kogpt.py > ..\..\results\kogpt_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoGPT 테스트 완료!

echo.
echo 🔍 6/7 KoSimCSE 테스트 실행 중...
cd envs\kosimcse_env
call Scripts\activate.bat
python ..\..\tests\test_kosimcse.py > ..\..\results\kosimcse_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ KoSimCSE 테스트 완료!

echo.
echo 🔍 7/7 기존 툴들 테스트 실행 중...
cd envs\existing_tools_env
call Scripts\activate.bat
python ..\..\tests\test_existing.py > ..\..\results\existing_results.txt 2>&1
call Scripts\deactivate.bat
cd ..\..
echo ✅ 기존 툴 테스트 완료!

echo.
echo 📊 결과 통합 분석 중...
python compare_all.py > results\comparison_summary.txt
echo ✅ 분석 완료!

echo.
echo 종료 시간: %date% %time%
echo.
echo 🎉 모든 테스트 완료! (7개 모델)
echo.
echo 📋 결과 확인:
echo   - results\kobert_results.txt
echo   - results\bert_results.txt
echo   - results\roberta_results.txt
echo   - results\koelectra_results.txt
echo   - results\kogpt_results.txt        [NEW]
echo   - results\kosimcse_results.txt     [NEW]
echo   - results\existing_results.txt
echo   - results\comparison_summary.txt
echo.
echo 📊 요약 보기: type results\comparison_summary.txt
echo.
pause