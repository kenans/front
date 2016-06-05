coffee -cj static/main.coffee.js static/main.coffee
python -c "import jsmin;jsm=jsmin.JavascriptMinify();version=open('version').readline().strip();jsm.minify(open('static/main.js'), open('static/main%s.js'%version,'w'))"
python -c "import cssmin;css=cssmin.cssmin(open('static/style.css').read());version=open('version').readline().strip();open('static/style%s.css'%version,'w').write(css)"
chmod 770 static/*
rsync -avz . rab:/var/www/rabb8/ --exclude=static/main.js --exclude=static/style.css --exclude=*.pyc --exclude=*.swp --exclude=setting.py --delete
