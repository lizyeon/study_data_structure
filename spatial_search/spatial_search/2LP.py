import math
import logging as log

import dto
import file_stream as fs
# import visualization as vs
from settings import TestConfig as config
import time
import datetime

GRID_WIDTH = config.GRID_WIDTH
GRID_HEIGHT = config.GRID_HEIGHT
TILE_SIZE = config.TILE_SIZE
RECS_SIZE = config.RECTANGLES_SIZE
TILE_NUM = config.TILE_NUM


def main():
    start = time.time()
    print('### Test Strarted ### - ', time.strftime('%H:%M:%S', time.localtime(start)))
    rects = fs.get_rects()
    rs = query_rects(rects)
    # rs = query_variation(rects)
    # rs = run()
    running_time = str(datetime.timedelta(seconds=time.time() - start)).split(".")
    running_time = running_time[0]
    print('### Test Terminaled [Runing time: ', running_time, '] - ', time.strftime('%H:%M:%S', time.localtime()),
          ' ###')
    header = dto.FileHeader('2LP','each rectangles',str(len(rects)),str(len(rects)),running_time)
    fs.out_result(header.get_header(), rs)

def query_variation(rects):
    rs = dict()
    sec_rects = indexing(rects)
    tiles = get_tiles()
    w_queries = fs.get_queries()
    for query in w_queries:
        if query == 1731:
            print('1731')
        tmp = filtering(rects, tiles, sec_rects, w_queries[query])
        rs_react = [int(x) for x in tmp]
        rs_react = sorted(rs_react)
        rs[query] = rs_react
        # vs.getResult(config, rects, w_queries[query], rs_react)
    print(rs)
    return rs


def query_rects(rects):
    rs = dict();
    sec_rects = indexing(rects)
    tiles = get_tiles()
    for rect in rects:
        # if rects[rect].id == 188:
        #     print(rects[rect].id)
        w_xl = rects[rect].xL
        w_yl = rects[rect].yL
        w_xu = rects[rect].xU
        w_yu = rects[rect].yU
        w_query = dto.Quardrate(w_xl, w_yl, w_xu, w_yu)
        rs_react = filtering(rects, tiles, sec_rects, w_query)
        rs[rects[rect].id] = rs_react
        # if rects[rect].id == 1:
        #     vs.getResult(config, rects, w_query, rs_react)
    # print(rs)
    return rs


def run():
    rects = []

    tiles = get_tiles()

    rects.append(dto.Rectangle(0, 386, 283, 406, 303))
    rects.append(dto.Rectangle(1, 408, 277, 428, 297))
    rects.append(dto.Rectangle(2, 361, 266, 381, 286))

    print(rects)

    w_xl = 345
    w_yl = 311
    w_xu = 423
    w_yu = 350

    sec_rects = indexing(rects)
    w_query = dto.Quardrate(w_xl, w_yl, w_xu, w_yu)
    rs_react = filtering(rects, tiles, sec_rects, w_query)
    # vs.getResult(config, rects, w_query, rs_react)
    return rs_react


def get_tiles():
    # Defining a grid using configurations
    tiles = {}
    n = 0
    for j in range(int(GRID_HEIGHT / TILE_SIZE)):
        for i in range(int(GRID_WIDTH / TILE_SIZE)):
            tiles[n] = [i, j]
            n += 1
    return tiles


def indexing(rects):
    sec_rects = dict();

    # Classifying the set of MBRs at each tile into A,B,C and D classes
    for i in range(0, int(GRID_WIDTH / TILE_SIZE)):
        for j in range(0, int(GRID_HEIGHT / TILE_SIZE)):
            class_a = [];
            class_b = [];
            class_c = [];
            class_d = [];
            t_xl = i * TILE_SIZE
            t_yl = j * TILE_SIZE
            t_xu = t_xl + TILE_SIZE
            t_yu = t_yl + TILE_SIZE
            t_num = (j * 10) + i

            # 타일에 속해있다 : 2. 시작 보더만 포함
            for rec in rects:
                r = rects[rec]
                if (t_xl <= r.xL < t_xu) and (t_yl <= r.yL < t_yu):
                    class_a.append(rec)
                elif (t_xl <= r.xL < t_xu) and (r.yL < t_yl) and (t_yl <= r.yU):
                    class_b.append(rec)
                elif (r.xL < t_xl) and (t_xl <= r.xU) and (t_yl <= r.yL < t_yu):
                    class_c.append(rec)
                elif (r.xL < t_xl) and (t_xl <= r.xU) \
                        and (r.yL < t_yl) and (t_yl <= r.yU):
                    class_d.append(rec)

            sec_rect = dto.RecsClass(t_num, class_a, class_b, class_c, class_d)
            sec_rects[t_num] = sec_rect
    return sec_rects


def filtering(rects, tiles, sec_rects, w_query):
    rs_rects = [];
    w_xl = w_query.xL
    w_yl = w_query.yL
    w_xu = w_query.xU
    w_yu = w_query.yU

    related_tiles = []

    # upper border 보다 작을 경우만 적용?
    for t_num in tiles:
        if math.floor(w_query.xL / TILE_SIZE) <= tiles[t_num][0] <= math.floor(w_xu / TILE_SIZE) and \
                math.floor(w_yl / TILE_SIZE) <= tiles[t_num][1] <= math.floor(w_yu / TILE_SIZE):
            related_tiles.append(t_num)

    partitions = dict()
    related_rects = dict()

    try:
        for t_num in related_tiles:
            t_xl = tiles[t_num][0] * TILE_SIZE
            t_yl = tiles[t_num][1] * TILE_SIZE

            # lemma 1: tile T와 교차하는 범위쿼리의 W의 x좌표가 T의 x좌표보다 먼저 시작하면,
            #           secondary-partition Tc와 Td는 고려하지 않는다 => Ta, Tb만 고려 1100
            if w_xl < t_xl and w_yl >= t_yl:
                partitions[t_num] = [1, 1, 0, 0]
                related_rects[t_num] = sec_rects[t_num].classA + sec_rects[t_num].classB

            # lemma 2: tile T와 교차하는 범위쿼리의 W의 y좌표가 T의 y좌표보다 먼저 시작하면,
            #           secondary-partition Tb와 Td는 고려하지 않는다
            elif w_yl < t_yl and w_xl >= t_xl:
                partitions[t_num] = [1, 0, 1, 0]
                related_rects[t_num] = sec_rects[t_num].classA + sec_rects[t_num].classC

            # lemma 1+2: tile T와 교차하는 범위쿼리의 W의 x,y좌표가 T의 x,y좌표보다 먼저 시작하면,
            #           secondary-partition Tb,Tc와 Td는 고려하지 않는다
            elif (w_xl < t_xl) and (w_yl < t_yl):
                partitions[t_num] = [1, 0, 0, 0]
                related_rects[t_num] = sec_rects[t_num].classA

            else:
                partitions[t_num] = [1, 1, 1, 1]
                related_rects[t_num] = (sec_rects[t_num].classA + sec_rects[t_num].classB +
                                        sec_rects[t_num].classC + sec_rects[t_num].classD)
    except KeyError as ke:
        print(t_num)
        log.error('KeyError occurred')
    partitions = sorted(partitions.items())

    # For a window query W that intersects more than one tile per dimension
    related_tiles = sorted(related_tiles)
    t_lower = tiles[related_tiles[0]]
    t_upper = tiles[related_tiles[-1]]

    if (t_upper[0] - t_lower[0] < 1) or (t_upper[1] - t_lower[1] < 1):
        for t_num in related_tiles:
            for i in related_rects[t_num]:
                if (rects[i].xL <= w_xu and rects[i].xU >= w_xl and
                        rects[i].yL <= w_yu and rects[i].yU >= w_yl):
                    rs_rects.append(rects[i].id)
        return rs_rects

    #  Step 4~5 => 각 Secondary -partition에 대해서 해당 파티션에 속하는 모든 r 찾기

    # W의 d좌표와 Tile의 d좌표 비교
    # window query (w_xl, w_yl, w_xu, w_yu)
    # xL, yL, xU, yU

    # decompositions = dict()
    # lemma 3 or 4 를 만족 하는지 확인 후 decompositions dict에 필요한 decomposition table 저장
    #  lemma 3: 만약 W의 d좌표가 T보다 먼저 시작해서 T의 안에서 끝난다면, T에 속하는 r에 대하여,
    #           rdl <= wdu이면, r의 d좌표는 W와 교차한다
    #  lemma 4: 만약 W의 d좌표가 T 안에 시작해서 T의 밖에서 끝난다면, T에 속하는 r에 대하여,
    #           rdu >= wdl이면, r의 d좌표는 W와 교차한다
    # print(partitions)
    try:
        for tile in partitions:
            t_num = tile[0]
            t_xl = tiles[t_num][0] * TILE_SIZE
            t_xu = t_xl + TILE_SIZE
            t_yl = tiles[t_num][1] * TILE_SIZE
            t_yu = t_yl + TILE_SIZE

            # lemma3 in dimension x
            # 만약 W의 x좌표가 T보다 먼저 시작해서 T의 안에서 끝난다면, T에 속하는 r에 대하여,
            #  rxl <= wxu이면, r의 x좌표는 W와 교차한다
            # 타일에 속해있다 : 2. 시작 보더만 포함
            if (t_xl <= w_xu < t_xu) and w_xl < t_xl:
                # lemma3 in dimension y
                if (t_yl <= w_yu < t_yu) and w_yl < t_yl:
                    # print('tile', t_num, ' - lemma3 in dimension x && y')
                    for key in related_rects.get(t_num):
                        if rects[key].xL <= w_xu and rects[key].yL <= w_yu:
                            rs_rects.append(key)
                # lemma4 in dimension y
                elif (t_yl <= w_yl < t_yu) and w_yu >= t_yu:
                    # print('tile', t_num, ' - lemma3 in dimension x && lemma4 in dimension y')
                    for key in related_rects.get(t_num):
                        if rects[key].xL <= w_xu and rects[key].yU >= w_yl:
                            rs_rects.append(key)
                else:
                    # print('tile', t_num, ' - lemma3 in dimension x')
                    for key in related_rects.get(t_num):
                        if rects[key].xL <= w_xu:
                            # and rects[key].yL <= w_yu and rects[key].yU >= w_yl:
                            rs_rects.append(key)

            # lemma4 in dimension x
            # lemma 4: 만약 W의 x좌표가 T 안에 시작해서 T의 밖에서 끝난다면(uppper boder 포함), T에 속하는 r에 대하여,
            #  rxu >= wxl이면, r의 x좌표는 W와 교차한다
            # 타일에 속해있다 : 2. 시작 보더만 포함
            elif (t_xl <= w_xl < t_xu) and w_xu >= t_xu:
                # lemma3 in dimension y
                if (t_yl <= w_yu < t_yu) and w_yl < t_yl:
                    # print('tile', t_num, ' - lemma4 in dimension x && lemma3 in dimension y')
                    for key in related_rects.get(t_num):
                        if rects[key].xU >= w_xl and rects[key].yL <= w_yu:
                            rs_rects.append(key)
                # lemma4 in dimension y
                elif (t_yl <= w_yl < t_yu) and w_yu >= t_yu:
                    # print('tile', t_num, ' - lemma4 in dimension x && lemma4 in dimension y')
                    for key in related_rects.get(t_num):
                        if rects[key].xU >= w_xl and rects[key].yU >= w_yl:
                            rs_rects.append(key)
                else:
                    # print('tile', t_num, ' - lemma4 in dimension x')
                    for key in related_rects.get(t_num):
                        if rects[key].xU >= w_xl:
                            # and rects[key].yL <= w_yu and rects[key].yU >= w_yl:
                            rs_rects.append(key)
            else:
                # lemma3 in dimension y
                if (t_yl <= w_yu < t_yu) and w_yl < t_yl:
                    # print('tile', t_num, ' - lemma3 in dimension y')
                    for key in related_rects.get(t_num):
                        if rects[key].yL <= w_yu:
                            # if rects[key].xL <= w_xu and rects[key].xU >= w_xl and rects[key].yL <= w_yu:
                            rs_rects.append(key)
                # lemma4 in dimension y
                elif (t_yl <= w_yl < t_yu) and w_yu >= t_yu:
                    # print('tile', t_num, ' - lemma4 in dimension y')
                    for key in related_rects.get(t_num):
                        if rects[key].yU >= w_yl:
                            # if rects[key].xL <= w_xu and rects[key].xU >= w_xl and rects[key].yU >= w_yl:
                            rs_rects.append(key)
                else:
                    # print('tile', t_num, ' - No comparison needed')
                    # tile 내에 윈도우 쿼리가 존재하는 경우 related_rects 내의 모든 rects를 결과로 도출함
                    for key in related_rects.get(t_num):
                        rs_rects.append(key)
                        # if rects[key].xL <= w_xu and rects[key].xU >= w_xl and rects[key].yL <= w_yu and rects[
                        #     key].yU >= w_yl:
                        #     rs_rects.append(key)
        # print(rs_rects)
        rs_rects = sorted(rs_rects)
        return rs_rects

    except Exception as e:
        log.error(e)


if __name__ == '__main__':
    main()
