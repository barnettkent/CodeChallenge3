#!/usr/bin/python

class Entity(object):
    def __init__(self):
        self.id = ''
        self.position = None
        self.direction = 'UP'
        self.speed = 0
        self.target = ''
        self.preferences = []
