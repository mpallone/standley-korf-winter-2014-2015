#!/usr/bin/env python3 
"""Standley-algorithm specific code. Poorly implements Operator Decomposition.

This code isn't meant to be well designed or efficient. It's only purpose is to
help me understand Standley's OD+ID based algorithms. 
""" 

from infrastructure import * 
import sys 
import math 

class GridWorldNode():
    """A node that contains a gridworld, with helper routines to facilitate
    search.
    """

    def __init__(self, baseGrid=None, agentList=None):
        """Create a GridWorldNode. 

        @param baseGrid: a grid such as one generated by generateCpfGrid(). 
        @param agentList: list of GridWorldAgent objects 
        """

        self.parent = None 
        self.stepsSoFar = 0

        # Make things easy for the copy constructor: 
        if baseGrid is None and agentList is None: 
            self.length = None 
            self.width = None 
            self.indexOfNextUnassignedAgent = None 
            self.agentList = None 
            self.grid = None 
            return 

        self.length, self.width = getLengthAndWidth(baseGrid)
        self.indexOfNextUnassignedAgent = 0 

        # Create a deep copy of the agent list. 
        self.agentList = [] 
        for agent in agentList: 
            self.agentList.append(agent.deepcopy())

        # Construct the grid. 
        self.grid = [] 
        for rowIndex in range(self.length): 
            self.grid.append([])
            for colIndex in range(self.width): 
                self.grid[rowIndex].append(Cell())

        for rowIndex in range(self.length): 
            for colIndex in range(self.width): 
                baseGridItem = baseGrid[rowIndex][colIndex]
                if baseGridItem == GridWorldEnum.obstacle: 
                    self.grid[rowIndex][colIndex].obstacle = True 

        for agent in self.agentList: 
            agentRow = agent.assignment.y 
            agentCol = agent.assignment.x 
            self.grid[agentRow][agentCol].agent = agent 

    def goalTest(self):
        """Return True if all agents have reached their goals.""" 
        # Walk through all cells, verifying that, if an agent is contained, 
        # then that agent's goal matches that cell's coordinates. 
        for rowIndex in range(self.length): 
            for colIndex in range(self.width): 
                cell = self.grid[rowIndex][colIndex]
                if cell.agent: 
                    agent = cell.agent
                    if agent.goal.x != colIndex or agent.goal.y != rowIndex:
                        return False 
        return True 

    def f(self):
        """Does this really need a docstring?"""
        return self.g() + self.h() 

    def g(self):
        """Does this really need a docstring?

        I'm actually not certain how best to implement this. Finding the true 
        minimal cost path from source to current position for all agents, while
        accounting for potential collisions, sounds like another AI problem 
        in and of itself. 

        Maybe I'm missing something obvious. 
        """ 
        return self.stepsSoFar # Not minimal! Not A*! 

    def h(self): 
        """Does this really need a docstring?"""
        # Euclidian distance => admissible heuristic 
        distance = 0 
        for rowIndex in range(self.length): 
            for colIndex in range(self.width): 
                cell = self.grid[rowIndex][colIndex]
                if cell.agent: 
                    agent = cell.agent
                    curr_x = colIndex
                    curr_y = rowIndex
                    if agent.assignment.x and agent.assignment.y: 
                        curr_x = agent.assignment.x 
                        curr_y = agent.assignment.y
                    goal_x = cell.agent.goal.x 
                    goal_y = cell.agent.goal.y 
                    distance += math.hypot(goal_x - curr_x, goal_y - curr_y)
        return distance 


    def _isLegalAssignment(self, agent, curr_x, curr_y, x, y):  
        """Return True if (x, y) is a legal assignment for agent. 

        Be careful not to confuse 'location' with 'assignment'. Location is 
        where the agent is, and assignment is where the agent will move to 
        in the next timestep. 

        @param agent: GridWorldAgent object we're thinking about moving to x,y
        @param curr_x: x coordinate of the agent 
        @param curr_y: y coordinate of the agent 
        @param x: x coordinate for the next timestep for the agent 
        @param y: y coordinate for the next timestep for the agent 

        @return True if (x,y) is a legal assignment for the agent, false 
            otherwise. 
        """

        # Easy stuff: don't go off the board or into an obstacle. 
        if x < 0 or x >= self.width: 
            return False 
        if y < 0 or y >= self.length: 
            return False 

        if self.grid[y][x].obstacle: 
            return False 

        # Make sure another agent isn't already assigned to these coordinates. 
        count = 0 
        for currAgent in self.agentList: 
            if currAgent.assignment.x == x and currAgent.assignment.y == y: 
                return False 

        # Make sure that we're not crossing over another agent's path. 
        if self.grid[y][x].agent is not None: 
            otherAgent = self.grid[y][x].agent
            if otherAgent.assignment.x == curr_x and                          \
                                             otherAgent.assignment.y == curr_y:
                return False 

        # I actually just noticed that this method isn't complete; it doesn't 
        # detect the case where agents cross paths, but don't swap places.

        return True 

    def expand(self):
        """Return a list of successor nodes. 

        If all nodes have been assigned a location, then they will all be 
        moved to that location and this method will return a list containing 
        a single node, in which all agents occupy their assignments.

        Otherwise, each successor node will contain an assignment for the next 
        agent in line, assuming that the next agent in line has a legal move 
        (note that it may be illegal to wait if another agent has been assigned
        the current agent's coordinates). If there are no legal moves, then 
        an empty list will be returned. 
        """
        # Return a single node in which all agents have moved to their 
        # assigned location, and mark their assignments as None.         
        if self.indexOfNextUnassignedAgent >= len(self.agentList): 

            newNode = self.deepcopy() 
            newNode.indexOfNextUnassignedAgent = 0 

            newGrid = []
            for rowIndex in range(self.length): 
                newGrid.append([])
                for colIndex in range(self.width): 
                    newGrid[rowIndex].append(Cell())
    
            for rowIndex in range(self.length): 
                for colIndex in range(self.width): 
                    cell = self.grid[rowIndex][colIndex]
                    if cell.obstacle: 
                        newGrid[rowIndex][colIndex].obstacle = True 

            newNode.grid = newGrid
            for agent in newNode.agentList: 
                row = agent.assignment.y
                col = agent.assignment.x 
                newNode.grid[row][col].agent = agent 
                agent.assignment = Coordinate(None, None)

            newNode.parent = self 
            newNode.stepsSoFar += 1

            return [newNode]

        # Otherwise, find an assignment for the next agent. 
        agent = self.agentList[self.indexOfNextUnassignedAgent]
        agent_row = None 
        agent_col = None 
        # Find this agent's coordinates: 
        # (this could be avoided in a more efficient implementation)
        for row in range(self.length):
            for col in range(self.width): 
                cell = self.grid[row][col]
                if cell.agent: 
                    if agent == cell.agent: 
                        agent_row = row 
                        agent_col = col 
                        break 

        children = []
        for row in range(agent_row-1, agent_row+1+1): 
            for col in range(agent_col-1, agent_col+1+1): 
                if self._isLegalAssignment(agent, agent_col, agent_row, col, 
                                           row):

                    newNode = self.deepcopy() 
                    newNode.grid[agent_row][agent_col].agent.assignment =     \
                                                           Coordinate(col, row)
                    newNode.indexOfNextUnassignedAgent += 1
                    newNode.parent = self 
                    children.append(newNode)

        return children 

    def deepcopy(self): 
        """Return a deep copy of this object."""
        newNode = GridWorldNode() 

        # Construct the new agent list. 
        newAgentList = []
        for agent in self.agentList: 
            newAgentList.append(agent.deepcopy())

        # Construct the new grid. 
        newGrid = []
        for rowIndex in range(self.length): 
            newGrid.append([])
            for colIndex in range(self.width): 
                newGrid[rowIndex].append(Cell())

        for rowIndex in range(self.length): 
            for colIndex in range(self.width): 
                cell = self.grid[rowIndex][colIndex]
                if cell.obstacle: 
                    newGrid[rowIndex][colIndex].obstacle = True 

        for rowIndex in range(self.length): 
            for colIndex in range(self.width): 
                cell = self.grid[rowIndex][colIndex]
                if cell.agent: 
                    for agent in newAgentList: 
                        if cell.agent.id == agent.id: 
                            newGrid[rowIndex][colIndex].agent = agent 
                            break 

        newNode.agentList = newAgentList
        newNode.grid = newGrid
        newNode.length = self.length 
        newNode.width = self.width 
        newNode.indexOfNextUnassignedAgent = self.indexOfNextUnassignedAgent
        newNode.stepsSoFar = self.stepsSoFar

        return newNode 

    def __str__(self): 
        """Return a string represnting this object.""" 
        myString = "\n\n\n"
        for row in self.grid: 
            for cell in row:         
                myString += str(cell) + " "
            myString += "\n"

        for agent in self.agentList: 
            myString += "\n" + str(agent)

        myString += "\nindexOfNextUnassignedAgent = "
        myString += str(self.indexOfNextUnassignedAgent)
        return myString

    def __hash__(self):
        """Does this really need a docstring?"""
        # make a string out of this object to hash over 
        myString = ""
        for rowIndex in range(self.length): 
            for colIndex in range(self.width):         
                cell = self.grid[rowIndex][colIndex]
                if cell.obstacle: 
                    myString += "x"
                elif cell.agent: 
                    myString += str(cell.agent.id)
                else:
                    myString += "_"

        for agent in self.agentList: 
            myString += str(agent)

        myHash = 0 
        for c in myString: 
            myHash = 101 * myHash + ord(c)
        return myHash 


class Cell: 
    """A cell in a gridworld, which may be empty, or may contain an agent or 
    an obstacle (but certainly not both)."""

    def __init__(self, obstacle=False, agent=None):
        """Create a grid world Cell.

        @param obstacle: a boolean indicating whether or not this object 
            contains an obstacle. 
        @param agent: a GridWorldAgent reference, or None if this cell does not
            contain an agent. 
        """ 
        self._obstacle = obstacle
        self._agent = agent 
        self.sanityCheck()

    def __str__(self):
        """Return a string representation of this cell.""" 
        if self.obstacle: 
            return("x")
        elif self.agent:
            return(str(self.agent.id))
        return "_"

    def __hash__(self):
        """Does this really need a docstring?""" 
        myString = ""
        if obstacle:
            myString += "1"
        else:
            myString += "0"

        if agent: 
            myString += str(agent.id)
        else: 
            myString += "0"

        myHash = 0 
        for c in myString: 
            myHash = 101 * myHash + ord(c)
        return myHash 

    @property
    def agent(self):
        """Return the agent in this cell. 

        @return None if this cell does not contain an agent, otherwise a 
            reference to a GridWorldAgent object. 
        """
        return self._agent
    @agent.setter
    def agent(self, value):
        """Set this cell's agent to 'value'. 

        An assert error will be raised if this cell contains an obstacle. 

        @param value: a GridWorldAgent object, or None 
        """
        self._agent = value
        self.sanityCheck() 

    @property
    def obstacle(self):
        """Return True if this cell contains an obstacle, and False otherwise.
        """
        return self._obstacle
    @obstacle.setter
    def obstacle(self, value):
        """Add or remove an obstacle to this cell. 

        An assert error will be raised if this cell contains an agent.

        @param value: True if this cell should contain an agent, False 
            otherwise. 
        """
        self._obstacle = value
        self.sanityCheck() 

    def sanityCheck(self):  
        """Assert that this cell does not contain an obstacle AND an agent.
        """
        if self.obstacle: 
            if self.agent is not None: 
                print("agent assigned to an obstacle cell!")
                print(self.agent)
                sys.exit() 


def insertInSortedOrder(nodeList, node): 
    """Insert node into nodeList such that nodeList remains in sorted order.

    Nodes with lower f() values appear closer to index 0. 

    @param nodeList: a list of GridWorldNode objects 
    @param node: a GridWorldNode object 
    """
    for i in range(len(nodeList)): 
        currNode = nodeList[i] 
        if currNode.f() > node.f(): 
            nodeList.insert(i, node)
            return 
    nodeList.append(node)

def main():
    print("\n\n\n\n\n\n----")

    grid = None 
    while True: 
        # Keep it simple to start with 
        grid = generateConnectedCpfGrid(obstacle_probability = 0.4) 
        # So that we can use hard coded indices: 
        if grid[0][0] == GridWorldEnum.empty: 
            if grid[7][7] == GridWorldEnum.empty: 
                if grid[5][5] == GridWorldEnum.empty: 
                    if grid[3][3] == GridWorldEnum.empty: 
                        break 

    print(convertGridToString(grid))

    agent1 = GridWorldAgent(7, 7, 0, 0, 1)
    agent2 = GridWorldAgent(0, 0, 7, 7, 2)
    agent3 = GridWorldAgent(3, 3, 5, 5, 3)

    firstNode = GridWorldNode(grid, [agent1, agent2, agent3])

    # A* (ish)
    closed = [] 
    nodeList = [] 
    for node in firstNode.expand(): 
        insertInSortedOrder(nodeList, node)
    goalNode = None 

    print("Initial state:")
    print(firstNode)
    print("\n")

    count = 0 
    while nodeList: 
        node = nodeList.pop(0)

        if node.goalTest(): 
            goalNode = node 
            break 

        # I'm aware that this is a horrible and lazy way to check for duplicate
        # states, but it's left over from debugging and I don't care to fix it.
        if node.__hash__() not in closed: 
            for child in node.expand(): 
                # nodeList.insert(0, child) # DFS 
                insertInSortedOrder(nodeList, child)

        closed.append(node.__hash__())

    if goalNode: 
        print("GOAL FOUND")
    else:
        print("GOAL NOT FOUND")
        sys.exit() 

    nodes = []
    currNode = goalNode
    while currNode is not None: 
        nodes.append(currNode)
        currNode = currNode.parent 

    print("------------------------------------------------------------------")
    nodes.reverse()
    for node in nodes:
        if node.indexOfNextUnassignedAgent == 0:
            print(node)
            input("Press enter: ")

    print("total steps:", goalNode.stepsSoFar)

if __name__ == '__main__': 
    main() 



