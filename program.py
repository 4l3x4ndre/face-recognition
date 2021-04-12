import database as db
import graph
import visual as gui


def create_graph(vertices_db, edges_db):
    g = graph.Graph_dic()
    edges = edges_db.select_item()
    for e in edges:
        # e is an item of the databse : person1, person2
        # To create a link between them we simply get their name
        g.add_edge(e[0], e[1])

    return g




def breadth_first_search(g, root):
    queue = [root]
    checked = []

    while len(queue) > 0:
        vertice = queue.pop(0)
        for n in g.neighbors(vertice):
            if n not in checked:
                queue.append(n)
        checked.append(vertice)

    return checked


def main():
    vert_db = db.Database('trump_vertices')
    edges_db = db.Database('trump_edges')

    g = create_graph(vert_db, edges_db)
    #path = breadth_first_search(g, 'Donald J. Trump')
    gui.draw(g)


main()
