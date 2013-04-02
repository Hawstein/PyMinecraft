# coding: utf-8
# 加入上面一句才能使用中文注释
from pyglet.gl import * # OpenGL,GLU接口
from pyglet.window import key # 键盘常量，事件
from ctypes import c_float # 导入c类型的float
import math
import random
import time

SECTOR_SIZE = 16

# 返回以x,y,z为中心，边长为2n的正方体六个面的顶点坐标
def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

# 纹理坐标
# 给出纹理图左下角坐标，返回一个正方形纹理的四个顶点坐标
# 由于纹理图可看成4*4的纹理patch，所以n=4(图中实际有6个patch,其它空白)
# 比如，欲返回左下角的那个正方形纹理patch，
# 输入是左下角的整数坐标(0,0)
# 输出是0,0, 1/4,0, 1/4,1/4, 0,1/4
def tex_coord(x, y, n=4):
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

# 计算一个正方体6个面的纹理贴图坐标
# top,bottom和4个侧面(side)共6个
# 将结果放入一个list中
def tex_coords(top, bottom, side):
    top = tex_coord(*top) # 将元组(x, y)分为x, y作为函数参数
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top) # extend用来连接两个list
    result.extend(bottom)
    result.extend(side * 4)
    return result

# 计算草块，沙块，砖块，石块6个面的纹理贴图坐标(用一个list保存)
# 可以看出除了草块，其他的正方体六个而的贴图都一样
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))

# 当前位置向6个方向移动1个单位要用到的增量坐标
FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

class TextureGroup(pyglet.graphics.Group):
    def __init__(self, path):
        super(TextureGroup, self).__init__()
        # 将纹理图载入显存
        self.texture = pyglet.image.load(path).get_texture()
    # 重写父类中的两个方法
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
    def unset_state(self):
        glDisable(self.texture.target)

# 对位置x,y,z取整
def normalize(position):
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

# 先将位置坐标x,y,z取整，然后各除以SECTOR_SIZE,返回x,0,z
# 会将许多不同的position映射到同一个(x,0,z)
# 一个(x,0,z)对应一个x*z*y=16*16*y的区域内的所有立方体中心position
def sectorize(position):
    x, y, z = normalize(position)
    x, y, z = x / SECTOR_SIZE, y / SECTOR_SIZE, z / SECTOR_SIZE
    return (x, 0, z) # 得到的是整数坐标

class Model(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.group = TextureGroup('texture.png') # 载入纹理贴图
        self.world = {} # 字典：position:texture的键值对，存在于地图中所有立方体的信息
        self.shown = {} # 字典：position:texture的键值对，显示出来的立方体
        self._shown = {} # 字典：postion:VertexList键值对，VertexList被批量渲染
        self.sectors = {} # 字典：(x,0,z):[position1,position2...]键值对
        self.queue = [] # 用于存储事件的队列
        self.initialize() # 画出游戏地图
    # 画地图，大小80*80
    def initialize(self):
        n = 80 # 地图大小
        s = 1 # 步长
        y = 0
        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s):
                # 在地下画一层石头，上面是一层草地
                # 地面从y=-2开始
                self.init_block((x, y - 2, z), GRASS)
                self.init_block((x, y - 3, z), STONE)
                # 地图的四周用墙围起来
                if x in (-n, n) or z in (-n, n):
                    for dy in xrange(-2, 3):
                        self.init_block((x, y + dy, z), STONE)
        o = n - 10 # 为了避免建到墙上，o取n-10
        # 在地面上随机建造一些草块，沙块，砖块
        for _ in xrange(120): # 只想迭代120次，不需要迭代变量i，直接用 _
            a = random.randint(-o, o) # 在[-o,o]内随机取一个整数
            b = random.randint(-o, o)
            c = -1
            h = random.randint(1, 6)
            s = random.randint(4, 8)
            d = 1
            t = random.choice([GRASS, SAND, BRICK]) # 随机选择一个纹理
            for y in xrange(c, c + h):
                for x in xrange(a - s, a + s + 1):
                    for z in xrange(b - s, b + s + 1):
                        if (x - a) ** 2 + (z - b) ** 2 > (s + 1) ** 2:
                            continue
                        if (x - 0) ** 2 + (z - 0) ** 2 < 5 ** 2:
                            continue
                        self.init_block((x, y, z), t)
                s -= d
    # 检测鼠标是否能对一个立方体进行操作。
    # 返回key,previous：key是鼠标可操作的块(中心坐标)，根据人所在位置和方向向量求出，
    # previous是与key处立方体相邻的空位置的中心坐标。
    # 如果返回非空，点击鼠标左键删除key处立方体，
    # 点击鼠标右键在previous处添加砖块。
    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m): # 迭代8*8=64次
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
    # 只要position周围6个面有一个没有立方体(exposed了)，返回真值，表示要绘制position处的立方体
    # 如果6个面都被立方体包围(没有exposed)，position处的立方体就可以不绘制
    # 因为绘制了也看不到
    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    # 初始化地图时调用它，但不会同步地绘制出来sync=false
    # 而是全部添加完一次性绘制
    def init_block(self, position, texture):
        self.add_block(position, texture, False)
    # 添加立方体
    def add_block(self, position, texture, sync=True):
        if position in self.world: # 如果position已经存在于world中，要先移除它
            self.remove_block(position, sync)
        self.world[position] = texture # 添加相应的位置和纹理
        # 以区域为一组添加立方体的position到字典中，
        # 16*16*y区域内的立方体都映射到一个键值,这些立方体position以tuble形式存在于一个列表中
        self.sectors.setdefault(sectorize(position), []).append(position)
        if sync: # 初始时该变量为false，不会同步绘制
            if self.exposed(position): # 如果同步绘制，且该位置是显露在外的
                self.show_block(position) # 绘制该立方体
            self.check_neighbors(position)
    # 删除立方体
    def remove_block(self, position, sync=True):
        del self.world[position] # 把world中的position,texture对删除
        self.sectors[sectorize(position)].remove(position) # 把区域中相应的position删除
        if sync: # 如果同步
            if position in self.shown: # 如果position在显示列表中
                self.hide_block(position) # 立即删除它
            self.check_neighbors(position)
    # 删除一个立方体后，要检查它周围6个邻接的位置
    # 是否有因此暴露出来的立方体，有的话要把它绘制出来
    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES: # 检查周围6个位置
            key = (x + dx, y + dy, z + dz)
            if key not in self.world: # 如果该处没有立方体，过
                continue
            if self.exposed(key): # 如果该处有立方体且暴露在外
                if key not in self.shown: # 且没有在显示列表中
                    self.show_block(key) # 则立即绘制出来
            else: # 如果没有暴露在外，而又在显示列表中，则立即隐藏(删除)它
                if key in self.shown: 
                    self.hide_block(key)
    # 将world中还没显示且显露在外的立方体绘制出来
    def show_blocks(self):
        for position in self.world:
            if position not in self.shown and self.exposed(position):
                self.show_block(position)
    # 显示立方体
    def show_block(self, position, immediate=True):
        texture = self.world[position] # 取出纹理(其实是6个面的纹理坐标信息)
        self.shown[position] = texture # 存入shown字典中
        if immediate: # 立即绘制
            self._show_block(position, texture)
        else: # 不立即绘制，进入事件队列
            self.enqueue(self._show_block, position, texture)
    # 添加顶点列表(VertexList)到渲染对象，(on_draw会指渲染它)
    # 并将position:VertexList对存入_shown
    def _show_block(self, position, texture):
        x, y, z = position
        # only show exposed faces
        # 只显示看得见的面
        index = 0
        count = 24
        # 中心为x,y,z的1*1*1正方体
        # 顶点坐标数据和纹理坐标数据
        vertex_data = cube_vertices(x, y, z, 0.5) 
        texture_data = list(texture)
        for dx, dy, dz in []:#FACES: 作者注释掉了FACES，此for循环不执行，即所有面都绘制
            if (x + dx, y + dy, z + dz) in self.world:
                count -= 4
                i = index * 12
                j = index * 8
                del vertex_data[i:i + 12]
                del texture_data[j:j + 8]
            else:
                index += 1
        # create vertex list
        # 添加顶点列表(VertexList)到批渲染对象中
        # 顶点数目count=24(6个面，一个面4个点)
        self._shown[position] = self.batch.add(count, GL_QUADS, self.group, 
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
    # 隐藏立方体
    def hide_block(self, position, immediate=True):
        self.shown.pop(position) # 将要隐藏的立方体中心坐标从显示列表中移除
        if immediate: # 立即移除，从图上消失
            self._hide_block(position)
        else: # 不立即移除，进行事件队列等待处理
            self.enqueue(self._hide_block, position)
    # 立即移除立方体
    # 将position位置的顶点列表弹出并删除，相应的立方体立即被移除(其实是在update之后)
    def _hide_block(self, position):
        self._shown.pop(position).delete()
    # 绘制一个区域内的立方体
    # 如果区域内的立方体位置没在显示列表，且位置是显露在外的，则显示立方体
    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False) # 放入队列，并不立即绘制
    # 隐藏区域
    # 如果一个立方体是在显示列表中的，则隐藏它，
    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False) # 放入事件队列，不会立即隐藏
    
    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]: # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)
    # 添加事件到队列queue
    def enqueue(self, func, *args):
        self.queue.append((func, args))
    # 处理队头事件
    def dequeue(self):
        func, args = self.queue.pop(0)
        func(*args)
    # 用1/60秒的时间来处理队列中的事件
    # 不一定要处理完
    def process_queue(self):
        start = time.clock()
        while self.queue and time.clock() - start < 1 / 60.0:
            self.dequeue()
    # 处理事件队列中的所有事件
    def process_entire_queue(self):
        while self.queue:
            self.dequeue()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        # *args,化序列为位置参数：(1,2) -> func(1,2)
        # **kwargs,化字典为关键字参数：{'a':1,'b':2} -> func(a=1,b=2)
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False # 初始时，鼠标事件没有绑定到游戏窗口
        self.flying = False
        self.strafe = [0, 0] # [z, x]，z表示前后运动，x表示左右运动
        self.position = (0, 0, 0) # 开始位置在地图中间
        # rotation(水平角x，俯仰角y)
        # 水平角是方向射线xoz上的投影与z轴负半轴的夹角
        # 俯仰角是方向射线与xoz平面的夹角
        self.rotation = (0, 0)
        # 
        self.sector = None
        # reticle表示游戏窗口中间的那个十字
        # 四个点，绘制成两条直线
        self.reticle = None 
        self.dy = 0
        self.inventory = [BRICK, GRASS, SAND] # 可以建造的类型
        self.block = self.inventory[0] # 初始时右键建造的是砖块
        self.num_keys = [ # 数字键响应，用于建造类型的切换
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        self.model = Model()
        # 游戏窗口左上角的label参数设置
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', 
            color=(0, 0, 0, 255))
        pyglet.clock.schedule_interval(self.update, 1.0 / 60)# 每秒刷新60次
    # 设置鼠标事件是否绑定到游戏窗口
    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    # 根据前进方向rotation来决定移动1单位距离时，各轴分量移动多少
    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y)) # cos(y)
        dy = math.sin(math.radians(y)) # sin(y)
        dx = math.cos(math.radians(x - 90)) * m # sin(x)cos(y)
        dz = math.sin(math.radians(x - 90)) * m # -cos(x)cos(y)
        return (dx, dy, dz)
    # 运动时计算三个轴的位移增量
    def get_motion_vector(self):
        if any(self.strafe): # 只要strafe中有一项为真(不为0)，就执行:
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe)) # arctan(z/x)，再转换成角度
            if self.flying: # 如果允许飞，那么运动时会考虑垂直方向即y轴方向的运动
                m = math.cos(math.radians(y)) # cos(y)
                dy = math.sin(math.radians(y)) # sin(y)
                if self.strafe[1]: # 如果x不为0
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0: # 如果z大于0
                    dy *= -1
                dx = math.cos(math.radians(x + strafe)) * m
                dz = math.sin(math.radians(x + strafe)) * m
            else:
                dy = 0.0
                dx = math.cos(math.radians(x + strafe))
                dz = math.sin(math.radians(x + strafe))
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)
    # 每1/60秒调用一次进行更新
    def update(self, dt):
        self.model.process_queue() # 用1/60的时间来处理队列中的事件，不一定要处理完
        sector = sectorize(self.position)
        if sector != self.sector: # 如果position的sector与当前sector不一样
            self.model.change_sectors(self.sector, sector)
            if self.sector is None: # 如果sector为空
                self.model.process_entire_queue() # 处理队列中的所有事件
            self.sector = sector # 更新sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)
    # 更新self.dy和self.position
    def _update(self, dt):
        # walking
        speed = 15 if self.flying else 5 # 如果能飞，速度15；否则为5
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity # 如果不能飞，则使其在y方向上符合重力规律
        if not self.flying:
            self.dy -= dt * 0.044 # g force, should be = jump_speed * 0.5 / max_jump_height
            self.dy = max(self.dy, -0.5) # terminal velocity
            dy += self.dy
        # collisions
        x, y, z = self.position
        # 碰撞检测后应该移动到的位置
        x, y, z = self.collide((x + dx, y + dy, z + dz), 2) 
        self.position = (x, y, z) # 更新位置
    # 碰撞检测
    # 返回的p是碰撞检测后应该移动到的位置
    # 如果没有遇到障碍物，p仍然是position；
    # 否则，p是新的值(会使其沿着墙走，或不支)
    def collide(self, position, height):
        pad = 0.25
        p = list(position) # 将元组变为list
        np = normalize(position) # 取整
        for face in FACES: # 检查周围6个面的立方体
            for i in xrange(3): # (x,y,z)中每一维单独检测
                if not face[i]: # 如果为0，过
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad: #
                    continue
                for dy in xrange(height): # 检测每个高度
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    op = tuple(op)
                    if op not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        self.dy = 0
                    break
        return tuple(p)
    # 第一句直接return，所以此函数不做任何事
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return
        x, y, z = self.position
        dx, dy, dz = self.get_sight_vector()
        d = scroll_y * 10
        self.position = (x + dx * d, y + dy * d, z + dz * d)
    # 鼠标按下事件
    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive: # 当鼠标事件已经绑定了此窗口
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == pyglet.window.mouse.LEFT:
                if block: # 如果按下左键且该处有block
                    texture = self.model.world[block]
                    if texture != STONE: # 如果block不是石块，就移除它
                        self.model.remove_block(block)
            else: # 如果按下右键，且有previous位置，则在previous处增加方块
                if previous:
                    self.model.add_block(previous, self.block)
        else: # 否则隐藏鼠标，并绑定鼠标事件到该窗口
            self.set_exclusive_mouse(True)
    # 鼠标移动事件，处理视角的变化
    # dx,dy表示鼠标从上一位置移动到当前位置x，y轴上的位移
    # 该函数将这个位移转换成了水平角x和俯仰角y的变化
    # 变化幅度由参数m控制
    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:  # 在鼠标绑定在该窗口时
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y)) # 限制仰视和俯视角y只能在-90度和90度之间
            self.rotation = (x, y)
    # 按下键盘事件，长按W，S，A，D键将不断改变坐标
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W: # opengl坐标系：z轴垂直平面向外，x轴向右，y轴向上
            self.strafe[0] -= 1 # 向前：z坐标-1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A: # 向左：x坐标-1
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = 0.015 # jump speed
        elif symbol == key.ESCAPE: # 鼠标退出当前窗口
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB: # 切换是否能飞，即是否可以在垂直方向y上运动
            self.flying = not self.flying
        elif symbol in self.num_keys: 
            index = (symbol - self.num_keys[0]) % len(self.inventory) # 0,1,2
            self.block = self.inventory[index] # 取得相应的方块类型
    # 释放按键事件
    def on_key_release(self, symbol, modifiers):
        if symbol == key.W: # 按键释放时，各方向退回一个单位
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
    # 窗口大小变化响应事件
    def on_resize(self, width, height):
        # label的纵坐标
        self.label.y = height - 10
        # reticle更新，包含四个点，绘制成两条直线
        if self.reticle:
            self.reticle.delete()
        x, y = self.width / 2, self.height / 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )
    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
    # 重写Window的on_draw函数
    # 当窗口需要被重绘时，事件循环(EventLoop)就会调度该事件
    def on_draw(self):
        self.clear()
        self.set_3d() # 进入3d模式
        glColor3d(1, 1, 1)
        self.model.batch.draw() # 将batch中保存的顶点列表绘制出来
        self.draw_focused_block() # 绘制鼠标focus的立方体的线框
        self.set_2d() # 进入2d模式
        self.draw_label() # 绘制label
        self.draw_reticle() # 绘制窗口中间的十字
    # 画出鼠标focus的立方体，在它的外层画个立方体线框
    def draw_focused_block(self):
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    def draw_label(self): # 显示帧率，当前位置坐标，显示的方块数及总共的方块数
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z, 
            len(self.model._shown), len(self.model.world))
        self.label.draw() # 绘制label的text
    # 绘制游戏窗口中间的十字，一条横线加一条竖线
    def draw_reticle(self):
        glColor3d(0, 0, 1)
        self.reticle.draw(GL_LINES)

def setup_fog(): # 设置雾效果
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (c_float * 4)(0.53, 0.81, 0.98, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_DENSITY, 0.35)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.53, 0.81, 0.98, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog() # 设置雾效果

def main():
    window = Window(width=800, height=600, caption='Pyglet', resizable=True) # 创建游戏窗口
    window.set_exclusive_mouse(True) # 隐藏鼠标光标，将所有的鼠标事件都绑定到此窗口
    setup() # 设置
    pyglet.app.run() # 运行，开始监听并处理事件

if __name__ == '__main__':
    main()
