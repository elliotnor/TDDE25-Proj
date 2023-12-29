## Getting started

Clone this repo and then remove the `.git` folder:
```
git clone https://gitlab.liu.se/tdde25/ctf
cd ctf
rm -rf .git
```
Then add your own git folder per the instructions on the TDDE25 git tutorial.


We also need to add the required libraries pymunk and pygame. We will do this using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) in Python, which allows us to create an isolated environment for our project instead of installing the libraries system-wide.

Create the environment by running:
```
python3 -m venv ctf-env
```
inside the project folder.

Then activate the environment:
```
source ctf-env/bin/activate
```

Now, install the required libraries:
```
pip install pymunk==5.7.0
pip install pygame==2.0.1
```

The environment will need to be activated in every new terminal that the project is run from. If using an IDE like VSCode it is recommended to [configure the interpreter](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment) for the project so that the environment is activated automatically.

Next go to our [wiki](https://gitlab.liu.se/tdde25/ctf/wikis/home) and get started on the tutorials.
