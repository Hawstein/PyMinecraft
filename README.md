# Minecraft

这是用Python和Pyglet写的简单的Minecraft游戏，
从<https://github.com/fogleman/Minecraft>fork过来的，
一共只有几百行代码，麻雀虽小，五脏俱全，觉得挺有意思的，
于是把源码读了一遍，并做了详细的注释。
通过这个例子学习Pyglet和Python游戏编程还是不错的，推荐。

以下是游戏视频：

http://www.youtube.com/watch?v=kC3lwK631X8

## How to Run

    pip install pyglet
    git clone https://github.com/fogleman/Minecraft.git
    cd Minecraft
    python main.py

On Mac OS X, you may have an issue with running Pyglet in 64-bit mode. Try this...

    arch -i386 python main.py
