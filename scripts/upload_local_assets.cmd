@echo off
setlocal
REM Run this from the extracted Kural upload package folder on Windows.
where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: Git is not installed or is not on PATH.
  pause
  exit /b 1
)
if not exist "phrase_model_v23.joblib" (
  echo ERROR: phrase_model_v23.joblib not found next to this script.
  pause
  exit /b 1
)
if exist "Kural_Git\.git" (
  echo Existing Kural_Git checkout found; pulling latest changes...
  git -C Kural_Git pull --ff-only || goto :fail
) else (
  git clone https://github.com/Nagasiv-cyber/Kural.git Kural_Git || goto :fail
)
copy /Y "phrase_model_v23.joblib" "Kural_Git\phrase_model_v23.joblib" >nul || goto :fail
if exist "docs" (
  xcopy /E /I /Y "docs" "Kural_Git\docs" >nul || goto :fail
)
cd Kural_Git || goto :fail
git add phrase_model_v23.joblib docs
git diff --cached --quiet
if not errorlevel 1 (
  echo No new files to push.
  goto :done
)
git commit -m "Add trained FlexVoice model and project documentation" || goto :fail
git push origin main || goto :fail
:done
echo.
echo Upload complete. Visit https://github.com/Nagasiv-cyber/Kural
pause
exit /b 0
:fail
echo.
echo An error occurred. Check GitHub sign-in and terminal output.
pause
exit /b 1
