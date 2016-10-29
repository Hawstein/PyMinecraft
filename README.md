# Minecraft
Written Minecraft game found at https://github.com/fogleman/Minecraftfork
This is a simple Python and Pyglet written Minecraft game. I found this code very interesting, so I took certain parts of it and made edits. 
This video is very good if you want to learn how to program in Pyglet and Python:
http://www.youtube.com/watch?v=kC3lwK631X8

## How to Run

    pip install pyglet
    git clone https://github.com/Hawstein/PyMinecraft.git
    cd PyMinecraft
    python main.py

In Windows and Mac, Pyglet does not support 64 python, so for 64-bit Mac, you can try:
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
    arch -i386 python main.py
	
You can also use Pyglet with 64-bit support 1.2:
	pip install https://pyglet.googlecode.com/files/pyglet-1.2alpha1.tar.gz 
	
## How to Play

### Moving

- W: Move forward
- S: Move backward
- A: Move left 
- D: Move right
- Mouse: Change perspective 
- Space: Jump
- Tab: Switching flight mode (flight mode is directly in the vertical direction of movement)

### Building

- Select the type of tile you want to build with 
    - 1: Bricks
    - 2: Grass
    - 3: Sand
- Click the left mouse button: Remove the box
- Click the right mouse button: Add a square

### Exit

- ESC: Release the mouse and close the window
