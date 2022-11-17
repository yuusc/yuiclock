# -*- coding: utf-8 -*-
import tkinter
from datetime import datetime, timedelta, timezone
import requests

# セグの太さ
SEG_WIDTH = 20

# 数字表示用のキャンバスのサイズの設定
CANVAS_WIDTH_NUMBER = 100

# コロン表示用のキャンバスのサイズ
CANVAS_WIDTH_COLON = 50

# 色の設定
COLOR_BG = "black"  # 時計の背景色
COLOR_SEG_ON = "orange"  # セグ点灯時の色
COLOR_SEG_OFF = "gray20"  # セグ消灯時の色


class ColonCanvas(tkinter.Canvas):
    '''コロンを表現する図形を描画するキャンバス'''

    canvas_width = CANVAS_WIDTH_COLON
    canvas_height = CANVAS_WIDTH_NUMBER * 2 - SEG_WIDTH

    def __init__(self, master, **kw):
        super().__init__(master, kw)

    def draw(self):
        '''コロンを長方形として描画する'''

        for i in range(2):
            # 横方向の中心はキャンバスの中心
            center_x = ColonCanvas.canvas_width / 2

            # 縦方向の中心はキャンバスの1/3 or 2/3の位置
            center_y = (i + 1) * ColonCanvas.canvas_height / 3

            # 長方形の確変の長さが20となるように座標を設定
            x1 = center_x - 10
            y1 = center_y - 10
            x2 = center_x + 10
            y2 = center_y + 10

            # 長方形を描画
            self.create_rectangle(
                x1, y1, x2, y2,
                fill=COLOR_SEG_ON,
                width=0
            )


class NumberCanvas(tkinter.Canvas):
    '''数字を表現するセグを描画するキャンバス'''

    # 各種パラメータの設定
    canvas_width = CANVAS_WIDTH_NUMBER
    seg_width = SEG_WIDTH
    canvas_height = canvas_width * 2 - seg_width
    seg_length = canvas_width - seg_width

    # 数字をセグ表示する際の、各セグの点灯or消灯の情報のリスト
    ON_OFF_INFOS = [
        # 上, 上左, 上右, 中, 下左, 下右, 下
        [True, True, True, False, True, True, True],  # 0
        [False, False, True, False, False, True, False],  # 1
        [True, False, True, True, True, False, True],  # 2
        [True, False, True, True, False, True, True],  # 3
        [False, True, True, True, False, True, False],  # 4
        [True, True, False, True, False, True, True],  # 5
        [True, True, False, True, True, True, True],  # 6
        [True, True, True, False, False, True, False],  # 7
        [True, True, True, True, True, True, True],  # 8
        [True, True, True, True, False, True, True]  # 9
    ]

    # 各セグを描画するときの情報のリスト
    SEG_DRAW_PARAMS = [
        # [回転するか？, 横方向の移動量, 縦方向の移動量]
        [False, canvas_width / 2, seg_width / 2],
        [True, seg_width / 2, canvas_height / 2 - seg_length / 2],
        [True, canvas_width - seg_width / 2,
         canvas_height / 2 - seg_length / 2],
        [False, canvas_width / 2, canvas_height / 2],
        [True, seg_width / 2, canvas_height / 2 + seg_length / 2],
        [True, canvas_width - seg_width / 2,
         canvas_height / 2 + seg_length / 2],
        [False, canvas_width / 2, canvas_height - seg_width / 2]
    ]

    # 基準セグの各頂点のx座標
    XS = [
        - canvas_width / 2 + seg_width,  # 左上
        - canvas_width / 2 + seg_width / 2,  # 左中
        - canvas_width / 2 + seg_width,  # 左下
        canvas_width / 2 - seg_width,  # 右下
        canvas_width / 2 - seg_width / 2,  # 右中
        canvas_width / 2 - seg_width  # 右上
    ]

    # 基準セグの各頂点のy座標
    YS = [
        - seg_width / 2,  # 左上
        0,  # 左中
        seg_width / 2,  # 左下
        seg_width / 2,  # 右下
        0,  # 右中
        - seg_width / 2  # 右上
    ]

    def __init__(self, master, **kw):
        super().__init__(master, kw)

        # 描画した六角形のIDを管理するリスト
        self.segs = []

    def draw(self):
        '''セグを描画する'''

        # 描画時のパラメータに従ってセグを描画
        for draw_param in NumberCanvas.SEG_DRAW_PARAMS:

            is_rotate, x_shift, y_shift = draw_param

            if is_rotate:
                # 回転必要な場合は、基準セグの頂点の座標をを９０度を回転
                r_xs = [-n for n in NumberCanvas.YS]
                r_ys = [n for n in NumberCanvas.XS]

            else:
                # 回転不要な場合は基準セグの頂点の座標をそのまま使用
                r_xs = NumberCanvas.XS
                r_ys = NumberCanvas.YS

            # 基準セグの各頂点を移動
            t_xs = [n + x_shift for n in r_xs]
            t_ys = [n + y_shift for n in r_ys]

            # 移動後の座標に六角形を描画
            seg = self.create_polygon(
                t_xs[0], t_ys[0],
                t_xs[1], t_ys[1],
                t_xs[2], t_ys[2],
                t_xs[3], t_ys[3],
                t_xs[4], t_ys[4],
                t_xs[5], t_ys[5],
                fill=COLOR_SEG_OFF,
                width=0,
            )

            # 描画した六角形のIDをリストに格納
            self.segs.append(seg)

    def update(self, num):
        '''数字numをセグ表示する'''

        for seg, is_on in zip(self.segs, NumberCanvas.ON_OFF_INFOS[num]):

            if is_on:
                # 点灯する場合のセグの色
                color = COLOR_SEG_ON
            else:
                # 消灯する場合のセグの色
                color = COLOR_SEG_OFF

            # セグを表現する多角形の色を変更
            self.itemconfig(seg, fill=color)


class Timer:
    '''時刻を取得するクラス'''

    def __init__(self):

        # タイムゾーンの設定
        self.JST = timezone(timedelta(hours=9))

    def time(self):

        # 時刻の取得
        now = datetime.now(tz=self.JST)

        # 時・分・秒にわけて返却
        return now.hour, now.minute, now.second


class Drawer:
    '''時計を描画するクラス'''

    CANVAS_NUMBER = 1
    CANVAS_COLON = 2

    def __init__(self, master):

        # 各種設定を行なった後に時計の盤面を描画
        self.initSetting(master)
        self.createClock()

    def initSetting(self, master):
        '''時計描画に必要な設定を行う'''

        # ウィジェットの作成先を設定
        self.master = master

        # 作成するキャンバスの種類
        self.canvas_types = [
            Drawer.CANVAS_NUMBER,
            Drawer.CANVAS_NUMBER,
            Drawer.CANVAS_COLON,
            Drawer.CANVAS_NUMBER,
            Drawer.CANVAS_NUMBER,
            Drawer.CANVAS_COLON,
            Drawer.CANVAS_NUMBER,
            Drawer.CANVAS_NUMBER
        ]

        self.number_canvases = []
        self.colon_canvases = []

    def createClock(self):
        '''時計の盤面を作成する'''

        firsttime = True

        # 数字のセグ表示用のキャンバスとコロン表示用のキャンバスを作成
        for canvas_type in self.canvas_types:
            if firsttime:
                canvas2 = ColonCanvas(
                        self.master,
                        width=ColonCanvas.canvas_width * 17,
                        height=ColonCanvas.canvas_height,
                        bg=COLOR_BG,
                        highlightthickness=0,
                )
                canvas2.create_text(50, 50, text= "お知らせ",fill="white",font=('Helvetica 15 bold'))
                canvas2.create_text(100, 100, text= "Some Text",fill="white",font=('Helvetica 15 bold'), tag="information")
                canvas2.pack(side=tkinter.BOTTOM)
                firsttime = False

            if canvas_type == Drawer.CANVAS_NUMBER:

                # 数字のセグ表示用のキャンバスを作成
                canvas = NumberCanvas(
                    self.master,
                    width=NumberCanvas.canvas_width,
                    height=NumberCanvas.canvas_height,
                    bg=COLOR_BG,
                    highlightthickness=0,
                )
                self.number_canvases.append(canvas)

            else:
                # コロン表示用のキャンバスを作成
                canvas = ColonCanvas(
                    self.master,
                    width=ColonCanvas.canvas_width,
                    height=ColonCanvas.canvas_height,
                    bg=COLOR_BG,
                    highlightthickness=0,
                )
                self.colon_canvases.append(canvas)

            # 左から順番にpackで詰めていく
            canvas.pack(side=tkinter.LEFT, padx=10, pady=10)
            
            

        

    def draw(self):
        '''各キャンバスに描画する'''

        for canvas in self.colon_canvases:
            # コロンを描画するよう依頼
            canvas.draw()

        for canvas in self.number_canvases:
            # セグを描画するよう依頼
            canvas.draw()

    def update(self, hour, minute, second):
        '''セグ表示を更新する'''

        # 時刻を１桁ずつに分割する
        nums = []
        nums.append(hour // 10)
        nums.append(hour % 10)
        nums.append(minute // 10)
        nums.append(minute % 10)
        nums.append(second // 10)
        nums.append(second % 10)

        for canvas, num in zip(self.number_canvases, nums):
            # 各キャンバスに対応する数字numをセグ表示するように依頼
            canvas.update(num)


class DigitalClock:
    '''デジタル時計を実現するクラス'''

    lasthour = 0

    def __init__(self, master):

        # after実行用にウィジェットのインスタンスを保持
        self.master = master

        # 各種クラスのオブジェクトを生成
        self.timer = Timer()
        self.drawer = Drawer(master)

        # コロンとセグを描画する
        self.draw()

        # 時刻をセグ表示する
        self.update()

    def draw(self):
        '''コロンとセグを描画する'''

        self.drawer.draw()

    def update(self):
        '''時刻をセグ表示を更新する'''

        # 時刻を取得し、その時刻に合わせて針を進める
        hour, minute, second = self.timer.time()
        self.drawer.update(hour, minute, second)

        # １秒後に再度セグ表示を行う
        self.master.after(1000, self.update)

        if self.lasthour != hour
            url='https://nlp100.github.io/data/jawiki-country.json.gz'
            urlData = requests.get(url).content



if __name__ == "__main__":
    app = tkinter.Tk()

    # 背景色を設定
    app.config(bg=COLOR_BG)

    DigitalClock(app)
    app.mainloop()