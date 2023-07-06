from collections import deque
from rtree import index
import numpy as np

import file_stream as fs


class MBR:
    def __init__(self, idx, xl, yl, xu, yu):
        self.id = idx
        self.xl = xl
        self.xu = xu
        self.yl = yl
        self.yu = yu


class Label_partitioning:
    def __init__(self):
        pass

    def do(self, mbrs):
        # get partitions: intersecting test
        partitions = self.get_partitions(mbrs)
        return partitions

    def get_partitions(self, L_mbrs):
        rtree = index.Index()
        for i, mbr in enumerate(L_mbrs):
            rtree.add(mbr.idx, (mbr.xl, mbr.yl, mbr.xu, mbr.yu))
        rects = deque()
        # intersecting test
        for mbr in L_mbrs:
            tmps = []
            hits = rtree.intersection((mbr.xl, mbr.yl, mbr.xu, mbr.yu), objects=True)
            for n in hits:
                tmps.append(n.id)
            rects.append((mbr.idx, tmps))

        labels = []
        visited = deque()

        for rect in rects:
            if rect not in visited:
                grh = self.dfs_deque(rects, rect[0])
                labels.append(grh)
                visited.extend(grh)

        return labels

    def dfs_deque(self, graph, start_node):
        visited = []
        need_visited = deque()
        need_visited.append(start_node)

        while need_visited:
            node = need_visited.pop()
            if node not in visited:
                visited.append(node)
                need_visited.extend(graph[node][1])
        return visited

    def search_label(self, l_partition, label):
        found = False
        for l in l_partition:
            found = np.array_equal(l.label, label)
        return found


if __name__ == '__main__':
    mbrs = fs.get_rects()
    l = Label_partitioning()
    partitions = l.do(mbrs)
