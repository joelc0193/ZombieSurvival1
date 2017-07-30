import sys
from math import *

class Vertex:
    def __init__(self, node):
        self.id = node
        self.adjacent = {}
        # Set distance to infinity for all nodes
        self.distance = sys.maxint
        # Mark all nodes unvisited        
        self.visited = False  
        # Predecessor
        self.previous = None

    def add_neighbor(self, neighbor, weight=0):
        self.adjacent[neighbor] = weight

    def remove_neighbor(self, neighbor, weight=0):
        del self.adjacent[neighbor]

    def get_connections(self):
        return self.adjacent.keys()  

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

    def set_distance(self, dist):
        self.distance = dist

    def get_distance(self):
        return self.distance

    def set_previous(self, prev):
        self.previous = prev

    def set_visited(self):
        self.visited = True

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self.adjacent])

class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0

    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_vertex(self, node):
        self.num_vertices = self.num_vertices + 1
        new_vertex = Vertex(node)
        self.vert_dict[node] = new_vertex
        return new_vertex

    def remove_vertex(self, node):
        self.get_vertex(node)
        self.num_vertices = self.num_vertices - 1
        vertex=self.get_vertex(node)
        adjacents=vertex.adjacent.keys()
        for neighbor in adjacents:
            self.remove_edge(vertex.id, neighbor.id)
        del self.vert_dict[node]

    def get_vertex(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, cost = 0):
        if frm not in self.vert_dict:
            self.add_vertex(frm)
        if to not in self.vert_dict:
            self.add_vertex(to)

        self.vert_dict[frm].add_neighbor(self.vert_dict[to], cost)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], cost)

    def remove_edge(self, e, e2):
        self.vert_dict[e].remove_neighbor(self.vert_dict[e2])
        self.vert_dict[e2].remove_neighbor(self.vert_dict[e])

    def get_vertices(self):
        return self.vert_dict.keys()

    def set_previous(self, current):
        self.previous = current

    def get_previous(self, current):
        return self.previous

def shortest(v, path):
    ''' make shortest path from v.previous'''
    if v.previous:
        path.append(v.previous.get_id())
        shortest(v.previous, path)
    return

import heapq

def dijkstra(aGraph, start, target):
    # Set the distance for the start node to zero 
    start.set_distance(0)

    # Put tuple pair into the priority queue
    unvisited_queue = [(v.get_distance(),v) for v in aGraph]
    heapq.heapify(unvisited_queue)

    while len(unvisited_queue):
        # Pops a vertex with the smallest distance 
        uv = heapq.heappop(unvisited_queue)
        current = uv[1]
        current.set_visited()

        #for next in v.adjacent:
        for next in current.adjacent:
            # if visited, skip
            if next.visited:
                continue
            new_dist = current.get_distance() + current.get_weight(next)
            
            if new_dist < next.get_distance():
                next.set_distance(new_dist)
                next.set_previous(current)

        # Rebuild heap
        # 1. Pop every item
        while len(unvisited_queue):
            heapq.heappop(unvisited_queue)
        # 2. Put all vertices not visited into the queue
        unvisited_queue = [(v.get_distance(),v) for v in aGraph if not v.visited]
        heapq.heapify(unvisited_queue)
    
if __name__ == '__main__':
    pass
  

def distance(node1, node2):
    return sqrt((node1[0] - node2[0])**2 + (node1[1] - node2[1])**2)

# g = Graph()

# g.add_vertex((626,350))
# g.add_vertex((231, 325))
# g.add_vertex((632, 326))
# g.add_vertex((626.0, 350.0))
# g.add_vertex((249.60418830797698, 349.44660089273856))

# g.add_edge((626,350), (249.60418830797698, 349.44660089273856), distance((626,350),(249.60418830797698, 349.44660089273856)))  
# g.add_edge((231, 325), (249.60418830797698, 349.44660089273856), distance((231, 325),(249.60418830797698, 349.44660089273856))) 
# g.add_edge((231, 325), (632, 326), distance((231, 325), (632, 326)))
# g.add_edge((632, 326), (231, 325), distance((632, 326), (231, 325)))
# g.add_edge((632, 326), (626.0, 350.0), distance((632, 326), (626.0, 350.0)))

def display_path_info(self):
    print 'Graph data:'
    for v in self:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            print '( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w))

    # dijkstra(g, g.get_vertex((249.60418830797698, 349.44660089273856)), g.get_vertex((626,350))) 

    # target = g.get_vertex((626,350))
    # path = [target.get_id()]
    # shortest(target, path)
    # print 'The shortest path : %s' %(path[::-1])