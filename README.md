# PyMinecraft by Hawstein

This is a simple Python and Pyglet written Minecraft game. The orignal code that I used as a basis from my program is from Fogelman https://github.com/fogleman/Minecraftfork. I found the aforementied link served as a very good foundation, so I took certain parts of it and made edits. 

## What to Expect
If you want to understand what Python/Pyglet Minecraft is, this youtube video will give you an idea as to what it is: 

http://www.youtube.com/watch?v=kC3lwK631X8

## How to Run 
First you must install pyglet using pip, this should be done in your terminal on your machine (ran by an adminstrator).  
  `  pip install pyglet`  
Next clone the respository.  
  `  git clone https://github.com/Hawstein/PyMinecraft.git`  
Change directories to PyMinecraft  
  `  cd PyMinecraft`  
Open up main.py using python  
  `  python main.py`
  
##### Additional Details

In Windows and Mac, Pyglet does not support 64 python, so for 64-bit Mac, you try:

	export VERSIONER_PYTHON_PREFER_32_BIT=yes
    arch -i386 python main.py
	

You can also use Pyglet with 64-bit support 1.2:

	pip install https://pyglet.googlecode.com/files/pyglet-1.2alpha1.tar.gz 
	
## Editing main.py
It is recommended that you use Visual Studio Code to edit your main.py file, PyCharm or any other IDE. Make sure all pull requests to this repository state what is 
being edited in details.
	
## How to Play 
The game is played through keyboard and mouse. Below are the commands.
  
### Moving

- W: Move forward
- S: Move backward
- A: Move left 
- D: Move right
- Mouse: Change perspective 
- Space: Jump
- Tab: Switching flight mode (flight mode is directly in the vertical direction of movement)
  
### Building

- Select the type of material you want to build with (Selecting either 1,2, or 3 will change the block you are using to build)
    - 1: Bricks
    - 2: Grass
    - 3: Sand
- Click the left mouse button: Remove the box
- Click the right mouse button: Add a square

### Exiting the Game

- ESC: Will close the game, and free your mouse
