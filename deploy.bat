@echo off
echo Starting deployment process...

echo Navigating to project directory...
cd /d "C:\Users\Prince Raj\Desktop\comestro\ecommerce-backend"

echo Collecting static files...
python manage.py collectstatic --noinput --clear

echo Running system checks...
python manage.py check

echo Deployment complete!
echo.
echo Next steps:
echo 1. Upload these changes to your server
echo 2. Run this script on your server
echo 3. Restart your web server
echo 4. Test the endpoints:
echo    - Home: https://backend.okpuja.in/
echo    - Swagger: https://backend.okpuja.in/swagger/
echo    - Admin: https://backend.okpuja.in/admin/

pause
