# Personal Site  

## previerw on linux  
[jekyll on ubuntu](https://jekyllrb.com/docs/installation/ubuntu/)  
```
# install  
sudo apt-get install ruby-full build-essential zlib1g-dev

# 
echo '# Install Ruby Gems to ~/gems' >> ~/.bashrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

gem install jekyll bundler
```

## preview on Windows  
[Testing your GitHub Pages site locally with Jekyll](https://docs.github.com/zh/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)  

### Prerequisites
```
1. [Ruby+Devkit](https://rubyinstaller.org/downloads/)  
ruby -v  
gem -v  
gcc -v  
g++ -v  
make -v  

2. gem install jekyll bundler
```

## command  
```
cd docs  
bundle install  
bundle exec jekyll serve  
bundle exec jekyll serve --host 192.168.8.60
```
