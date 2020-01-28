:loop
git pull
python pagegen.py
git add *
git commit -m "update content"
git push
timeout /t 300
goto :loop