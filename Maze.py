#!/usr/bin/python

import yaml

from Entity import *
from MazeTiles import *

class Maze(object):

    def __init__(self, definitionFile):
        self.mazeData = self._readMazeFile(definitionFile)

        self.mazeTiles = MazeTiles(self.mazeData['Maze'])
        self.entities = self._parseEntities()
        self.teleporterPositions = self._findTeleporters()

    def _readMazeFile(self, path):
        mazeDataStruct = None

        with open(path, 'r') as mazeFile:
            mazeDataStruct = yaml.load(mazeFile.read())

        return mazeDataStruct

    def _parseEntities(self):
        entities = []

        for entity in self.mazeData['Entities']:
            newEntity = Entity()
            newEntity.id = entity['id']
            newEntity.speed = entity['speed']
            newEntity.target = entity['target']
            newEntity.preferences = entity['preferences']

            if 'direction' in entity.keys():
                newEntity.direction = entity['direction']

            newEntity.position = self._findEntityPosition(newEntity.id)

            entities.append(newEntity)

        idList = [entity['id'] for entity in self.mazeData['Entities']]
        targetList = [entity['target'] for entity in self.mazeData['Entities']]

        if 'G' not in idList:
            goal = Entity()
            goal.id = 'G'
            goal.position = self.mazeTiles.FindEntityPositionFromTiles(goal.id)
            entities.append(goal)

        if 'Z' in targetList and not 'Z' in idList:
            target = Entity()
            target.id = 'Z'
            target.position = self.mazeTiles.FindEntityPositionFromTiles(target.id)
            print("Z id: {} pos: {} speed: {}".format(target.id, target.position, target.speed))
            entities.append(target)

        return entities

    def _findEntityPosition(self, id):
        position = None

        for row in range(self.mazeTiles.rows):
            for col in range(self.mazeTiles.cols):
                if self.mazeTiles.GetTileValue(row, col) == id:
                    position = self.mazeTiles.CalcStartPostionFromTile(row, col)
                    break

        return position

    def _findTeleporters(self):
        teleporterPositions = []

        for row in range(self.mazeTiles.rows):
            for col in range(self.mazeTiles.cols):
                if self.mazeTiles.GetTileValue(row, col) == 'T':
                    teleporterPositions.append(self.mazeTiles.CalcStartPostionFromTile(row, col))

        return teleporterPositions

    def Run(self):
        self.isFinished = False
        self.tick = 0

        while not self.isFinished:
            if self.tick % 3 == 0:
                self._displayTiles()
                # self._displayEntityDirections()
                # self._displayEntityPositions()
            self._runTickUpdate()

    def _runTickUpdate(self):
        if self.tick > 0:
            self._decideEntityDirections()
        self._updateEntityPositions()
        self.isFinished = self._checkIfFinished(self.entities, self.mazeTiles)
        self.mazeTiles.Update(self.entities)
        self.tick += 1

    def _decideEntityDirections(self):
        for i, entity in enumerate(self.entities):

            teleported = False
            for teleporterPosition in self.teleporterPositions:
                if entity.position[0] == teleporterPosition[0] and \
                   entity.position[1] == teleporterPosition[1]:
                   self.entities[i].position = self._getOtherTeleporterPosition(teleporterPosition)
                   teleported = True
                   break

            if not teleported:
                self.entities[i].direction = self._decideDirectionForSingleEntity(entity)

    def _decideDirectionForSingleEntity(self, entity):
        resultDirection = entity.direction

        if entity.speed != 0:
            if self.mazeTiles.IsPositionInTileCenter(entity.position):

                possibleDirections = self.mazeTiles.GetPossibleDirections(entity)
                oppositeDirection = self._getOppositeDirection(entity.direction)

                availableDirections = [dir for dir in possibleDirections if dir != oppositeDirection]
                directionScores = {key: 0 for key in availableDirections}

                directionScores = self._scoreInLineEntities(entity, directionScores)

                for dir in directionScores.keys():
                    if not self.mazeTiles.DirectionIsAwayFromTarget(dir, entity, self._findTargetFor(entity)):
                        directionScores[dir] += 9

                directionScores = self._scoreDirectionPreferences(entity, directionScores)
                directionScores = self._scoreCurrentDirection(entity, directionScores)

                if 'LEFT' in directionScores.keys() and 'RIGHT' in directionScores.keys() and \
                    directionScores['LEFT'] == directionScores['RIGHT']:
                    directionScores['RIGHT'] += 1

                # print ("Entity: {} Scores: {}".format(entity.id, directionScores))

                # Find the highest score
                direction = availableDirections[0]

                for dir, score in directionScores.iteritems():
                    if score > directionScores[direction]:
                        direction = dir

                resultDirection = direction

        return resultDirection

    def _getOtherTeleporterPosition(self, teleporterPosition):
        otherTeleporterPosition = self.teleporterPositions[0]

        if self.teleporterPositions[0][0] == teleporterPosition[0] and \
           self.teleporterPositions[0][1] == teleporterPosition[1]:
           otherTeleporterPosition = self.teleporterPositions[1]

        return otherTeleporterPosition

    def _scoreInLineEntities(self, entity, currentScores):
        areInLine, inLineDirection = self.mazeTiles.CheckIfEntitiesAreInLine(entity, self._findTargetFor(entity))

        if areInLine:
            for dir in currentScores.keys():
                if dir == inLineDirection:
                    currentScores[dir] += 21

        return currentScores

    def _scoreDirectionPreferences(self, entity, currentScores):
        if 'VERTICAL_PREFERENCE' in entity.preferences:
            vertChoice = self._chooseVerticalDirection(entity)
            if vertChoice in currentScores.keys():
                currentScores[vertChoice] += 5
        elif 'HORIZONTAL_PREFERENCE' in entity.preferences:
            horizChoice = self._chooseHorizontalDirection(entity)
            if horizChoice in currentScores.keys():
                currentScores[horizChoice] += 5
        elif 'NEAREST_DIRECTION_PREFERENCE' in entity.preferences:
            nearestChoice = self.mazeTiles.GetNearestDirectionToTarget(entity, self._findTargetFor(entity))
            if nearestChoice in currentScores.keys():
                currentScores[nearestChoice] += 5

        return currentScores

    def _scoreCurrentDirection(self, entity, currentScores):
        if entity.direction in currentScores.keys():
            allLeadAwayFromGoal = True
            for dir in currentScores.keys():
                if not self.mazeTiles.DirectionIsAwayFromTarget(dir, entity, self._findTargetFor(entity)):
                    allLeadAwayFromGoal = False
                    break

            if allLeadAwayFromGoal:
                currentScores[entity.direction] += 6

        return currentScores

    def _chooseVerticalDirection(self, entity):
        direction = None

        if self._possibleDirection('UP', entity) and not self._oppositeDirectionPreferred('UP', entity):
            direction = 'UP'
        elif self._possibleDirection('DOWN', entity):
            direction = 'DOWN'

        return direction

    def _chooseHorizontalDirection(self, entity):
        direction = None

        if self._possibleDirection('RIGHT', entity) and not self._oppositeDirectionPreferred('RIGHT', entity):
            direction = 'RIGHT'
        elif self._possibleDirection('LEFT', entity):
            direction = 'LEFT'

        return direction

    def _possibleDirection(self, direction, entity):
        possibleDirections = self.mazeTiles.GetPossibleDirections(entity)
        oppositeDirection = self._getOppositeDirection(direction)

        return direction in possibleDirections and \
               entity.direction != oppositeDirection

    def _getOppositeDirection(self, direction):
        if direction == 'UP':
            opposite = 'DOWN'
        elif direction == 'DOWN':
            opposite = 'UP'
        elif direction == 'LEFT':
            opposite = 'RIGHT'
        elif direction == 'RIGHT':
            opposite = 'LEFT'

        return opposite

    def _oppositeDirectionPreferred(self, direction, entity):
        target = self._findTargetFor(entity)

        possibleDirections = self.mazeTiles.GetPossibleDirections(entity)
        oppositeDirection = self._getOppositeDirection(direction)

        directionDist = self.mazeTiles.GetDistanceToTargetForDirection(direction, entity, target)
        oppositeDist = self.mazeTiles.GetDistanceToTargetForDirection(oppositeDirection, entity, target)

        oppositeIsNearer = False
        if directionDist == None and oppositeDist != None:
            oppositeIsNearer = True

        return oppositeDirection in possibleDirections and \
               oppositeIsNearer and \
               entity.direction != oppositeDirection

    def _findTargetFor(self, entity):
        target = None
        for e in self.entities:
            if e.id == entity.target:
                target = e
                break

        return target

    def _updateEntityPositions(self):
        for i, entity in enumerate(self.entities):

            speedMultiplier = 1
            target = self._findTargetFor(entity)

            if 'LOS_SPEED_X_3' in entity.preferences and \
               self.mazeTiles.HasLineOfSightToTarget(entity, target):
               speedMultiplier = 3

            newPosition = [entity.position[0], entity.position[1]]

            if entity.direction == 'UP':
                newPosition[1] = entity.position[1] - (entity.speed * speedMultiplier)
            elif entity.direction == 'DOWN':
                newPosition[1] = entity.position[1] + (entity.speed * speedMultiplier)
            elif entity.direction == 'LEFT':
                newPosition[0] = entity.position[0] - (entity.speed * speedMultiplier)
            elif entity.direction == 'RIGHT':
                newPosition[0] = entity.position[0] + (entity.speed * speedMultiplier)

            newPosition = self.mazeTiles.BoundsCheckPosition(newPosition)
            self.entities[i].position = newPosition

    def _checkIfFinished(self, entities, tiles):
        finished = False

        for entity in entities:
            target = self._findTargetFor(entity)

            if target != None:
                row, col = self.mazeTiles.ConvertPositionToTile(entity.position)
                targetRow, targetCol = self.mazeTiles.ConvertPositionToTile(target.position)

                if row == targetRow and col == targetCol:
                    finished = True

                    if entity.id == 'P':
                        print("PLAYER FOUND THE CHEESE!")
                    else:
                        print("THE PLAYER DID NOT FIND THE CHEESE!")

        return finished

    def _displayTiles(self):
        print("")
        self.mazeTiles.DisplayTiles(self.teleporterPositions)

    def _displayEntityDirections(self):
        for entity in self.entities:
            print("Entity: {} Direction: {}".format(entity.id, entity.direction))

    def _displayEntityPositions(self):
        for i, entity in enumerate(self.entities):
            print("Enity: {} Position: {} {}".format(entity.id, self.entities[i].position[0], self.entities[i].position[1]))

    def _displayEntities(self):
        print("Maze Entities -----")
        for entity in self.entities:
            print("ID: {}\n- pos: {}\n- direction: {}\n- speed: {}\n- target: {}\n- prefs: {}\n\n".format(\
                  entity.id, \
                  entity.position, \
                  entity.direction, \
                  entity.speed, \
                  entity.target, \
                  entity.preferences
                  )
            )
