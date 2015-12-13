#!/usr/bin/python

import argparse

from Maze import *

if __name__ == '__main__':

    argParser = argparse.ArgumentParser()
    argParser.add_argument('mazeFile', help='YAML definition of the maze')
    args = argParser.parse_args()

    theMaze = Maze(args.mazeFile)
    theMaze.Run()
